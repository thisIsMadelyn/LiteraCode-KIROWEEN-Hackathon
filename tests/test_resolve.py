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
