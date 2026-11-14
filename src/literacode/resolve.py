"""
literacode resolve - local conflict server.

Serves the built React app from ``ui/dist`` and a small JSON API.  Local only:
binds to 127.0.0.1, no auth, no deployment.

API:
    GET|POST /api/conflicts   conflicted chunks with base/ours/theirs context
    POST /api/propose         {chunk_id} -> agent proposal (read-only; see propose.py)
    GET  /api/file            {name} of the document being resolved
    POST /api/resolve         {chunk_id, body} -> {remaining, prose_conflicts}

Base and theirs come from git's index stages (``:1:``, ``:3:``) when the file
is mid-merge; the working-tree copy supplies ours.  Outside a merge, only the
working copy is available and base/theirs are reported as empty.
"""
from __future__ import annotations

import hashlib
import http.server
import json
import os
import re
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from .model import Chunk, Document, Prose
from .parser import parse_document, parse_string
from .serialiser import serialise

CONFLICT_ATTR = "lit:conflict"

_PLACEHOLDER = (
    "<!doctype html><title>lit resolve</title>"
    "<h1>lit resolve</h1><p>The UI is not built. Run <code>npm run build</code>"
    " in <code>ui/</code>. The API is available at <code>/api/conflicts</code>.</p>"
)


class ResolveError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status

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


_MARKER_LINE = re.compile(r"^(<<<<<<< |=======$|>>>>>>> )", re.M)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_chunk(doc_path: Path, chunk_id: str, body: str, expected_hash: str) -> dict:
    """
    Write ``body`` as the resolution of one conflicted chunk.

    Refuses (ResolveError) if the file changed since ``expected_hash``, the
    chunk is not a known conflict, or the body is empty or still contains
    conflict markers. The file is replaced atomically via a temp file.
    Returns {remaining, prose_conflicts, hash}.
    """
    if file_hash(doc_path) != expected_hash:
        raise ResolveError(
            "document changed on disk since lit resolve started; "
            "restart lit resolve", 409,
        )
    if not isinstance(body, str) or not body.strip():
        raise ResolveError("resolution is empty")
    if _MARKER_LINE.search(body):
        raise ResolveError("resolution still contains conflict markers")

    doc = parse_document(doc_path)
    chunk = next(
        (c for c in doc.chunks() if c.id == chunk_id and is_conflicted(c)), None
    )
    if chunk is None:
        raise ResolveError(f"no conflicted chunk '{chunk_id}'", 404)

    chunk.body = body if body.endswith("\n") else body + "\n"
    chunk._fence_attrs = " ".join(
        a for a in chunk._fence_attrs.split(" ") if a != CONFLICT_ATTR
    )
    text = serialise(doc)

    tmp = doc_path.with_name(doc_path.name + ".lit_resolved")
    tmp.write_text(text, encoding="utf-8", newline="")
    os.replace(tmp, doc_path)

    left = parse_document(doc_path)
    return {
        "remaining": sum(is_conflicted(c) for c in left.chunks()),
        "prose_conflicts": sum(
            len(re.findall(r"^<<<<<<< ", n.text, re.M))
            for n in left.nodes if isinstance(n, Prose)
        ),
        "hash": file_hash(doc_path),
    }


def _make_handler(doc_path: Path, static_root: Path, state: dict):
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
            if self.path.split("?")[0] == "/api/file":
                self._json(200, {"name": doc_path.name})
                return True
            if self.path.split("?")[0] == "/api/conflicts":
                try:
                    self._json(200, load_conflicts(doc_path))
                except (OSError, ValueError) as e:
                    self._json(500, {"error": str(e)})
                return True
            return False

        def _propose(self) -> None:
            """POST /api/propose {chunk_id} -> agent proposal. Never writes."""
            try:
                length = int(self.headers.get("Content-Length") or 0)
                chunk_id = json.loads(self.rfile.read(length) or b"{}")["chunk_id"]
                match = [c for c in load_conflicts(doc_path) if c["chunk_id"] == chunk_id]
            except (OSError, ValueError, KeyError, TypeError) as e:
                self._json(400, {"error": f"bad request: {e}"})
                return
            if not match:
                self._json(404, {"error": f"no conflict for chunk '{chunk_id}'"})
                return
            from .propose import propose

            self._json(200, propose(match[0]))

        def _resolve(self) -> None:
            """POST /api/resolve {chunk_id, body}: the only route that writes."""
            try:
                length = int(self.headers.get("Content-Length") or 0)
                req = json.loads(self.rfile.read(length) or b"{}")
                chunk_id, body = req["chunk_id"], req["body"]
            except (ValueError, KeyError, TypeError) as e:
                self._json(400, {"error": f"bad request: {e}"})
                return
            with state["lock"]:
                try:
                    out = resolve_chunk(doc_path, chunk_id, body, state["hash"])
                except ResolveError as e:
                    self._json(e.status, {"error": str(e)})
                    return
                except OSError as e:
                    self._json(500, {"error": str(e)})
                    return
                state["hash"] = out.pop("hash")
            self._json(200, out)
            if out["remaining"] == 0:
                # Let the response flush, then stop the server.
                threading.Timer(3.0, self.server.shutdown).start()

        def do_POST(self):
            if self.path.split("?")[0] == "/api/propose":
                self._propose()
            elif self.path.split("?")[0] == "/api/resolve":
                self._resolve()
            elif not self._api():
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
    state = {"hash": file_hash(doc_path), "lock": threading.Lock()}
    return http.server.ThreadingHTTPServer(
        ("127.0.0.1", port), _make_handler(doc_path, static_root, state)
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
