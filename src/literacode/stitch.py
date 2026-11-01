"""
literacode stitch — edited .py files → chunk bodies in the document.

Reads sync markers written by tangle to identify which document and chunk
each region belongs to, then replaces the corresponding Chunk.body in the
source document and serialises it back.

Fails loudly on any ambiguity.  Never silently discards edits.
"""
from __future__ import annotations

import re
from pathlib import Path

from .parser import parse_string
from .serialiser import serialise

# Matches: # lit:chunk id=<id> src=<path>
MARKER_RE = re.compile(r"^# lit:chunk id=([\w-]+) src=(.+)$")


class StitchError(Exception):
    """Raised when stitch cannot safely complete."""


def _split_regions(text: str) -> list[tuple[str, str, str]]:
    """
    Split a tangled .py file into regions at sync marker lines.

    Returns a list of (id, src, body) triples.
    Empty leading content (before the first marker) is ignored — it would be
    a hand-edit above all chunks, which we cannot stitch.
    """
    regions: list[tuple[str, str, str]] = []
    current_id: str | None = None
    current_src: str | None = None
    body_lines: list[str] = []

    lines = text.splitlines(keepends=True)

    def flush() -> None:
        if current_id is not None:
            # Strip a single trailing blank line added as separator by tangle
            body = "".join(body_lines)
            # tangle adds "" + "\n".join() so there may be a trailing \n\n;
            # we want to keep exactly what was between the marker and the next
            # marker.  The separator blank line is not part of the chunk body.
            regions.append((current_id, current_src or "", body))
            body_lines.clear()

    for line in lines:
        m = MARKER_RE.match(line.rstrip("\n\r"))
        if m:
            flush()
            current_id = m.group(1)
            current_src = m.group(2)
            body_lines.clear()
        elif current_id is not None:
            body_lines.append(line)

    flush()
    return regions


def stitch(py_path: Path, doc_path: Path) -> None:
    """
    Read edited chunk bodies from py_path, update doc_path in place.

    Args:
        py_path:  Path to the tangled .py file that was edited.
        doc_path: Path to the source .md document.

    Raises:
        StitchError: if any sync marker references an id not in the document,
                     or references a different source document, or duplicate ids.
    """
    py_text = py_path.read_text(encoding="utf-8", newline="")
    regions = _split_regions(py_text)

    if not regions:
        # No sync markers — nothing to do
        return

    # Normalise doc_path for comparison (same normalisation as tangle)
    try:
        # Try to compare relative to py_path's parent or a known root;
        # we just check str representation matches
        pass
    except ValueError:
        pass

    doc_text = doc_path.read_text(encoding="utf-8", newline="")
    doc = parse_string(doc_text)

    seen_ids: set[str] = set()

    for chunk_id, src, new_body in regions:
        # Check src matches doc_path
        # tangle writes forward-slash paths; normalise for comparison
        src_norm = src.replace("\\", "/")
        # Accept exact match or basename match to handle cwd differences
        doc_str = str(doc_path).replace("\\", "/")
        if src_norm != doc_str and not doc_str.endswith("/" + src_norm) and not src_norm.endswith("/" + doc_str):
            # Try comparing just relative suffix
            # Allow if src is a suffix of doc_path or vice versa at path boundaries
            src_parts = src_norm.lstrip("/").split("/")
            doc_parts = doc_str.lstrip("/").split("/")
            min_len = min(len(src_parts), len(doc_parts))
            if src_parts[-min_len:] != doc_parts[-min_len:]:
                raise StitchError(
                    f"Sync marker in {py_path} has src={src!r} but "
                    f"stitching into {doc_path!r}"
                )

        if chunk_id in seen_ids:
            raise StitchError(
                f"Duplicate chunk id {chunk_id!r} found in {py_path}"
            )
        seen_ids.add(chunk_id)

        chunk = doc.get_chunk(chunk_id)
        if chunk is None:
            raise StitchError(
                f"Sync marker references id={chunk_id!r} which does not "
                f"exist in {doc_path}"
            )

        # Strip the separator blank lines tangle adds between regions.
        # tangle writes: marker\nbody\n[\n]marker\n...
        # body already ends in \n; tangle's join adds more blank lines.
        # Normalise: rstrip trailing newlines, then add exactly one back.
        body = new_body.rstrip("\n")
        if body:
            body += "\n"
        else:
            body = "\n"  # preserve empty bodies

        chunk.body = body

    # Serialise back to disk
    doc_path.write_text(serialise(doc), encoding="utf-8", newline="")
