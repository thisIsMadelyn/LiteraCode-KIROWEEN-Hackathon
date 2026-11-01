"""
literacode tangle — model → .py files on disk.

For each unique `file=` target in the document, writes one .py file.
Each chunk region is preceded by a sync marker comment so stitch can
find its way back.

Sync marker format (from format-grammar.md §4):
    # lit:chunk id=<id> src=<doc_path>
"""
from __future__ import annotations

import re
from pathlib import Path

from .model import Chunk, Document

SYNC_MARKER = "# lit:chunk id={id} src={src}"
REF_RE = re.compile(r"<<([\w-]+)>>")


class TangleError(Exception):
    """Raised for unresolvable errors during tangling."""


def _expand_refs(chunk: Chunk, doc: Document, seen: frozenset[str]) -> str:
    """
    Expand <<other-id>> references in chunk.body recursively.
    Returns the fully-expanded body.
    """
    if chunk.id in seen:
        raise TangleError(f"Circular chunk reference: {chunk.id}")
    seen = seen | {chunk.id}

    def replace(m: re.Match) -> str:  # type: ignore[type-arg]
        ref_id = m.group(1)
        ref_chunk = doc.get_chunk(ref_id)
        if ref_chunk is None:
            raise TangleError(
                f"Chunk '{chunk.id}' references '{ref_id}' which does not exist"
            )
        return _expand_refs(ref_chunk, doc, seen)

    return REF_RE.sub(replace, chunk.body)


def tangle(doc: Document, doc_path: Path, out_root: Path) -> list[Path]:
    """
    Write tangled .py files.

    Args:
        doc:      The parsed Document.
        doc_path: Path to the source document (used in sync markers).
        out_root: Root directory for output files.  file= paths are resolved
                  relative to out_root.

    Returns:
        List of Path objects written (one per unique file= target).
    """
    # Group chunks by target file, preserving document order
    file_chunks: dict[str, list[Chunk]] = {}
    for chunk in doc.chunks():
        if chunk.file is None:
            continue  # not a tangle target
        if chunk.file not in file_chunks:
            file_chunks[chunk.file] = []
        file_chunks[chunk.file].append(chunk)

    written: list[Path] = []

    for file_rel, chunks in file_chunks.items():
        out_path = out_root / file_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Normalise doc_path to be relative to out_root if possible,
        # otherwise use as-is (relative paths look better in markers)
        try:
            src_str = str(doc_path.relative_to(out_root)).replace("\\", "/")
        except ValueError:
            src_str = str(doc_path).replace("\\", "/")

        lines: list[str] = []
        for i, chunk in enumerate(chunks):
            marker = SYNC_MARKER.format(id=chunk.id, src=src_str)
            body = _expand_refs(chunk, doc, frozenset())
            # Ensure body ends with exactly one newline
            if not body.endswith("\n"):
                body += "\n"
            lines.append(marker)
            lines.append(body)
            if i < len(chunks) - 1:
                lines.append("")  # blank separator between regions

        out_path.write_text("\n".join(lines), encoding="utf-8", newline="")
        written.append(out_path)

    return written
