# lit:chunk id=propose-header src=lit/resolve.md
"""
Conflict-resolver agent call for ``lit resolve``.

Returns a *proposal* only. Nothing here writes to disk; a human accepts it in
the UI and the resolution area is the only path to the document.

Providers, in order: OpenAI (OPENAI_API_KEY), Anthropic (ANTHROPIC_API_KEY).
With no key, or if the call fails, the stub returns the ours body and says so.
Model names come from LIT_OPENAI_MODEL / LIT_ANTHROPIC_MODEL.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

AGENT_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / ".kiro" / "agents" / "conflict-resolver.md"
)
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-5"
TIMEOUT_S = 90


# lit:chunk id=load_system_prompt src=lit/resolve.md
def load_system_prompt(path: Path = AGENT_PROMPT_PATH) -> str:
    """The text under '## System prompt' in the agent definition."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^## System prompt\s*\n(.*)\Z", text, re.S | re.M)
    if not m:
        raise ValueError(f"no '## System prompt' section in {path}")
    return m.group(1).strip()


# lit:chunk id=build_user_message src=lit/resolve.md
def build_user_message(conflict: dict) -> str:
    """The conflict as JSON: id, lang, and base/ours/theirs with prose context."""
    return json.dumps(
        {k: conflict[k] for k in ("chunk_id", "lang", "base", "ours", "theirs")},
        indent=2,
    )


# lit:chunk id=parse_reply src=lit/resolve.md
def parse_reply(text: str) -> dict:
    """
    Split the agent's reply into proposal / reasoning / confidence.

    ``proposal`` is None when the agent declined (body is CONFLICT or missing).
    """
    sections: dict[str, str] = {}
    current = None
    for line in text.splitlines(keepends=True):
        m = re.match(r"##\s+(Proposal|Reasoning|Confidence)\s*$", line.strip())
        if m:
            current = m.group(1).lower()
            sections[current] = ""
        elif current:
            sections[current] += line

    body = sections.get("proposal", "").strip("\n")
    fence = re.fullmatch(r"```[^\n]*\n(.*?)\n?```\s*", body, re.S)
    if fence:
        body = fence.group(1)
    proposal = None
    if body.strip() and body.strip().upper() != "CONFLICT":
        proposal = body if body.endswith("\n") else body + "\n"
    return {
        "proposal": proposal,
        "reasoning": sections.get("reasoning", "").strip() or text.strip(),
        "confidence": sections.get("confidence", "").strip(),
    }


# lit:chunk id=_post_json src=lit/resolve.md
def _post_json(url: str, headers: dict, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
        return json.load(r)


# lit:chunk id=_call_openai src=lit/resolve.md
def _call_openai(system: str, user: str, key: str) -> str:
    out = _post_json(
        "https://api.openai.com/v1/chat/completions",
        {"Authorization": f"Bearer {key}"},
        {
            "model": os.environ.get("LIT_OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
    )
    return out["choices"][0]["message"]["content"]


# lit:chunk id=_call_anthropic src=lit/resolve.md
def _call_anthropic(system: str, user: str, key: str) -> str:
    out = _post_json(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": key, "anthropic-version": "2023-06-01"},
        {
            "model": os.environ.get("LIT_ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL),
            "max_tokens": 4096,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
    )
    return "".join(b.get("text", "") for b in out["content"])


# lit:chunk id=propose_stub src=lit/resolve.md
def propose_stub(conflict: dict, note: str) -> dict:
    """Offline fallback: propose the ours body unchanged."""
    return {
        "proposal": conflict["ours"]["body"],
        "reasoning": note,
        "confidence": "",
        "source": "stub",
    }


# lit:chunk id=propose src=lit/resolve.md
def propose(conflict: dict) -> dict:
    """
    Ask the agent to resolve one conflict (an entry from load_conflicts()).

    Returns {proposal, reasoning, confidence, source}. ``proposal`` is None if
    the agent says it cannot resolve the conflict.
    """
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not (openai_key or anthropic_key):
        return propose_stub(
            conflict,
            "No OPENAI_API_KEY or ANTHROPIC_API_KEY set. "
            "This is the ours body, not an agent proposal.",
        )
    try:
        system = load_system_prompt()
        user = build_user_message(conflict)
        if openai_key:
            source, reply = "openai", _call_openai(system, user, openai_key)
        else:
            source, reply = "anthropic", _call_anthropic(system, user, anthropic_key)
    except (OSError, ValueError, KeyError, IndexError, urllib.error.URLError) as e:
        return propose_stub(
            conflict, f"Agent call failed ({type(e).__name__}: {e}). Showing ours."
        )
    return {**parse_reply(reply), "source": source}
