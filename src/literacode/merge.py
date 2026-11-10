"""
literacode three-way merge — model level.

Merges three Document objects (base, ours, theirs) at the level of
named chunks and prose sections — not lines of text.

Each chunk is resolved independently by identity (its id), then the merged
document is laid out in ``ours`` order.  That separation is what makes
Scenario A work:
  - ours  reorders chunks  [A, B, C] → [B, A, C]
  - theirs edits chunk A's body
  - merged result: [B, A_edited, C], zero conflicts.

Layout rule:
- Narrative order follows ``ours``.
- A chunk that exists only in ``theirs`` is inserted immediately after the
  nearest preceding chunk (in theirs' order) that ``ours`` also has.
- Prose is taken from ``ours`` unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from .model import Chunk, Document, Prose


@dataclass
class Conflict:
    """A chunk that was changed incompatibly on both sides."""
    chunk_id: str
    base_body: str | None       # None if the chunk didn't exist in base
    ours_body: str              # "" if ours deleted the chunk
    theirs_body: str            # "" if theirs deleted the chunk


@dataclass
class MergeResult:
    """Output of three_way_merge()."""
    document: Document              # merged document
    conflicts: list[Conflict] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.conflicts) == 0


def _resolve(
    base: str | None, ours: str | None, theirs: str | None
) -> tuple[str | None, bool]:
    """
    Resolve one chunk body.  ``None`` means the chunk is absent on that side.

    Returns (resolved_body, is_conflict).  ``resolved_body`` None means the
    chunk is deleted.  On conflict the body is a placeholder (ours, or theirs
    if ours deleted it) that the driver replaces with conflict markers.

    This single rule covers every row of the change taxonomy: added, edited,
    deleted, identical on both sides, and edit-vs-delete.
    """
    if ours == theirs:
        return ours, False
    if ours == base:
        return theirs, False
    if theirs == base:
        return ours, False
    return (ours if ours is not None else theirs), True


def three_way_merge(
    base: Document,
    ours: Document,
    theirs: Document,
) -> MergeResult:
    """Merge three document versions at the model level."""
    base_map = {c.id: c for c in base.chunks()}
    ours_map = {c.id: c for c in ours.chunks()}
    theirs_map = {c.id: c for c in theirs.chunks()}

    # Deterministic order: ours, then theirs-only, then base-only.
    all_ids = list(dict.fromkeys([*ours_map, *theirs_map, *base_map]))

    resolved: dict[str, str | None] = {}
    conflicts: list[Conflict] = []

    for cid in all_ids:
        b, o, t = (m.get(cid) for m in (base_map, ours_map, theirs_map))
        base_body = b.body if b else None
        ours_body = o.body if o else None
        theirs_body = t.body if t else None

        body, is_conflict = _resolve(base_body, ours_body, theirs_body)
        resolved[cid] = body
        if is_conflict:
            conflicts.append(Conflict(
                chunk_id=cid,
                base_body=base_body,
                ours_body=ours_body if ours_body is not None else "",
                theirs_body=theirs_body if theirs_body is not None else "",
            ))

    return MergeResult(
        document=_layout(ours, theirs, resolved, theirs_map),
        conflicts=conflicts,
    )


def _layout(
    ours: Document,
    theirs: Document,
    resolved: dict[str, str | None],
    theirs_map: dict[str, Chunk],
) -> Document:
    """Build the merged Document in ours order, slotting in theirs-only chunks."""
    ours_ids = {c.id for c in ours.chunks()}

    # Anchor each theirs-only chunk to the nearest preceding chunk in theirs'
    # order that ours also has (None = before any shared chunk).
    after: dict[str | None, list[str]] = {}
    anchor: str | None = None
    for chunk in theirs.chunks():
        if chunk.id in ours_ids:
            anchor = chunk.id
        else:
            after.setdefault(anchor, []).append(chunk.id)

    nodes: list[Prose | Chunk] = []

    def emit_theirs_only(anchor_id: str | None) -> None:
        for tid in after.get(anchor_id, []):
            body = resolved[tid]
            if body is not None:
                nodes.append(replace(theirs_map[tid], body=body))

    emit_theirs_only(None)
    for node in ours.nodes:
        if isinstance(node, Prose):
            nodes.append(node)
            continue
        body = resolved[node.id]
        if body is None:
            continue  # deleted
        # Structural attributes (file, lang, fence) are taken from ours.
        nodes.append(replace(node, body=body))
        emit_theirs_only(node.id)

    return Document(nodes=nodes)
