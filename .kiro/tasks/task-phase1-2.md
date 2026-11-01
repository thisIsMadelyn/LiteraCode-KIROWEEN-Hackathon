# task-phase1-2: `lit tangle` — model to `.py` files on disk, with sync markers

## Status
- [x] Done

## What this is
The forward direction of the round trip. Given a parsed document, `lit tangle`
writes one `.py` file per unique `file=` target found in the chunks. Each chunk
region in the output file is preceded by a sync marker comment so `lit stitch`
can find its way back.

## Prerequisite
task-phase1-1 must be done. Tangle operates on the model, not raw text.

## How to execute

### 1. Create `src/literacode/tangle.py`

Core function:
```python
def tangle(doc: Document, doc_path: Path, out_root: Path) -> list[Path]:
    """Write tangled .py files. Returns list of paths written."""
```

Algorithm:
1. Collect all `Chunk` nodes that have a `file=` attribute.
2. Group by `file` value (preserving document order within each group).
3. For each target file:
   a. Create parent directories if needed.
   b. Write each chunk region with a sync marker header:
      ```python
      # lit:chunk id=<id> src=<doc_path>
      <body lines>
      ```
   c. Separate chunk regions with a blank line.
4. Return the list of written paths.

### 2. Sync marker format (from task-phase0-3)

```python
SYNC_MARKER = "# lit:chunk id={id} src={src}"
```

The marker is the first line of each chunk region. It must be:
- A valid Python comment
- Machine-parseable by a simple regex in stitch
- Never modified by hand

### 3. Chunk references (`<<id>>`)

If a chunk body contains `<<other-chunk-id>>`, substitute the body of that
chunk inline at tangle time. Resolution order: depth-first, in document order.
Circular references must raise a clear error, not loop forever.

> **Cut-order note:** if this is getting complex, references can be deferred
> (see PLAN.md cut item 3). Single-chunk-per-file still covers the demo.

### 4. Wire up the CLI

In `src/literacode/cli.py`:
```python
import argparse
from pathlib import Path
from .parser import parse_document
from .tangle import tangle

def cmd_tangle(args):
    doc = parse_document(Path(args.file))
    written = tangle(doc, Path(args.file), Path("."))
    for p in written:
        print(f"  wrote {p}")
```

`lit tangle <file.md>` runs this.

### 5. Smoke test

In `tests/test_tangle.py`:
- Parse a fixture document with two chunks targeting the same file.
- Call `tangle()`.
- Read the output file and assert:
  - Both sync markers are present.
  - Both chunk bodies appear in order.
  - No fence lines (` ``` `) appear in the output.

## Done when
- `lit tangle somefile.md` writes `.py` files to disk
- Each chunk region in the output starts with a `# lit:chunk ...` comment
- The smoke test passes
- Running tangle twice produces identical output (deterministic)
