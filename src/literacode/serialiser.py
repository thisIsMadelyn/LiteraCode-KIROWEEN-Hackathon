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
