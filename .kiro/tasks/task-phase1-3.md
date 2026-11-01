# task-phase1-3: `lit stitch` — edited `.py` files back into the document

## Status
- [ ] Done

## What this is
The reverse direction. After a developer edits a tangled `.py` file, `lit stitch`
reads each chunk region (identified by its sync marker), finds the corresponding
chunk in the source document by `id`, and replaces the chunk body with the
edited version.

This is the harder direction. The sync markers are the only reliable anchor —
do not infer chunk identity from position or content.

## Prerequisite
task-phase1-2 must be done. Stitch reads the markers tangle wrote.

## How to execute

### 1. Create `src/literacode/stitch.py`

Core function:
```python
def stitch(py_path: Path, doc_path: Path) -> None:
    """
    Read edited chunk bodies from py_path, update doc_path in place.
    Raises if a sync marker references a chunk id not found in the document.
    """
```

Algorithm:
1. Read `py_path` and split into regions at `# lit:chunk id=...` markers.
2. For each region, extract `id` and `src` from the marker.
3. Assert `src` matches `doc_path` (refuse to stitch a file tangled from a
   different document).
4. Parse `doc_path` into a Document.
5. For each extracted (id, body) pair, find the matching `Chunk` node and
   replace its `.body` with the new body.
6. Serialise the updated Document back to `doc_path`.

### 2. Document serialiser

You need a way to write a `Document` back to markdown. This is the most
fragile part. Rules:
- Prose nodes are written verbatim — every byte preserved.
- Chunk nodes are written as a fenced block with the original attribute line,
  then the new body, then the closing fence.
- The output must be byte-for-byte identical to the input if no chunk bodies
  changed. Test this explicitly.

Keep the serialiser as dumb as possible: it reconstructs fences from the
model, nothing else.

### 3. Error cases — fail loudly

| Situation | Behaviour |
|---|---|
| Sync marker has `id=` not in the document | raise `StitchError` with the id |
| Sync marker has `src=` pointing to a different document | raise `StitchError` |
| Two sync markers with the same `id=` in one `.py` file | raise `StitchError` |
| `.py` file has no sync markers at all | do nothing, exit 0 |

Never silently discard edits. If something is wrong, crash with a clear message.

### 4. Wire up the CLI

```python
def cmd_stitch(args):
    from .stitch import stitch
    for py_file in args.files:
        stitch(Path(py_file), ...)  # doc_path read from the marker
        print(f"  stitched {py_file}")
```

`lit stitch src/literacode/parser.py` reads the sync markers inside that file
to find the source document path automatically.

### 5. Smoke test

In `tests/test_stitch.py`:
- Start from a fixture document.
- Tangle it to a temp directory.
- Edit one chunk body in the tangled file.
- Stitch back.
- Re-parse the document and assert the chunk body matches the edit.
- Assert all prose nodes are byte-for-byte unchanged.

## Done when
- `lit stitch <file.py>` updates the source document
- The smoke test passes
- An unmodified stitch is a no-op (document unchanged)
