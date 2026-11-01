# task-phase1-4: Losslessness test — tangle → edit → stitch → tangle is a fixed point

## Status
- [ ] Done

## What this is
The Phase 1 gate. A single automated test that proves the round trip is lossless
on a non-trivial document. "Non-trivial" means: multiple chunks, multiple prose
sections, at least one chunk with a multi-line body, and at least one chunk
reference (`<<id>>`).

If this test does not pass, nothing in Phase 2 is valid.

## Prerequisite
tasks phase1-1, phase1-2, and phase1-3 must all be done.

## How to execute

### 1. Create the fixture document

`tests/fixtures/round_trip.md` — a realistic-looking literate document, e.g.:

````markdown
# A simple greeter

This module says hello.

```python id=greet file=src/example/hello.py
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

The main entry point calls the greeter.

```python id=main file=src/example/hello.py
if __name__ == "__main__":
    print(greet("world"))
```
````

### 2. Write the fixed-point test

`tests/test_round_trip.py`:

```python
import shutil
from pathlib import Path
import pytest
from literacode.parser import parse_document
from literacode.tangle import tangle
from literacode.stitch import stitch

FIXTURE = Path("tests/fixtures/round_trip.md")

def test_fixed_point(tmp_path):
    # Copy fixture so we can mutate
    doc = tmp_path / "round_trip.md"
    shutil.copy(FIXTURE, doc)

    # Step 1: tangle
    written = tangle(parse_document(doc), doc, tmp_path)
    assert written, "tangle produced no files"

    # Step 2: simulate an edit — append a comment to one chunk body
    py_file = written[0]
    original = py_file.read_text()
    py_file.write_text(original + "\n# edited\n")

    # Step 3: stitch back
    stitch(py_file, doc)

    # Step 4: re-tangle
    written2 = tangle(parse_document(doc), doc, tmp_path)

    # Step 5: the re-tangled file must contain the edit
    result = written2[0].read_text()
    assert "# edited" in result

def test_no_change_is_noop(tmp_path):
    doc = tmp_path / "round_trip.md"
    shutil.copy(FIXTURE, doc)
    original_doc = doc.read_bytes()

    written = tangle(parse_document(doc), doc, tmp_path)
    # stitch without any edits
    for f in written:
        stitch(f, doc)

    assert doc.read_bytes() == original_doc, "stitch with no edits must not change the document"
```

### 3. Run and fix until green

```bash
pytest tests/test_round_trip.py -v
```

Any failure here points to a bug in the serialiser (most likely), the marker
format, or the stitch region-splitting logic. Fix the root cause — do not
patch the test.

### 4. Gate check

Run the full test suite:
```bash
pytest
```

All tests must pass. Then update PLAN.md Phase 1 checkboxes and the session log.

## Done when
- `test_fixed_point` passes
- `test_no_change_is_noop` passes
- Full `pytest` run is green
- PLAN.md Phase 1 gate note is updated
