"""
Phase 1 gate: losslessness test.

tangle → edit → stitch → tangle must be a fixed point.
"""
import shutil
from pathlib import Path

from literacode.parser import parse_document
from literacode.stitch import stitch
from literacode.tangle import tangle

FIXTURE = Path(__file__).parent / "fixtures" / "round_trip.md"


def test_fixed_point(tmp_path: Path):
    # Copy fixture so we can mutate
    doc_path = tmp_path / "round_trip.md"
    shutil.copy(FIXTURE, doc_path)

    # Step 1: tangle
    written = tangle(parse_document(doc_path), doc_path, tmp_path)
    assert written, "tangle produced no files"

    py_file = tmp_path / "src" / "example" / "hello.py"
    assert py_file.exists()

    # Step 2: simulate an edit — append a comment to the chunk body
    original = py_file.read_text(encoding="utf-8")
    py_file.write_text(original + "# edited\n", encoding="utf-8")

    # Step 3: stitch back
    stitch(py_file, doc_path)

    # Step 4: re-tangle
    written2 = tangle(parse_document(doc_path), doc_path, tmp_path)

    # Step 5: the re-tangled file must contain the edit
    result = (tmp_path / "src" / "example" / "hello.py").read_text(encoding="utf-8")
    assert "# edited" in result


def test_no_change_is_noop(tmp_path: Path):
    doc_path = tmp_path / "round_trip.md"
    shutil.copy(FIXTURE, doc_path)
    original_doc = doc_path.read_bytes()

    written = tangle(parse_document(doc_path), doc_path, tmp_path)
    # stitch without any edits
    for f in written:
        stitch(f, doc_path)

    assert doc_path.read_bytes() == original_doc, (
        "stitch with no edits must not change the document"
    )


def test_serialiser_round_trip(tmp_path: Path):
    """parse → serialise must be byte-for-byte identity."""
    from literacode.serialiser import serialise

    doc_path = tmp_path / "round_trip.md"
    shutil.copy(FIXTURE, doc_path)
    original = doc_path.read_text(encoding="utf-8")

    doc = parse_document(doc_path)
    result = serialise(doc)

    assert result == original, (
        "serialise(parse(doc)) must equal the original document verbatim"
    )
