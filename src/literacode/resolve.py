"""
literacode resolve - local conflict server.

Serves the built React app from ``ui/dist`` and a small JSON API.  Local only:
binds to 127.0.0.1, no auth, no deployment.

API (this module, task 3-1):
    GET|POST /api/conflicts   conflicted chunks with base/ours/theirs context

Base and theirs come from git's index stages (``:1:``, ``:3:``) when the file
is mid-merge; the working-tree copy supplies ours.  Outside a merge, only the
working copy is available and base/theirs are reported as empty.
"""
from __future__ import annotations

import http.server
import json
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from .model import Chunk, Document, Prose
from .parser import parse_string

CONFLICT_ATTR = "lit:conflict"

_PLACEHOLDER = (
    "<!doctype html><title>lit resolve</title>"
    "<h1>lit resolve</h1><p>The UI is not built. Run <code>npm run build</code>"
    " in <code>ui/</code>. The API is available at <code>/api/conflicts</code>.</p>"
)


class ResolveError(Exception):
    pass


def is_conflicted(chunk: Chunk) -> bool:
    return CONFLICT_ATTR in chunk._fence_attrs.split()


def _split_markers(body: str) -> tuple[str, str]:
    """(ours, theirs) from a body written by the merge driver."""
    ours: list[str] = []
    theirs: list[str] = []
    side = None
    for line in body.splitlines(keepends=True):
        if line.startswith("<<<<<<< "):
            side = ours
        elif line.startswith("=======") and side is ours:
            side = theirs
        elif line.startswith(">>>>>>> ") and side is theirs:
            side = None
        elif side is not None:
            side.append(line)
    return "".join(ours), "".join(theirs)


def _git_stage(stage: int, path: Path) -> str | None:
    """Contents of the file at an index stage, or None if there is none."""
    try:
        rel = subprocess.run(
            ["git", "ls-files", "--full-name", "--", path.name],
            cwd=path.parent, capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        if not rel:
            return None
        out = subprocess.run(
            ["git", "show", f":{stage}:{rel[0]}"],
            cwd=path.parent, capture_output=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout.decode("utf-8")


def _context(doc: Document | None, chunk_id: str) -> dict[str, str] | None:
    """Body plus nearest prose before/after for one chunk, or None if absent."""
    if doc is None:
        return None
    nodes = doc.nodes
    for i, node in enumerate(nodes):
        if isinstance(node, Chunk) and node.id == chunk_id:
            before = nodes[i - 1].text if i > 0 and isinstance(nodes[i - 1], Prose) else ""
            after = (
                nodes[i + 1].text
                if i + 1 < len(nodes) and isinstance(nodes[i + 1], Prose)
                else ""
            )
            return {"body": node.body, "prose_before": before, "prose_after": after}
    return None


_EMPTY = {"body": "", "prose_before": "", "prose_after": ""}


def load_conflicts(doc_path: Path) -> list[dict]:
    """The conflicts in doc_path, as the payload ``/api/conflicts`` returns."""
    work = parse_string(doc_path.read_text(encoding="utf-8"))
    base_text = _git_stage(1, doc_path)
    ours_text = _git_stage(2, doc_path)
    theirs_text = _git_stage(3, doc_path)
    ours_doc = parse_string(ours_text) if ours_text is not None else work
    base = parse_string(base_text) if base_text is not None else None
    theirs = parse_string(theirs_text) if theirs_text is not None else None

    result = []
    for chunk in work.chunks():
        if not is_conflicted(chunk):
            continue
        ours_body, theirs_body = _split_markers(chunk.body)
        # Prose per side comes from that side's index stage. The working copy
        # has the merged prose, so it is only the fallback outside a merge.
        ours = _context(ours_doc, chunk.id) or dict(_EMPTY)
        ours["body"] = ours_body
        th = _context(theirs, chunk.id) or dict(_EMPTY)
        if theirs is None:
            th["body"] = theirs_body
        result.append({
            "chunk_id": chunk.id,
            "lang": chunk.lang,
            "base": _context(base, chunk.id) or dict(_EMPTY),
            "ours": ours,
            "theirs": th,
        })
    return result


def _make_handler(doc_path: Path, static_root: Path):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # keep the terminal quiet
            pass

        def _send(self, status: int, body: bytes, ctype: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, payload) -> None:
            self._send(status, json.dumps(payload).encode(), "application/json")

        def _api(self) -> bool:
            if self.path.split("?")[0] == "/api/conflicts":
                try:
                    self._json(200, load_conflicts(doc_path))
                except (OSError, ValueError) as e:
                    self._json(500, {"error": str(e)})
                return True
            return False

        def do_POST(self):
            if not self._api():
                self._json(404, {"error": "not found"})

        def do_GET(self):
            if self._api():
                return
            rel = self.path.split("?")[0].lstrip("/") or "index.html"
            target = (static_root / rel).resolve()
            if static_root.resolve() not in target.parents or not target.is_file():
                target = static_root / "index.html"
            if not target.is_file():
                self._send(200, _PLACEHOLDER.encode(), "text/html; charset=utf-8")
                return
            ctype = {
                ".html": "text/html; charset=utf-8", ".js": "text/javascript",
                ".css": "text/css", ".svg": "image/svg+xml",
            }.get(target.suffix, "application/octet-stream")
            self._send(200, target.read_bytes(), ctype)

    return Handler


def make_server(doc_path: Path, port: int, static_root: Path | None = None):
    if static_root is None:
        static_root = Path(__file__).resolve().parents[2] / "ui" / "dist"
    return http.server.ThreadingHTTPServer(
        ("127.0.0.1", port), _make_handler(doc_path, static_root)
    )


def find_conflicted_doc() -> Path | None:
    """The single unmerged .md file in the repo, if exactly one."""
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            capture_output=True, text=True, check=True,
        ).stdout.split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    md = [p for p in out if p.endswith(".md")]
    return Path(md[0]) if len(md) == 1 else None


def serve(file: str | None = None, port: int = 7777) -> int:
    doc_path = Path(file) if file else find_conflicted_doc()
    if doc_path is None:
        print("lit resolve: give a file, or run inside a merge with exactly one "
              "conflicted .md file", file=sys.stderr)
        return 1
    if not doc_path.is_file():
        print(f"lit resolve: file not found: {doc_path}", file=sys.stderr)
        return 1
    doc_path = doc_path.resolve()

    try:
        server = make_server(doc_path, port)
    except OSError as e:
        print(f"lit resolve: cannot bind port {port}: {e}", file=sys.stderr)
        return 1

    url = f"http://127.0.0.1:{port}/"
    print(f"lit resolve: serving {doc_path.name} at {url}  (Ctrl+C to stop)")
    threading.Timer(0.3, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
