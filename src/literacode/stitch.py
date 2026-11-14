# lit:chunk id=stitch-header src=lit/stitch.md
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


# lit:chunk id=StitchError src=lit/stitch.md
class StitchError(Exception):
    """Raised when stitch cannot safely complete."""


# lit:chunk id=_split_regions src=lit/stitch.md
def _split_regions(text: str) -> list[tuple[str, str, str]]:
    """
    Split a tangled .py file into regions at sync marker lines.

    Returns a list of (id, src, body) triples.  Content before the first
    marker is ignored — it would be a hand-edit above all chunks, which we
    cannot stitch.
    """
    regions: list[tuple[str, str, str]] = []
    current: tuple[str, str] | None = None
    body_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        m = MARKER_RE.match(line.rstrip("\n\r"))
        if m:
            if current is not None:
                regions.append((*current, "".join(body_lines)))
            current = (m.group(1), m.group(2))
            body_lines = []
        elif current is not None:
            body_lines.append(line)

    if current is not None:
        regions.append((*current, "".join(body_lines)))
    return regions


# lit:chunk id=stitch src=lit/stitch.md
def stitch(py_path: Path, doc_path: Path) -> None:
    """
    Read edited chunk bodies from py_path, update doc_path in place.

    Args:
        py_path:  Path to the tangled .py file that was edited.
        doc_path: Path to the source .md document.

    Raises:
        StitchError: if any sync marker references an id not in the document,
                     names a different source document, or repeats an id.
    """
    regions = _split_regions(py_path.read_text(encoding="utf-8", newline=""))
    if not regions:
        return  # no sync markers — nothing to do

    doc = parse_string(doc_path.read_text(encoding="utf-8", newline=""))
    seen_ids: set[str] = set()

    for chunk_id, src, new_body in regions:
        # Tangle writes src relative to its output root, so only the file
        # name is comparable independent of the working directory.
        if Path(src.replace("\\", "/")).name != doc_path.name:
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

        # Tangle separates regions with blank lines that are not part of the
        # chunk body: strip trailing newlines, then restore exactly one.
        chunk.body = new_body.rstrip("\n") + "\n"

    doc_path.write_text(serialise(doc), encoding="utf-8", newline="")
