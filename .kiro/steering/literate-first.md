---
inclusion: always
---

# Literate-first rule

literacode is written in literacode. This is the project's own proof, and it is
not optional.

## The rule

**Every `.py` file under `src/` is generated.** It is tangled from a chunk in a
literate document under `lit/`. Nothing under `src/` is authored directly.

Before editing any `src/**/*.py`:

1. Find the chunk it came from. The sync marker comment at the top of each
   generated region names the document and the chunk id.
2. Decide which side to edit:
   - **Prose, structure, or a new chunk** → edit the document in `lit/`, then `lit tangle`.
   - **A code body you are already looking at in the IDE** → edit the `.py`, then `lit stitch`.
3. Never hand-edit a sync marker. They are the tool's bookkeeping.

## Bootstrap exception

Until `tangle` and `stitch` both work end to end, `src/` is authored directly.
This exception ends the moment the round trip passes its tests, and the migration
to literate sources is a planned task, not an afterthought.

State which mode you are in when it matters. Do not silently assume the exception
still applies.

## Why

A tool that cannot build itself has not been tested. Every defect in the tangler
costs this project directly, which is the point.
