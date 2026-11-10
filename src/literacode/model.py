"""
literacode document model.

A Document is an ordered list of Prose and Chunk nodes, reflecting the source
order in the markdown file.  Order matters: it is what the merge driver diffs.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Prose:
    """Raw markdown text between (or before/after) chunk fences."""
    text: str  # verbatim, every byte preserved


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
