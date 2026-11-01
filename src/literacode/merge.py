"""
literacode three-way merge — model level.

Merges three Document objects (base, ours, theirs) at the level of
named chunks and prose sections — not lines of text.

The ordering rule:
- Narrative order follows ``ours`` as primary.
- Any new chunks that appear in ``theirs`` but not in ``ours`` are inserted
  immediately after the nearest preceding shared chunk (so new narrative
  from theirs lands approximately where theirs put it).

This is the rule that makes Scenario A work:
  - ours  reorders chunks  [A, B, C] → [B, A, C]
  - theirs edits chunk A's body
  - merged result: [B, A_edited, C], zero conflicts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

from .model import Chunk, Document, Prose


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class Conflict:
    """A chunk that was edited differently on both sides."""
    chunk_id: str
    base_body: str | None       # None if the chunk didn't exist in base
    ours_body: str
    theirs_body: str


@dataclass
class MergeResult:
    """Output of three_way_merge()."""
    document: Document              # merged document
    conflicts: list[Conflict] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.conflicts) == 0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _chunk_map(doc: Document) -> dict[str, Chunk]:
    """Return {id: Chunk} for all Chunk nodes in doc."""
    return {c.id: c for c in doc.chunks()}


def _prose_index(doc: Document) -> list[Prose]:
    """Ordered list of Prose nodes."""
    return [n for n in doc.nodes if isinstance(n, Prose)]


def _chunk_order(doc: Document) -> list[str]:
    """Chunk ids in document order."""
    return [n.id for n in doc.nodes if isinstance(n, Chunk)]


# ---------------------------------------------------------------------------
# Three-way merge
# ---------------------------------------------------------------------------

def three_way_merge(
    base: Document,
    ours: Document,
    theirs: Document,
) -> MergeResult:
    """
    Merge three document versions at the model level.

    Change taxonomy applied to each chunk:

    | Base    | Ours      | Theirs    | Result           |
    |---------|-----------|-----------|------------------|
    | present | unchanged | unchanged | keep             |
    | present | changed   | unchanged | take ours        |
    | present | unchanged | changed   | take theirs      |
    | present | changed   | changed = | take either      |
    | present | changed   | changed ≠ | CONFLICT         |
    | present | deleted   | unchanged | delete           |
    | present | unchanged | deleted   | delete           |
    | present | deleted   | deleted   | delete           |
    | present | deleted   | changed   | CONFLICT         |
    | present | changed   | deleted   | CONFLICT         |
    | absent  | added     | absent    | insert from ours |
    | absent  | absent    | added     | insert from theirs|
    | absent  | added     | added =   | insert once      |
    | absent  | added     | added ≠   | CONFLICT         |

    Ordering: follows ours order, with theirs-only additions inserted
    after the last common preceding chunk.
    """
    base_map   = _chunk_map(base)
    ours_map   = _chunk_map(ours)
    theirs_map = _chunk_map(theirs)

    all_ids = (
        set(base_map) | set(ours_map) | set(theirs_map)
    )

    # Resolved body per id (None means deleted)
    resolved: dict[str, str | None] = {}
    conflicts: list[Conflict] = []
    conflict_ids: set[str] = set()

    for cid in all_ids:
        base_chunk   = base_map.get(cid)
        ours_chunk   = ours_map.get(cid)
        theirs_chunk = theirs_map.get(cid)

        base_body   = base_chunk.body   if base_chunk   else None
        ours_body   = ours_chunk.body   if ours_chunk   else None
        theirs_body = theirs_chunk.body if theirs_chunk else None

        if base_body is None:
            # New chunk — not in base
            if ours_body is None and theirs_body is None:
                # Shouldn't happen but be safe
                continue
            elif ours_body is None:
                # Added only in theirs
                resolved[cid] = theirs_body
            elif theirs_body is None:
                # Added only in ours
                resolved[cid] = ours_body
            elif ours_body == theirs_body:
                # Both added the same
                resolved[cid] = ours_body
            else:
                # Both added differently
                conflicts.append(Conflict(
                    chunk_id=cid,
                    base_body=None,
                    ours_body=ours_body,
                    theirs_body=theirs_body,
                ))
                conflict_ids.add(cid)
                resolved[cid] = ours_body  # placeholder
        else:
            # Existed in base
            ours_changed   = ours_body   != base_body
            theirs_changed = theirs_body != base_body

            if ours_body is None and theirs_body is None:
                resolved[cid] = None  # deleted both sides
            elif ours_body is None:
                if not theirs_changed:
                    resolved[cid] = None  # deleted ours, unchanged theirs
                else:
                    conflicts.append(Conflict(
                        chunk_id=cid,
                        base_body=base_body,
                        ours_body="",  # deleted
                        theirs_body=theirs_body,
                    ))
                    conflict_ids.add(cid)
                    resolved[cid] = theirs_body
            elif theirs_body is None:
                if not ours_changed:
                    resolved[cid] = None  # deleted theirs, unchanged ours
                else:
                    conflicts.append(Conflict(
                        chunk_id=cid,
                        base_body=base_body,
                        ours_body=ours_body,
                        theirs_body="",  # deleted
                    ))
                    conflict_ids.add(cid)
                    resolved[cid] = ours_body
            elif not ours_changed and not theirs_changed:
                resolved[cid] = base_body
            elif ours_changed and not theirs_changed:
                resolved[cid] = ours_body
            elif not ours_changed and theirs_changed:
                resolved[cid] = theirs_body
            elif ours_body == theirs_body:
                resolved[cid] = ours_body  # identical edits
            else:
                conflicts.append(Conflict(
                    chunk_id=cid,
                    base_body=base_body,
                    ours_body=ours_body,
                    theirs_body=theirs_body,
                ))
                conflict_ids.add(cid)
                resolved[cid] = ours_body  # placeholder

    # ---------------------------------------------------------------------------
    # Build the merged document in ours order, inserting theirs-only chunks
    # ---------------------------------------------------------------------------
    merged_doc = _build_merged_document(
        base=base,
        ours=ours,
        theirs=theirs,
        resolved=resolved,
        conflict_ids=conflict_ids,
        ours_map=ours_map,
        theirs_map=theirs_map,
    )

    return MergeResult(document=merged_doc, conflicts=conflicts)


def _build_merged_document(
    base: Document,
    ours: Document,
    theirs: Document,
    resolved: dict[str, str | None],
    conflict_ids: set[str],
    ours_map: dict[str, Chunk],
    theirs_map: dict[str, Chunk],
) -> Document:
    """
    Build the merged Document.

    Strategy:
    1. Walk ours nodes in order.
    2. For each Chunk in ours: use the resolved body; skip deleted.
    3. For prose: use ours prose (simple — prose merge is not line-based here).
    4. After each ours chunk, insert any theirs-only chunks (new in theirs,
       absent from ours) that appeared after this chunk in theirs' order.
    """
    ours_chunk_order = _chunk_order(ours)
    theirs_chunk_order = _chunk_order(theirs)
    ours_id_set = set(ours_chunk_order)

    # theirs-only chunks: present in theirs, absent from ours
    theirs_only = [cid for cid in theirs_chunk_order if cid not in ours_id_set]

    # Map each theirs-only chunk to the last ours chunk that preceded it
    # in theirs' ordering
    theirs_only_after: dict[str | None, list[str]] = {}
    # key = ours chunk id (or None meaning "before any ours chunk")
    for cid in theirs_only:
        idx = theirs_chunk_order.index(cid)
        # Find nearest preceding chunk that IS in ours
        anchor: str | None = None
        for preceding in reversed(theirs_chunk_order[:idx]):
            if preceding in ours_id_set:
                anchor = preceding
                break
        theirs_only_after.setdefault(anchor, []).append(cid)

    nodes: list[Prose | Chunk] = []

    # Insert theirs-only chunks that have no ours anchor (go at the start)
    for cid in theirs_only_after.get(None, []):
        body = resolved.get(cid)
        if body is not None:
            src_chunk = theirs_map[cid]
            nodes.append(Chunk(
                id=src_chunk.id,
                file=src_chunk.file,
                lang=src_chunk.lang,
                body=body,
                refs=src_chunk.refs,
                _fence_attrs=src_chunk._fence_attrs,
            ))

    for node in ours.nodes:
        if isinstance(node, Prose):
            nodes.append(Prose(text=node.text))
        elif isinstance(node, Chunk):
            cid = node.id
            body = resolved.get(cid)
            if body is None:
                # Deleted — skip
                continue
            # Use the source chunk from ours for structural attrs;
            # theirs may have a different file/lang if both sides changed attrs
            # (not a case we handle — take ours)
            nodes.append(Chunk(
                id=node.id,
                file=node.file,
                lang=node.lang,
                body=body,
                refs=node.refs,
                _fence_attrs=node._fence_attrs,
            ))
            # Insert any theirs-only chunks anchored after this chunk
            for tcid in theirs_only_after.get(cid, []):
                tbody = resolved.get(tcid)
                if tbody is not None:
                    src = theirs_map[tcid]
                    nodes.append(Chunk(
                        id=src.id,
                        file=src.file,
                        lang=src.lang,
                        body=tbody,
                        refs=src.refs,
                        _fence_attrs=src._fence_attrs,
                    ))

    return Document(nodes=nodes)
