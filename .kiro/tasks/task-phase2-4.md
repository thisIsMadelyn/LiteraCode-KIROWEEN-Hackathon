# task-phase2-4: Exit codes correct, conflict markers written where unresolvable

## Status
- [ ] Done

## What this is
`lit merge %O %A %B %P` is what git actually calls. It must:
- Exit 0 if the merge was clean (git will accept the result).
- Exit 1 if conflicts remain (git will mark the merge as failed).
- Write its output to `%A` (the "ours" file path), which is what git reads.
- Write conflict markers into the document for any unresolvable chunks, so
  `lit resolve` can find them later.

## Prerequisite
task-phase2-1 (three-way merge logic) must be done.

## How to execute

### 1. Create `src/literacode/driver.py`

```python
import sys
from pathlib import Path
from .parser import parse_document
from .merge import three_way_merge
from .serialiser import serialise  # the document → markdown writer from stitch

def merge_driver(base: str, ours: str, theirs: str, path: str) -> int:
    """
    Called as: lit merge %O %A %B %P
    base  = %O  (common ancestor)
    ours  = %A  (current branch — we write the result here)
    theirs = %B (incoming branch)
    path  = %P  (the pathname of the file being merged, for messages)
    Returns exit code: 0 = clean, 1 = conflicts.
    """
    base_doc  = parse_document(Path(base))
    ours_doc  = parse_document(Path(ours))
    theirs_doc = parse_document(Path(theirs))

    result = three_way_merge(base_doc, ours_doc, theirs_doc)

    if result.conflicts:
        merged_doc = _embed_conflict_markers(result)
        Path(ours).write_text(serialise(merged_doc))
        _print_conflicts(result.conflicts, path)
        return 1
    else:
        Path(ours).write_text(serialise(result.document))
        return 0
```

### 2. Conflict marker format

When a chunk has a conflict, embed it in the document as a special fenced
block that `lit resolve` can find:

````markdown
```python id=parse file=src/demo/main.py lit:conflict
<<<<<<< ours
def parse(text):
    return text.split()
=======
def parse(text):
    return [t.strip(".,") for t in text.split()]
>>>>>>> theirs
```
````

The `lit:conflict` attribute is the flag `lit resolve` scans for.

### 3. Wire up the CLI

```python
def cmd_merge(args):
    from .driver import merge_driver
    sys.exit(merge_driver(args.base, args.ours, args.theirs, args.path))
```

Argparse for `lit merge O A B P` (four positional arguments, matching git's
`%O %A %B %P` substitution).

### 4. Test the exit codes

`tests/test_driver.py`:
- Clean merge (Scenario A inputs) → exit code 0, output file parseable.
- Conflicted merge (Scenario B inputs) → exit code 1, output file contains
  `lit:conflict` marker.

## Done when
- `lit merge O A B P` exits 0 on a clean merge, 1 on conflicts
- The output is always written to the `A` path
- Conflict markers are parseable by the serialiser (round-trip safe)
- Exit code tests pass
