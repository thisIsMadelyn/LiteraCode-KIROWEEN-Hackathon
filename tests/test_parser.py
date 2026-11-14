"""
Smoke tests for the parser.
"""
from pathlib import Path

import pytest

from literacode.model import Chunk, Document, Prose
from literacode.parser import parse_document, parse_string

FIXTURE = Path(__file__).parent / "fixtures" / "round_trip.md"


def test_parse_plain_markdown():
    """A file with no chunk attributes parses without error."""
    doc = parse_string("# Hello\n\nJust some prose.\n")
    assert isinstance(doc, Document)
    assert all(isinstance(n, Prose) for n in doc.nodes)


def test_empty_document():
    doc = parse_string("")
    assert doc.nodes == []


def test_chunk_fields():
    md = (
        "Before.\n"
        "\n"
        "```python id=my-chunk file=src/foo.py\n"
        "x = 1\n"
        "```\n"
        "\n"
        "After.\n"
    )
    doc = parse_string(md)
    chunks = doc.chunks()
    assert len(chunks) == 1
    c = chunks[0]
    assert c.id == "my-chunk"
    assert c.file == "src/foo.py"
    assert c.lang == "python"
    assert c.body == "x = 1\n"


def test_plain_fence_is_prose():
    """A fence without id= must not become a Chunk."""
    md = "```python\nx = 1\n```\n"
    doc = parse_string(md)
    assert doc.chunks() == []
    # The whole thing is prose
    assert len(doc.nodes) == 1
    assert isinstance(doc.nodes[0], Prose)
    assert "```python" in doc.nodes[0].text


def test_fixture_parses():
    doc = parse_document(FIXTURE)
    chunks = doc.chunks()
    ids = [c.id for c in chunks]
    assert "greet" in ids
    assert "main" in ids
    assert "type-alias" in ids

    greet = doc.get_chunk("greet")
    assert greet is not None
    assert greet.file == "src/example/hello.py"
    assert "Hello" in greet.body


def test_get_chunk_missing():
    doc = parse_string("# nothing\n")
    assert doc.get_chunk("nope") is None
