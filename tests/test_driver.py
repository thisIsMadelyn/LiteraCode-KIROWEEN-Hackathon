"""
Tests for the merge driver (exit codes, conflict marker format, file output).
"""
import shutil
from pathlib import Path

import pytest

from literacode.driver import merge_driver
from literacode.model import Chunk
from literacode.parser import parse_document, parse_string


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SCENARIO_A_BASE = """\
# Scenario A

The parser comes first.

```python id=parse file=src/demo/main.py
def parse(text):
    return text.split()
```

Then we validate.

```python id=validate file=src/demo/main.py
def validate(tokens):
    return [t for t in tokens if t.isalpha()]
```

Finally we format.

```python id=fmt file=src/demo/main.py
def fmt(tokens):
    return ", ".join(tokens)
```
"""

SCENARIO_A_OURS = """\
# Scenario A

Then we validate.

```python id=validate file=src/demo/main.py
def validate(tokens):
    return [t for t in tokens if t.isalpha()]
```

The parser comes second now.

```python id=parse file=src/demo/main.py
def parse(text):
    return text.split()
```

Finally we format.

```python id=fmt file=src/demo/main.py
def fmt(tokens):
    return ", ".join(tokens)
```
"""

SCENARIO_A_THEIRS = """\
# Scenario A

The parser comes first.

```python id=parse file=src/demo/main.py
def parse(text):
    return [t.strip('.,') for t in text.split()]
```

Then we validate.

```python id=validate file=src/demo/main.py
def validate(tokens):
    return [t for t in tokens if t.isalpha()]
```

Finally we format.

```python id=fmt file=src/demo/main.py
def fmt(tokens):
    return ", ".join(tokens)
```
"""


# ---------------------------------------------------------------------------
# File-level driver tests
# ---------------------------------------------------------------------------

def test_driver_clean_merge_exit_0(tmp_path: Path):
    base_file   = tmp_path / "base.md"
    ours_file   = tmp_path / "ours.md"
    theirs_file = tmp_path / "theirs.md"

    base_file.write_text(SCENARIO_A_BASE, encoding="utf-8", newline="")
    ours_file.write_text(SCENARIO_A_OURS, encoding="utf-8", newline="")
    theirs_file.write_text(SCENARIO_A_THEIRS, encoding="utf-8", newline="")

    rc = merge_driver(base_file, ours_file, theirs_file, "scenario_a.md")
    assert rc == 0


def test_driver_clean_merge_writes_ours(tmp_path: Path):
    base_file   = tmp_path / "base.md"
    ours_file   = tmp_path / "ours.md"
    theirs_file = tmp_path / "theirs.md"

    base_file.write_text(SCENARIO_A_BASE, encoding="utf-8", newline="")
    ours_file.write_text(SCENARIO_A_OURS, encoding="utf-8", newline="")
    theirs_file.write_text(SCENARIO_A_THEIRS, encoding="utf-8", newline="")

    merge_driver(base_file, ours_file, theirs_file, "scenario_a.md")

    result_doc = parse_document(ours_file)
    # Order follows ours: [validate, parse, fmt]
    chunk_ids = [n.id for n in result_doc.nodes if isinstance(n, Chunk)]
    assert chunk_ids == ["validate", "parse", "fmt"]
    # parse body is theirs' edit
    assert "strip" in result_doc.get_chunk("parse").body


def test_driver_conflict_exit_1(tmp_path: Path):
    base_md = "```python id=A file=out.py\nx = 0\n```\n"
    ours_md = "```python id=A file=out.py\nx = 1  # ours\n```\n"
    theirs_md = "```python id=A file=out.py\nx = 2  # theirs\n```\n"

    base_file   = tmp_path / "base.md"
    ours_file   = tmp_path / "ours.md"
    theirs_file = tmp_path / "theirs.md"

    base_file.write_text(base_md, encoding="utf-8", newline="")
    ours_file.write_text(ours_md, encoding="utf-8", newline="")
    theirs_file.write_text(theirs_md, encoding="utf-8", newline="")

    rc = merge_driver(base_file, ours_file, theirs_file, "test.md")
    assert rc == 1


def test_driver_conflict_embeds_markers(tmp_path: Path):
    base_md = "```python id=A file=out.py\nx = 0\n```\n"
    ours_md = "```python id=A file=out.py\nx = 1  # ours\n```\n"
    theirs_md = "```python id=A file=out.py\nx = 2  # theirs\n```\n"

    base_file   = tmp_path / "base.md"
    ours_file   = tmp_path / "ours.md"
    theirs_file = tmp_path / "theirs.md"

    base_file.write_text(base_md, encoding="utf-8", newline="")
    ours_file.write_text(ours_md, encoding="utf-8", newline="")
    theirs_file.write_text(theirs_md, encoding="utf-8", newline="")

    merge_driver(base_file, ours_file, theirs_file, "test.md")

    result_text = ours_file.read_text(encoding="utf-8")
    assert "<<<<<<< ours" in result_text
    assert "=======" in result_text
    assert ">>>>>>> theirs" in result_text
    assert "lit:conflict" in result_text


def test_driver_output_parseable_after_conflict(tmp_path: Path):
    """Even a conflicted merge must produce a parseable document."""
    base_md = "```python id=A file=out.py\nx = 0\n```\n"
    ours_md = "```python id=A file=out.py\nx = 1  # ours\n```\n"
    theirs_md = "```python id=A file=out.py\nx = 2  # theirs\n```\n"

    base_file   = tmp_path / "base.md"
    ours_file   = tmp_path / "ours.md"
    theirs_file = tmp_path / "theirs.md"

    base_file.write_text(base_md, encoding="utf-8", newline="")
    ours_file.write_text(ours_md, encoding="utf-8", newline="")
    theirs_file.write_text(theirs_md, encoding="utf-8", newline="")

    merge_driver(base_file, ours_file, theirs_file, "test.md")

    # Must not raise
    result_doc = parse_document(ours_file)
    assert result_doc is not None
