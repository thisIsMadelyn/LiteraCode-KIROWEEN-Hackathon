<!-- generated files: src/literacode/model.py, src/literacode/parser.py, src/literacode/serialiser.py, src/literacode/__init__.py -->
<!-- do not edit generated files directly: edit this document, then run `lit tangle`, or edit the .py and run `lit stitch` -->

# The document format

A literacode document is ordinary markdown. A fenced code block that carries an `id=` attribute becomes a *chunk*: a named unit with an identity that survives edits and reordering. Everything else is *prose*. This document holds the model that describes that structure, the parser that builds it, and the serialiser that writes it back byte for byte. The grammar itself is in `lit/format-grammar.md`.

## `src/literacode/model.py`

The model is a flat, ordered list of nodes. Order matters because it is what the merge driver compares.

```python id=model-header file=src/literacode/model.py
"""
literacode document model.

A Document is an ordered list of Prose and Chunk nodes, reflecting the source
order in the markdown file.  Order matters: it is what the merge driver diffs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
```

Prose is stored verbatim, every byte, so that serialising never changes the narrative.

```python id=Prose file=src/literacode/model.py
@dataclass
class Prose:
    """Raw markdown text between (or before/after) chunk fences."""
    text: str  # verbatim, every byte preserved
```

A chunk is the unit of identity. `_fence_attrs` keeps the raw attribute string of the opening fence so the fence can be reproduced exactly.

```python id=Chunk file=src/literacode/model.py
@dataclass
class Chunk:
    """A named fenced code block — the unit of identity in literacode."""
    id: str
    file: str | None   # target output path for tangle; None if not a tangle target
    lang: str          # language tag (e.g. "python")
    body: str          # code body — no fence lines; trailing newline preserved

    # The raw attribute string from the opening fence line, e.g.
    # "python id=foo file=bar.py".  Stored so the serialiser can reproduce the
    # fence exactly without having to reconstruct it from parsed fields.
    _fence_attrs: str = field(default="", repr=False, compare=False)
```

The document is the node list plus two lookups by chunk id.

```python id=Document file=src/literacode/model.py
@dataclass
class Document:
    """The parsed representation of a literacode markdown file."""
    nodes: list[Prose | Chunk] = field(default_factory=list)

    def chunks(self) -> list[Chunk]:
        """All Chunk nodes, in document order."""
        return [n for n in self.nodes if isinstance(n, Chunk)]

    def get_chunk(self, chunk_id: str) -> Chunk | None:
        """Return the first Chunk with the given id, or None."""
        for n in self.nodes:
            if isinstance(n, Chunk) and n.id == chunk_id:
                return n
        return None
```

## `src/literacode/parser.py`

The parser is a small line-by-line state machine, not a markdown library. It only needs to find fences, and it must preserve everything it does not understand.

```python id=parser-header file=src/literacode/parser.py
"""
literacode parser — document → model.

State machine over lines.  A fenced code block with an `id=` attribute becomes
a Chunk; everything else (including plain fences without id=) accumulates as
Prose.
"""
from __future__ import annotations

import re
from pathlib import Path

from .model import Chunk, Document, Prose

# Opening fence: ```[lang][attrs]  (the language may be absent)
# Group 1 = fence marker, 2 = lang, 3 = rest of attribute string (may be empty)
FENCE_OPEN_RE = re.compile(r"^(```+)(\w*)([ \t].*)?\s*$")

# Key=value tokens in the attribute string
ATTR_RE = re.compile(r"([\w-]+)=(\S+)")
```

Fence attributes are space-separated `key=value` tokens. Values cannot contain spaces, which keeps the syntax quote-free.

```python id=_parse_attrs file=src/literacode/parser.py
def _parse_attrs(attr_str: str) -> dict[str, str]:
    """Return {key: value} from a space-separated key=value string."""
    return {m.group(1): m.group(2) for m in ATTR_RE.finditer(attr_str)}
```

Reading a file keeps line endings as they are (`newline=""`), which the round-trip guarantee depends on.

```python id=parse_document file=src/literacode/parser.py
def parse_document(path: Path) -> Document:
    """
    Parse a literacode markdown file and return a Document.

    Any .md file is valid input.  A file with no chunk attributes produces
    a Document with a single Prose node (or an empty Document for empty files).
    """
    text = path.read_text(encoding="utf-8", newline="")
    return parse_string(text)
```

A fence with an `id=` opens a chunk. A fence without one is prose, so ordinary code samples in a document stay invisible to the tool.

```python id=parse_string file=src/literacode/parser.py
def parse_string(text: str) -> Document:
    """Parse a literacode document from a string."""
    lines = text.splitlines(keepends=True)
    doc = Document()

    prose_lines: list[str] = []
    chunk_lines: list[str] = []
    in_chunk = False
    plain_fence_marker = ""             # set while inside a fence with no id=
    current_fence_marker: str = ""      # the backtick prefix (``` or ````)
    current_fence_attrs: str = ""       # the raw attribute string after lang
    current_lang: str = ""
    current_id: str = ""
    current_file: str | None = None
    current_attrs_raw: str = ""

    def flush_prose() -> None:
        if prose_lines:
            doc.nodes.append(Prose(text="".join(prose_lines)))
            prose_lines.clear()

    def flush_chunk() -> None:
        doc.nodes.append(
            Chunk(
                id=current_id,
                file=current_file,
                lang=current_lang,
                body="".join(chunk_lines),
                _fence_attrs=current_attrs_raw,
            )
        )
        chunk_lines.clear()

    for line in lines:
        if plain_fence_marker:
            # Inside a plain fence: everything up to its closing fence is
            # prose, even lines that look like chunk fences (CommonMark rule).
            prose_lines.append(line)
            if line.rstrip("\n\r") == plain_fence_marker:
                plain_fence_marker = ""
        elif not in_chunk:
            # Check for an opening fence
            m = FENCE_OPEN_RE.match(line)
            if m:
                fence_marker = m.group(1)   # ``` or ````
                lang = m.group(2)
                attr_str = m.group(3) or ""
                attrs = _parse_attrs(attr_str)
                if "id" in attrs:
                    # This is a literacode chunk
                    flush_prose()
                    # Stash opening fence line as prose so we can reconstruct it
                    in_chunk = True
                    current_fence_marker = fence_marker
                    current_lang = lang
                    current_id = attrs["id"]
                    current_file = attrs.get("file")
                    # Preserve the original attribute string (after lang) exactly
                    current_attrs_raw = (m.group(3) or "").rstrip()
                    chunk_lines.clear()
                    continue
                # Plain fence without id= → prose
                prose_lines.append(line)
                plain_fence_marker = fence_marker
            else:
                prose_lines.append(line)
        else:
            # Inside a chunk — look for the closing fence
            stripped = line.rstrip("\n\r")
            if stripped == current_fence_marker:
                # Closing fence
                flush_chunk()
                in_chunk = False
                current_fence_marker = ""
            else:
                chunk_lines.append(line)

    # Flush any remaining content
    if in_chunk:
        # Unclosed fence — treat accumulated lines as prose (be lenient)
        # Re-emit the opening fence line and the body as prose
        prose_lines.append(
            f"{current_fence_marker}{current_lang}{current_attrs_raw}\n"
        )
        prose_lines.extend(chunk_lines)
        flush_prose()
    else:
        flush_prose()

    return doc
```

## `src/literacode/serialiser.py`

Serialising is the inverse of parsing. With no body changes the output must equal the input exactly.

```python id=serialiser-header file=src/literacode/serialiser.py
"""
literacode serialiser — model → markdown.

Rules (from format-grammar.md §6):
- Prose nodes are written verbatim.  Every byte is preserved.
- Chunk nodes are reconstructed from their model fields: opening fence line,
  body, closing fence.  The _fence_attrs field reproduces the original
  attribute string exactly.
- The output is byte-for-byte identical to the input when no chunk bodies
  have changed.
"""
from __future__ import annotations

from .model import Chunk, Document, Prose
```

Prose is written back untouched. A chunk is rebuilt from its fence attributes, its body and the closing fence.

```python id=serialise file=src/literacode/serialiser.py
def serialise(doc: Document) -> str:
    """Return the markdown text for a Document."""
    parts: list[str] = []

    for node in doc.nodes:
        if isinstance(node, Prose):
            parts.append(node.text)
        elif isinstance(node, Chunk):
            # Opening fence: ```lang [attrs]
            # _fence_attrs already has the leading space when present
            fence_open = f"```{node.lang}{node._fence_attrs}\n"
            fence_close = "```\n"
            parts.append(fence_open)
            parts.append(node.body)
            parts.append(fence_close)
        else:
            raise TypeError(f"Unknown node type: {type(node)}")

    return "".join(parts)
```

## `src/literacode/__init__.py`

The package marker.

```python id=package-init file=src/literacode/__init__.py
# literacode — literate markdown round-trip and merge driver
```
