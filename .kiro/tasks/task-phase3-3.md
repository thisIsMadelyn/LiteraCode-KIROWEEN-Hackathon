# task-phase3-3: Conflict-resolver agent wired in, output is a reviewable diff

## Status
- [ ] Done

## What this is
The agent from `.kiro/agents/conflict-resolver.md` is called from the Python
server. It receives the base/ours/theirs bodies plus the surrounding prose and
returns a proposed merged body. That proposal appears in the UI as a diff the
human can accept, reject, or hand-edit. The agent never writes to disk.

## Prerequisite
task-phase3-2 (the three-way view) must be done. The agent wires into the
existing review flow — it does not replace it.

## How to execute

### 1. Agent call from the server

Add a `/api/propose` endpoint:

```python
# POST /api/propose
# Body: { chunk_id, base, ours, theirs, prose_before, prose_after }
# Returns: { proposal: "<merged body or CONFLICT>" }
```

The server calls the conflict-resolver agent (via an LLM API). The call is
synchronous from the UI's perspective (show a spinner).

For the LLM call, use the prompt from `.kiro/agents/conflict-resolver.md`
as the system prompt. The input JSON is the user message.

Supported providers (in preference order):
- OpenAI (`OPENAI_API_KEY`)
- Anthropic (`ANTHROPIC_API_KEY`)
- Fall through to a stub that returns the `ours` body if no key is set

This means the UI works without an API key — the proposal is just `ours`.

### 2. Show the proposal as a diff

When the user clicks "Get proposal", the UI:
1. POSTs to `/api/propose`
2. Receives the proposal body
3. Computes a line diff between `ours` body and the proposal
4. Renders the diff (green = added, red = removed) below the three-column view
5. Offers three buttons: **Accept** (copy proposal to the resolution area),
   **Reject** (clear the proposal), **Edit** (copy proposal to resolution area
   and focus it for editing)

If the agent returns `CONFLICT`, show a message: "The agent cannot resolve
this conflict. Please resolve manually."

### 3. Non-negotiable

The agent proposal is never automatically accepted. The Accept button is the
only way it reaches the resolution area. The resolution area is the only way
it reaches disk. This is a hard rule from the product spec.

### 4. Stub for offline / no-key use

```python
def propose_stub(base, ours, theirs, prose_before, prose_after):
    # Returns ours as-is — at least the UI flow works
    return ours
```

## Done when
- "Get proposal" button calls the agent (or stub) and shows a diff
- Accept/Reject/Edit buttons work as described
- The agent never writes to disk without user action
- The UI flow works with no API key (stub mode)
