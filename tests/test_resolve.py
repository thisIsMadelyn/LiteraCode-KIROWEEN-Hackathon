"""Smoke tests for the lit resolve server (file-only mode, outside a merge)."""
import json
import threading
import urllib.request

from literacode.resolve import load_conflicts, make_server

CONFLICTED = """\
Intro.

```python id=a file=a.py lit:conflict
<<<<<<< ours
x = 3
=======
x = 2
>>>>>>> theirs
```

Outro.
"""


def test_load_conflicts_from_markers(tmp_path):
    doc = tmp_path / "d.md"
    doc.write_text(CONFLICTED, encoding="utf-8")
    (c,) = load_conflicts(doc)
    assert c["chunk_id"] == "a"
    assert c["ours"]["body"] == "x = 3\n"
    assert c["theirs"]["body"] == "x = 2\n"
    assert c["ours"]["prose_before"] == "Intro.\n\n"


def test_server_serves_page_and_conflicts(tmp_path):
    doc = tmp_path / "d.md"
    doc.write_text(CONFLICTED, encoding="utf-8")
    server = make_server(doc, 0, static_root=tmp_path / "nodist")
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as r:
            assert r.status == 200
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/conflicts", data=b"", method="POST"
        )
        with urllib.request.urlopen(req) as r:
            assert [c["chunk_id"] for c in json.load(r)] == ["a"]
    finally:
        server.shutdown()
        server.server_close()


# ---------------------------------------------------------------------------
# /api/resolve
# ---------------------------------------------------------------------------

import urllib.error

import pytest

from literacode.parser import parse_document
from literacode.resolve import ResolveError, file_hash, resolve_chunk


def test_resolve_chunk_writes_body_and_clears_marker(tmp_path):
    doc = tmp_path / "d.md"
    doc.write_text(CONFLICTED, encoding="utf-8", newline="")
    out = resolve_chunk(doc, "a", "x = 5", file_hash(doc))
    assert (out["remaining"], out["prose_conflicts"]) == (0, 0)
    assert doc.read_text(encoding="utf-8") == (
        "Intro.\n\n```python id=a file=a.py\nx = 5\n```\n\nOutro.\n"
    )
    assert parse_document(doc).get_chunk("a").body == "x = 5\n"
    assert not list(tmp_path.glob("*.lit_resolved"))


@pytest.mark.parametrize("chunk_id,body,status", [
    ("nope", "x = 1", 404),
    ("a", "   \n", 400),
    ("a", "<<<<<<< ours\nx\n=======\ny\n>>>>>>> theirs\n", 400),
])
def test_resolve_chunk_refuses_bad_input(tmp_path, chunk_id, body, status):
    doc = tmp_path / "d.md"
    doc.write_text(CONFLICTED, encoding="utf-8", newline="")
    with pytest.raises(ResolveError) as e:
        resolve_chunk(doc, chunk_id, body, file_hash(doc))
    assert e.value.status == status
    assert doc.read_text(encoding="utf-8") == CONFLICTED


def test_resolve_chunk_409_when_file_changed(tmp_path):
    doc = tmp_path / "d.md"
    doc.write_text(CONFLICTED, encoding="utf-8", newline="")
    h = file_hash(doc)
    doc.write_text(CONFLICTED + "edited\n", encoding="utf-8", newline="")
    with pytest.raises(ResolveError) as e:
        resolve_chunk(doc, "a", "x = 1", h)
    assert e.value.status == 409


def test_resolve_endpoint_and_shutdown(tmp_path):
    doc = tmp_path / "d.md"
    doc.write_text(CONFLICTED, encoding="utf-8", newline="")
    server = make_server(doc, 0, static_root=tmp_path)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/resolve", method="POST",
        data=json.dumps({"chunk_id": "a", "body": "x = 4\n"}).encode(),
    )
    with urllib.request.urlopen(req) as r:
        assert json.load(r) == {"remaining": 0, "prose_conflicts": 0}
    # second attempt: the chunk is no longer conflicted
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req)
    assert e.value.code == 404
    t.join(timeout=8)  # server shuts itself down about 3 s after the last conflict
    assert not t.is_alive()
    server.server_close()
