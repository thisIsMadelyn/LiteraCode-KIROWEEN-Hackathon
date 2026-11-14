<!-- generated files: src/literacode/tangle.py -->
<!-- do not edit generated files directly: edit this document, then run `lit tangle`, or edit the .py and run `lit stitch` -->

# Tangle: document to Python files

`lit tangle` turns the chunks that name a `file=` target into ordinary `.py` files. Each chunk is written after a sync marker comment that names the chunk and its source document. Stitch later reads those markers to find its way back, so the markers are bookkeeping and are never edited by hand.

## `src/literacode/tangle.py`

The marker format is fixed by the grammar: `# lit:chunk id=<id> src=<doc>`.

```python id=tangle-header file=src/literacode/tangle.py
"""
literacode tangle — model → .py files on disk.

For each unique `file=` target in the document, writes one .py file.
Each chunk region is preceded by a sync marker comment so stitch can
find its way back.

Sync marker format (from lit/format.md, section 4):
    # lit:chunk id=<id> src=<doc_path>
"""
from __future__ import annotations

import re
from pathlib import Path

from .model import Chunk, Document

SYNC_MARKER = "# lit:chunk id={id} src={src}"
REF_RE = re.compile(r"<<([\w-]+)>>")
```

Tangling can fail on a missing or circular reference. Those are errors, not warnings.

```python id=TangleError file=src/literacode/tangle.py
class TangleError(Exception):
    """Raised for unresolvable errors during tangling."""
```

A chunk body may refer to another chunk with a double-angle-bracket id. References expand depth first and a cycle is a hard error.

```python id=_expand_refs file=src/literacode/tangle.py
def _expand_refs(chunk: Chunk, doc: Document, seen: frozenset[str]) -> str:
    """
    Expand chunk references in chunk.body recursively.
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
```

Rendering builds the text of every target file without touching the disk. Regions of one file are separated by two blank lines, which is also what PEP 8 wants between top-level definitions.

```python id=render file=src/literacode/tangle.py
def render(doc: Document, doc_path: Path, out_root: Path) -> dict[Path, str]:
    """
    The tangled text of every file the document targets, without writing.

    Args:
        doc:      The parsed Document.
        doc_path: Path to the source document (used in sync markers).
        out_root: Root directory for output files.  file= paths are resolved
                  relative to out_root.

    Returns:
        {output path: file text}, one entry per unique file= target.
    """
    # Group chunks by target file, preserving document order
    file_chunks: dict[str, list[Chunk]] = {}
    for chunk in doc.chunks():
        if chunk.file is None:
            continue  # not a tangle target
        if chunk.file not in file_chunks:
            file_chunks[chunk.file] = []
        file_chunks[chunk.file].append(chunk)

    rendered: dict[Path, str] = {}

    for file_rel, chunks in file_chunks.items():
        out_path = out_root / file_rel

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

        rendered[out_path] = "\n".join(lines)

    return rendered
```

Writing is a thin wrapper over rendering.

```python id=tangle file=src/literacode/tangle.py
def tangle(doc: Document, doc_path: Path, out_root: Path) -> list[Path]:
    """Write tangled .py files.  Returns the paths written."""
    rendered = render(doc, doc_path, out_root)
    for out_path, text in rendered.items():
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8", newline="")
    return list(rendered)
```

`lit tangle --check` uses this to find generated files that no longer match their document. The pre-commit hook relies on it.

```python id=stale file=src/literacode/tangle.py
def stale(doc: Document, doc_path: Path, out_root: Path) -> list[Path]:
    """Targets whose file on disk differs from (or is missing from) the tangle."""
    out = []
    for out_path, text in render(doc, doc_path, out_root).items():
        on_disk = (
            out_path.read_text(encoding="utf-8", newline="")
            if out_path.is_file() else None
        )
        if on_disk != text:
            out.append(out_path)
    return out
```
