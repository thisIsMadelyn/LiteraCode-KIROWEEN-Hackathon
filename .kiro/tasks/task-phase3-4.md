# task-phase3-4: Accept / reject / hand-edit, writes the resolution

## Status
- [ ] Done

## What this is
The final step of the resolve flow. When the human is satisfied with the
resolution in the text area (whether typed, accepted from agent, or edited),
they click "Resolve". The server writes that body into the document, clears
the conflict marker, and the UI moves to the next conflict. When all conflicts
are resolved, the server exits and tells the user to `git add` the file.

## Prerequisite
task-phase3-3 must be done. The resolution area must be populated before this
step has anything to write.

## How to execute

### 1. `/api/resolve` endpoint

```python
# POST /api/resolve
# Body: { chunk_id: str, body: str }
# Returns: { remaining: int }  ← number of unresolved conflicts left
```

Server logic:
1. Parse the document.
2. Find the chunk with `id == chunk_id` and `lit:conflict` in its attributes.
3. Replace the body with the submitted body.
4. Remove the `lit:conflict` attribute from the fence.
5. Write the document back to disk.
6. Return the count of remaining `lit:conflict` chunks.

### 2. "All done" state

When `remaining == 0`:
- The server sends a final message: "All conflicts resolved."
- The UI shows: "All conflicts resolved. Run `git add <file>` to stage the result."
- The server calls `server.shutdown()` after a short delay (e.g. 3 seconds).

The user should not need to manually kill the process.

### 3. UI flow

```
[Conflict view] → user edits resolution area
  → clicks "Resolve"
  → POST /api/resolve
  → if remaining > 0: load next conflict
  → if remaining == 0: show "all done" screen, server shuts down
```

The "Resolve" button is disabled if the resolution text area is empty.

### 4. Safety

- Never write if `chunk_id` is not found in the document.
- Never write if the document has changed on disk since the server loaded it
  (check mtime or a hash). If it has, return a 409 and tell the user to
  restart `lit resolve`.
- Do not remove the backup of the original — write to a `.lit_resolved` temp
  file first, then rename atomically.

## Done when
- Clicking "Resolve" updates the document on disk and clears the conflict marker
- All-done state shuts the server down gracefully
- The resolved document is valid (parseable, no remaining `lit:conflict` markers)
- Phase 3 gate (Scenario B end to end) is verified manually
