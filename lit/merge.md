<!-- generated files: src/literacode/merge.py, src/literacode/driver.py -->
<!-- do not edit generated files directly: edit this document, then run `lit tangle`, or edit the .py and run `lit stitch` -->

# The merge driver

Git merges lines of text, which is why a reordered chunk plus an edited chunk body turns into garbage. This module merges the parsed documents instead. Chunks are matched by id, each one is resolved on its own, and the result is laid out in the order of our side. Only a chunk edited differently on both sides is a conflict, and the driver then hands the decision to a human instead of inventing content.

## `src/literacode/merge.py`

The layout rule is: our order wins, and a chunk only theirs has is placed after the nearest preceding chunk that ours also has.

```python id=merge-header file=src/literacode/merge.py
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
```

A conflict records all three versions of one chunk body. `kind` says whether it is a chunk or the prose before a chunk.

```python id=Conflict file=src/literacode/merge.py
@dataclass
class Conflict:
    """A chunk that was changed incompatibly on both sides."""
    chunk_id: str
    base_body: str | None       # None if the chunk didn't exist in base
    ours_body: str              # "" if ours deleted the chunk
    theirs_body: str            # "" if theirs deleted the chunk
    kind: str = "chunk"         # "chunk" or "prose" (then chunk_id is the slot key)
```

The result is the merged document plus whatever could not be merged.

```python id=MergeResult file=src/literacode/merge.py
@dataclass
class MergeResult:
    """Output of three_way_merge()."""
    document: Document              # merged document
    conflicts: list[Conflict] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.conflicts) == 0
```

One rule covers every case for a body or a prose slot: identical on both sides, changed on only one side, or changed differently on both. `None` means absent, so adds and deletes are handled by the same rule.

```python id=_resolve file=src/literacode/merge.py
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
```

Every chunk is resolved by id first, and only then is the document laid out. Separating the two is what lets a reorder on one side and an edit on the other combine cleanly.

```python id=three_way_merge file=src/literacode/merge.py
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

    document = _layout(ours, theirs, resolved, theirs_map, base, conflicts)
    return MergeResult(document=document, conflicts=conflicts)
```

Prose has no identity of its own, so it is keyed by the chunk that follows it. Trailing prose gets the key `None`.

```python id=_slots file=src/literacode/merge.py
def _slots(doc: Document) -> dict[str | None, str]:
    """Prose text keyed by the id of the following chunk (None = trailing)."""
    slots: dict[str | None, str] = {}
    pending = ""
    for node in doc.nodes:
        if isinstance(node, Prose):
            pending += node.text
        else:
            if pending:
                slots[node.id] = pending
            pending = ""
    if pending:
        slots[None] = pending
    return slots
```

The merged document follows ours. Each prose slot goes through the same resolve rule as a chunk body. If both sides changed a slot differently, ours is kept, markers are written into the prose, and a conflict is recorded.

```python id=_layout file=src/literacode/merge.py
def _layout(
    ours: Document,
    theirs: Document,
    resolved: dict[str, str | None],
    theirs_map: dict[str, Chunk],
    base: Document,
    conflicts: list[Conflict],
) -> Document:
    """Build the merged Document in ours order, slotting in theirs-only chunks."""
    ours_ids = {c.id for c in ours.chunks()}
    base_slots, ours_slots, theirs_slots = _slots(base), _slots(ours), _slots(theirs)

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

    def emit_slot(key: str | None) -> None:
        o, t = ours_slots.get(key), theirs_slots.get(key)
        text, is_conflict = _resolve(base_slots.get(key), o, t)
        if is_conflict:
            conflicts.append(Conflict(
                chunk_id="" if key is None else key,
                base_body=base_slots.get(key),
                ours_body=o or "",
                theirs_body=t or "",
                kind="prose",
            ))
            text = (
                "<<<<<<< ours\n" + _nl(o) + "=======\n" + _nl(t)
                + ">>>>>>> theirs\n"
            )
        if text:
            nodes.append(Prose(text=text))

    def emit_theirs_only(anchor_id: str | None) -> None:
        for tid in after.get(anchor_id, []):
            body = resolved[tid]
            if body is not None:
                emit_slot(tid)
                nodes.append(replace(theirs_map[tid], body=body))

    emit_theirs_only(None)
    for node in ours.nodes:
        if isinstance(node, Prose):
            continue
        body = resolved[node.id]
        if body is None:
            continue  # deleted
        emit_slot(node.id)
        # Structural attributes (file, lang, fence) are taken from ours.
        nodes.append(replace(node, body=body))
        emit_theirs_only(node.id)
    emit_slot(None)

    return Document(nodes=nodes)
```

Marker blocks need every part to end with a newline.

```python id=_nl file=src/literacode/merge.py
def _nl(text: str | None) -> str:
    text = text or ""
    return text if not text or text.endswith("\n") else text + "\n"
```

## `src/literacode/driver.py`

Git calls the driver with three file paths and expects the result in the second one (ours). Exit 0 means merged cleanly and exit 1 means conflicts remain.

```python id=driver-header file=src/literacode/driver.py
"""
literacode merge driver — called by git as: lit merge %O %A %B %P

Exit 0 = clean merge.  Exit 1 = conflicts remain.
Output is always written to the %A path (ours).
"""
from __future__ import annotations

import sys
from pathlib import Path

from .merge import MergeResult, three_way_merge
from .model import Chunk
from .parser import parse_document
from .serialiser import serialise
```

A conflicted chunk is tagged in its fence so `lit resolve` can find it.

```python id=_CONFLICT_ATTR file=src/literacode/driver.py
# ---------------------------------------------------------------------------
# Conflict marker format (for lit resolve to find later)
# ---------------------------------------------------------------------------

_CONFLICT_ATTR = " lit:conflict"
```

A conflicted body is replaced by an ours/theirs marker block in the usual git style. The driver never invents a merged body.

```python id=_embed_conflict_markers file=src/literacode/driver.py
def _embed_conflict_markers(result: MergeResult) -> None:
    """
    In-place: replace conflicted Chunk bodies in result.document with a
    conflict-marker block so lit resolve can locate them.

    Conflict marker format embedded in the chunk body:

        <<<<<<< ours
        <ours body>
        =======
        <theirs body>
        >>>>>>> theirs
    """
    conflict_map = {c.chunk_id: c for c in result.conflicts if c.kind == "chunk"}

    for node in result.document.nodes:
        if not isinstance(node, Chunk):
            continue
        if node.id not in conflict_map:
            continue
        c = conflict_map[node.id]
        marker_body = (
            "<<<<<<< ours\n"
            + (c.ours_body or "")
            + "=======\n"
            + (c.theirs_body or "")
            + ">>>>>>> theirs\n"
        )
        node.body = marker_body
        # Tag the chunk's fence attrs so lit resolve can find it
        if _CONFLICT_ATTR not in node._fence_attrs:
            node._fence_attrs = node._fence_attrs + _CONFLICT_ATTR
```

The entry point parses all three files, merges, writes the result over ours, and reports each conflict on stderr.

```python id=merge_driver file=src/literacode/driver.py
def merge_driver(
    base: Path,
    ours: Path,
    theirs: Path,
    path_hint: str = "",
) -> int:
    """
    Main merge driver entry point.

    Args:
        base:      Path to the common ancestor file (%O).
        ours:      Path to our version (%A).  Result is written here.
        theirs:    Path to their version (%B).
        path_hint: The working-tree path of the file (%P), for messages.

    Returns:
        0 if the merge is clean, 1 if conflicts remain.
    """
    base_doc   = parse_document(base)
    ours_doc   = parse_document(ours)
    theirs_doc = parse_document(theirs)

    result = three_way_merge(base_doc, ours_doc, theirs_doc)

    # Embed conflict markers into the document before serialising
    if result.conflicts:
        _embed_conflict_markers(result)

    ours.write_text(serialise(result.document), encoding="utf-8", newline="")

    if result.conflicts:
        for conflict in result.conflicts:
            what = "chunk" if conflict.kind == "chunk" else "prose before chunk"
            print(
                f"CONFLICT (literacode): {what} '{conflict.chunk_id}' "
                f"modified on both sides in {path_hint or str(ours)}",
                file=sys.stderr,
            )
        return 1

    return 0
```
