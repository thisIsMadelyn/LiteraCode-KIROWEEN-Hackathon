# task-phase2-1: Three-way diff over the model

## Status
- [ ] Done

## What this is
The core of the merge driver. Given three `Document` objects — base, ours,
theirs — compute what changed on each side at the chunk/prose level and produce
a merged `Document` or a set of conflicts.

This operates on the model, not on text. Line-based diffing is explicitly not
used here.

## Prerequisite
Phase 1 gate must be passed. The model must be stable.

## How to execute

### 1. Define the change taxonomy

For each node (keyed by chunk `id` for chunks, by position for prose):

| Base | Ours | Theirs | Result |
|---|---|---|---|
| exists | unchanged | unchanged | keep as-is |
| exists | changed | unchanged | take ours |
| exists | unchanged | changed | take theirs |
| exists | changed | changed (same edit) | take either |
| exists | changed | changed (different) | **CONFLICT** |
| exists | deleted | unchanged | delete |
| exists | unchanged | deleted | delete |
| exists | deleted | deleted | delete |
| exists | deleted | changed | **CONFLICT** |
| exists | changed | deleted | **CONFLICT** |
| absent | added | absent | insert ours |
| absent | absent | added | insert theirs |
| absent | added | added (same) | insert once |
| absent | added | added (different) | **CONFLICT** |

For prose sections: equality is byte-for-byte identity. A reorder is not a
change to the prose content; it is a structural change (handled separately).

For chunks: equality is body equality. A chunk moved to a different position in
the narrative is still the same chunk — identity comes from `id`, not position.

### 2. Create `src/literacode/merge.py`

```python
from dataclasses import dataclass
from .model import Document, Chunk, Prose

@dataclass
class Conflict:
    chunk_id: str
    base: str | None
    ours: str
    theirs: str

@dataclass
class MergeResult:
    document: Document          # merged document (may contain placeholder nodes)
    conflicts: list[Conflict]   # empty = clean merge

def three_way_merge(base: Document, ours: Document, theirs: Document) -> MergeResult:
    ...
```

### 3. Ordering strategy

The narrative order in the merged document follows `ours` as the primary, then
inserts any new chunks from `theirs` that don't exist in `ours` at the position
that best preserves the theirs narrative (after the nearest preceding shared
chunk).

This is the rule that makes Scenario A work: if `ours` reordered chunks and
`theirs` edited a chunk body, the merged order is `ours`' order with `theirs`'
body edits applied.

### 4. Smoke test

`tests/test_merge.py`:
- Scenario A: base has chunks [A, B, C]. Ours reorders to [B, A, C]. Theirs
  edits chunk A's body. Merged result: [B, A_edited, C]. No conflicts.
- Scenario B: base has chunk A. Both ours and theirs edit A differently.
  Result: one Conflict with the right base/ours/theirs values.

## Done when
- `three_way_merge()` exists and is importable
- Scenario A smoke test produces a clean merge with the correct order
- Scenario B smoke test produces exactly one Conflict
