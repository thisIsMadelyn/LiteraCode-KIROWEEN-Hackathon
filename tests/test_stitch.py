"""
Tests for lit stitch.
"""
import shutil
from pathlib import Path

import pytest

from literacode.parser import parse_document
from literacode.stitch import stitch, StitchError
from literacode.tangle import tangle

FIXTURE = Path(__file__).parent / "fixtures" / "round_trip.md"


def test_stitch_updates_chunk_body(tmp_path: Path):
    # Copy fixture
    doc_path = tmp_path / "round_trip.md"
    shutil.copy(FIXTURE, doc_path)

    written = tangle(parse_document(doc_path), doc_path, tmp_path)
    py_file = tmp_path / "src" / "example" / "hello.py"
    assert py_file in written

    # Edit the file: append a comment to the greet region
    original = py_file.read_text(encoding="utf-8")
    # Find the greet region and append a comment after its body
    new_content = original.replace(
        '    return f"Hello, {name}!"\n',
        '    return f"Hello, {name}!"\n    # edited\n',
    )
    py_file.write_text(new_content, encoding="utf-8")

    stitch(py_file, doc_path)

    doc = parse_document(doc_path)
    greet = doc.get_chunk("greet")
    assert greet is not None
    assert "# edited" in greet.body


def test_stitch_prose_unchanged(tmp_path: Path):
    doc_path = tmp_path / "round_trip.md"
    shutil.copy(FIXTURE, doc_path)
    original_bytes = doc_path.read_bytes()

    written = tangle(parse_document(doc_path), doc_path, tmp_path)
    # stitch without any edits
    for py_file in written:
        stitch(py_file, doc_path)

    assert doc_path.read_bytes() == original_bytes, (
        "stitch with no edits must not change the document"
    )


def test_stitch_unknown_id_raises(tmp_path: Path):
    doc_path = tmp_path / "round_trip.md"
    shutil.copy(FIXTURE, doc_path)

    written = tangle(parse_document(doc_path), doc_path, tmp_path)
    py_file = tmp_path / "src" / "example" / "hello.py"

    # Inject a fake marker pointing at a nonexistent chunk
    bad_content = (
        f"# lit:chunk id=DOES-NOT-EXIST src={doc_path}\n"
        "fake body\n"
    )
    py_file.write_text(bad_content, encoding="utf-8")

    with pytest.raises(StitchError, match="DOES-NOT-EXIST"):
        stitch(py_file, doc_path)


def test_stitch_no_markers_is_noop(tmp_path: Path):
    doc_path = tmp_path / "round_trip.md"
    shutil.copy(FIXTURE, doc_path)
    original_bytes = doc_path.read_bytes()

    py_file = tmp_path / "plain.py"
    py_file.write_text("x = 1\n", encoding="utf-8")

    stitch(py_file, doc_path)
    assert doc_path.read_bytes() == original_bytes
