"""Tests for the conflict-resolver agent call (no network)."""
import json
import threading
import urllib.error
import urllib.request

from literacode import propose as P
from literacode.resolve import make_server
from tests.test_resolve import CONFLICTED

REPLY = """## Proposal
```python
x = 5
```

## Reasoning
Both sides.

## Confidence
high
"""


def test_system_prompt_loads_from_agent_file():
    prompt = P.load_system_prompt()
    assert prompt.startswith("You resolve a merge conflict")
    assert "## Proposal" in prompt


def test_parse_reply_strips_fence_and_splits_sections():
    r = P.parse_reply(REPLY)
    assert r["proposal"] == "x = 5\n"
    assert r["reasoning"] == "Both sides."
    assert r["confidence"] == "high"


def test_parse_reply_conflict_means_no_proposal():
    r = P.parse_reply("## Proposal\nCONFLICT\n\n## Reasoning\nIncompatible.\n")
    assert r["proposal"] is None
    assert r["reasoning"] == "Incompatible."


def _conflict():
    return {"chunk_id": "a", "lang": "python",
            "base": {"body": "x = 1\n"}, "ours": {"body": "x = 3\n"},
            "theirs": {"body": "x = 2\n"}}


def test_no_key_returns_ours_stub(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = P.propose(_conflict())
    assert (r["source"], r["proposal"]) == ("stub", "x = 3\n")


def test_provider_failure_falls_back_to_stub_with_reason(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    def boom(*a):
        raise urllib.error.URLError("offline")
    monkeypatch.setattr(P, "_call_openai", boom)
    r = P.propose(_conflict())
    assert r["source"] == "stub" and "offline" in r["reasoning"]


def test_openai_reply_is_parsed(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setattr(P, "_call_openai", lambda *a: REPLY)
    r = P.propose(_conflict())
    assert (r["source"], r["proposal"]) == ("openai", "x = 5\n")


def test_propose_endpoint_does_not_touch_document(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    doc = tmp_path / "d.md"
    doc.write_text(CONFLICTED, encoding="utf-8")
    server = make_server(doc, 0, static_root=tmp_path)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        def post(payload):
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/propose",
                data=json.dumps(payload).encode(), method="POST")
            return urllib.request.urlopen(req)
        assert json.load(post({"chunk_id": "a"}))["proposal"] == "x = 3\n"
        try:
            post({"chunk_id": "nope"})
            assert False, "expected 404"
        except urllib.error.HTTPError as e:
            assert e.code == 404
    finally:
        server.shutdown()
        server.server_close()
    assert doc.read_text(encoding="utf-8") == CONFLICTED
