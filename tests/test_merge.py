"""
Tests for the three-way merge logic.

Scenario A: one side reorders chunks; the other edits a chunk body.
            Result: reordered order + edited body, zero conflicts.

Scenario B: both sides edit the same chunk differently.
            Result: one Conflict.
"""
from pathlib import Path

import pytest

from literacode.merge import three_way_merge, Conflict
from literacode.model import Document, Chunk, Prose
from literacode.parser import parse_string


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc(*chunks: tuple[str, str, str | None]) -> Document:
    """
    Build a simple Document with only Chunk nodes (no prose between them).
    Each tuple is (id, body, file).  file=None means no tangle target.
    """
    nodes = []
    for cid, body, file in chunks:
        nodes.append(Chunk(
            id=cid,
            file=file,
            lang="python",
            body=body,
            _fence_attrs=f" id={cid}" + (f" file={file}" if file else ""),
        ))
    return Document(nodes=nodes)


# ---------------------------------------------------------------------------
# Scenario A
# ---------------------------------------------------------------------------

class TestScenarioA:
    """
    base:   [parse, validate, fmt]   — original order
    ours:   [validate, parse, fmt]   — reordered (validate first)
    theirs: [parse, validate, fmt]   — same order as base, but parse body edited
    """

    BASE_PARSE_BODY = "def parse(text):\n    return text.split()\n"
    THEIRS_PARSE_BODY = "def parse(text):\n    return [t.strip('.,') for t in text.split()]\n"
    VALIDATE_BODY = "def validate(tokens):\n    return [t for t in tokens if t.isalpha()]\n"
    FMT_BODY = "def fmt(tokens):\n    return ', '.join(tokens)\n"

    def _make_docs(self):
        base = _doc(
            ("parse",    self.BASE_PARSE_BODY,   "src/demo/main.py"),
            ("validate", self.VALIDATE_BODY,     "src/demo/main.py"),
            ("fmt",      self.FMT_BODY,          "src/demo/main.py"),
        )
        ours = _doc(
            ("validate", self.VALIDATE_BODY,     "src/demo/main.py"),
            ("parse",    self.BASE_PARSE_BODY,   "src/demo/main.py"),
            ("fmt",      self.FMT_BODY,          "src/demo/main.py"),
        )
        theirs = _doc(
            ("parse",    self.THEIRS_PARSE_BODY, "src/demo/main.py"),
            ("validate", self.VALIDATE_BODY,     "src/demo/main.py"),
            ("fmt",      self.FMT_BODY,          "src/demo/main.py"),
        )
        return base, ours, theirs

    def test_clean_merge(self):
        base, ours, theirs = self._make_docs()
        result = three_way_merge(base, ours, theirs)
        assert result.is_clean, f"Expected clean merge, got conflicts: {result.conflicts}"

    def test_order_follows_ours(self):
        base, ours, theirs = self._make_docs()
        result = three_way_merge(base, ours, theirs)
        chunk_ids = [n.id for n in result.document.nodes if isinstance(n, Chunk)]
        assert chunk_ids == ["validate", "parse", "fmt"], (
            f"Expected ours order [validate, parse, fmt], got {chunk_ids}"
        )

    def test_body_from_theirs(self):
        base, ours, theirs = self._make_docs()
        result = three_way_merge(base, ours, theirs)
        parse_chunk = result.document.get_chunk("parse")
        assert parse_chunk is not None
        assert parse_chunk.body == self.THEIRS_PARSE_BODY, (
            "parse body should be theirs' edited version"
        )

    def test_unedited_chunks_unchanged(self):
        base, ours, theirs = self._make_docs()
        result = three_way_merge(base, ours, theirs)
        validate_chunk = result.document.get_chunk("validate")
        fmt_chunk = result.document.get_chunk("fmt")
        assert validate_chunk.body == self.VALIDATE_BODY
        assert fmt_chunk.body == self.FMT_BODY


# ---------------------------------------------------------------------------
# Scenario B
# ---------------------------------------------------------------------------

class TestScenarioB:
    """
    base:   chunk A with body_base
    ours:   chunk A with body_ours  (different from base)
    theirs: chunk A with body_theirs (also different, not equal to ours)
    """

    BASE_BODY   = "x = 0\n"
    OURS_BODY   = "x = 1  # ours edit\n"
    THEIRS_BODY = "x = 2  # theirs edit\n"

    def _make_docs(self):
        base   = _doc(("A", self.BASE_BODY,   "out.py"))
        ours   = _doc(("A", self.OURS_BODY,   "out.py"))
        theirs = _doc(("A", self.THEIRS_BODY, "out.py"))
        return base, ours, theirs

    def test_produces_conflict(self):
        base, ours, theirs = self._make_docs()
        result = three_way_merge(base, ours, theirs)
        assert not result.is_clean
        assert len(result.conflicts) == 1

    def test_conflict_fields(self):
        base, ours, theirs = self._make_docs()
        result = three_way_merge(base, ours, theirs)
        c = result.conflicts[0]
        assert c.chunk_id == "A"
        assert c.base_body == self.BASE_BODY
        assert c.ours_body == self.OURS_BODY
        assert c.theirs_body == self.THEIRS_BODY


# ---------------------------------------------------------------------------
# Additional cases
# ---------------------------------------------------------------------------

def test_identical_edits_clean():
    """Both sides make the same edit — no conflict."""
    base   = _doc(("A", "x = 0\n", None))
    ours   = _doc(("A", "x = 1\n", None))
    theirs = _doc(("A", "x = 1\n", None))
    result = three_way_merge(base, ours, theirs)
    assert result.is_clean
    assert result.document.get_chunk("A").body == "x = 1\n"


def test_delete_both_sides():
    """Chunk deleted on both sides — gone from result, no conflict."""
    base   = _doc(("A", "x = 0\n", None), ("B", "y = 1\n", None))
    ours   = _doc(("B", "y = 1\n", None))        # A deleted
    theirs = _doc(("B", "y = 1\n", None))        # A deleted
    result = three_way_merge(base, ours, theirs)
    assert result.is_clean
    assert result.document.get_chunk("A") is None
    assert result.document.get_chunk("B") is not None


def test_new_chunk_from_theirs():
    """A chunk added only in theirs appears in the merged result."""
    base   = _doc(("A", "x = 0\n", None))
    ours   = _doc(("A", "x = 0\n", None))
    theirs = _doc(("A", "x = 0\n", None), ("B", "y = 1\n", None))
    result = three_way_merge(base, ours, theirs)
    assert result.is_clean
    assert result.document.get_chunk("B") is not None


def test_unchanged_is_noop():
    """All three versions identical — no changes, no conflicts."""
    md = "```python id=A\nx = 0\n```\n"
    base = ours = theirs = parse_string(md)
    result = three_way_merge(base, ours, theirs)
    assert result.is_clean
    assert result.document.get_chunk("A").body == "x = 0\n"


def test_demo_fixture(tmp_path: Path):
    """The scenario_a.md fixture merges cleanly (all nodes same in base/ours/theirs)."""
    from literacode.parser import parse_document
    fixture = Path(__file__).parent / "demo" / "scenario_a.md"
    doc = parse_document(fixture)
    result = three_way_merge(doc, doc, doc)
    assert result.is_clean


# ---------------------------------------------------------------------------
# Prose slots
# ---------------------------------------------------------------------------

def _pdoc(text: str) -> Document:
    return parse_string(text)


_FENCE = "```python id=a file=a.py\nx = 1\n```\n"


def test_theirs_only_prose_edit_is_kept():
    base = _pdoc("Intro.\n\n" + _FENCE)
    ours = _pdoc("Intro.\n\n" + _FENCE)
    theirs = _pdoc("Intro, rewritten.\n\n" + _FENCE)
    result = three_way_merge(base, ours, theirs)
    assert result.is_clean
    assert result.document.nodes[0].text == "Intro, rewritten.\n\n"


def test_ours_only_prose_edit_is_kept():
    base = _pdoc("Intro.\n\n" + _FENCE)
    ours = _pdoc("Mine.\n\n" + _FENCE)
    theirs = _pdoc("Intro.\n\n" + _FENCE)
    result = three_way_merge(base, ours, theirs)
    assert result.is_clean
    assert result.document.nodes[0].text == "Mine.\n\n"


def test_both_sides_edit_prose_conflicts_with_markers():
    base = _pdoc("Intro.\n\n" + _FENCE)
    ours = _pdoc("Mine.\n\n" + _FENCE)
    theirs = _pdoc("Theirs.\n\n" + _FENCE)
    result = three_way_merge(base, ours, theirs)
    assert [(c.kind, c.chunk_id) for c in result.conflicts] == [("prose", "a")]
    text = result.document.nodes[0].text
    assert "<<<<<<< ours\nMine.\n" in text and "Theirs." in text
