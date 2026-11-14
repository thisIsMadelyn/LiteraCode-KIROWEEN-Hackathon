"""
Tests for lit tangle.
"""
import shutil
from pathlib import Path

import pytest

from literacode.parser import parse_string, parse_document
from literacode.tangle import TangleError, render, tangle

FIXTURE = Path(__file__).parent / "fixtures" / "round_trip.md"


def test_tangle_writes_files(tmp_path: Path):
    doc = parse_document(FIXTURE)
    written = tangle(doc, FIXTURE, tmp_path)
    assert len(written) == 1
    out = tmp_path / "src" / "example" / "hello.py"
    assert out in written
    assert out.exists()


def test_tangle_sync_markers(tmp_path: Path):
    doc = parse_document(FIXTURE)
    tangle(doc, FIXTURE, tmp_path)
    content = (tmp_path / "src" / "example" / "hello.py").read_text()
    assert "# lit:chunk id=greet" in content
    assert "# lit:chunk id=main" in content


def test_tangle_no_fence_lines(tmp_path: Path):
    doc = parse_document(FIXTURE)
    tangle(doc, FIXTURE, tmp_path)
    content = (tmp_path / "src" / "example" / "hello.py").read_text()
    assert "```" not in content


def test_tangle_bodies_in_order(tmp_path: Path):
    doc = parse_document(FIXTURE)
    tangle(doc, FIXTURE, tmp_path)
    content = (tmp_path / "src" / "example" / "hello.py").read_text()
    greet_pos = content.index("# lit:chunk id=greet")
    main_pos = content.index("# lit:chunk id=main")
    assert greet_pos < main_pos


def test_tangle_deterministic(tmp_path: Path):
    doc = parse_document(FIXTURE)
    tangle(doc, FIXTURE, tmp_path)
    first = (tmp_path / "src" / "example" / "hello.py").read_bytes()
    tangle(doc, FIXTURE, tmp_path)
    second = (tmp_path / "src" / "example" / "hello.py").read_bytes()
    assert first == second


def test_tangle_no_targets():
    """A document with no file= chunks produces no output."""
    doc = parse_string("```python id=helper\nx = 1\n```\n")
    result = tangle(doc, Path("fake.md"), Path("."))
    assert result == []


def test_tangle_ref_expansion(tmp_path: Path):
    md = (
        "```python id=body file=out.py\n"
        "<<helper>>\n"
        "```\n"
        "```python id=helper\n"
        "x = 42\n"
        "```\n"
    )
    doc = parse_string(md)
    tangle(doc, tmp_path / "fake.md", tmp_path)
    content = (tmp_path / "out.py").read_text()
    assert "x = 42" in content
    assert "<<helper>>" not in content


def test_tangle_circular_ref_raises(tmp_path: Path):
    md = (
        "```python id=a file=out.py\n"
        "<<b>>\n"
        "```\n"
        "```python id=b\n"
        "<<a>>\n"
        "```\n"
    )
    doc = parse_string(md)
    with pytest.raises(TangleError, match="Circular"):
        tangle(doc, tmp_path / "fake.md", tmp_path)


def test_stale_detects_drift_and_clears_after_tangle(tmp_path):
    from literacode.tangle import stale

    doc = parse_document(FIXTURE)
    assert stale(doc, FIXTURE, tmp_path)  # nothing written yet
    tangle(doc, FIXTURE, tmp_path)
    assert stale(doc, FIXTURE, tmp_path) == []
    target = next(iter(render(doc, FIXTURE, tmp_path)))
    target.write_text("# edited\n", encoding="utf-8")
    assert stale(doc, FIXTURE, tmp_path) == [target]
