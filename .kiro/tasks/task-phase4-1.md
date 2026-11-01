# task-phase4-1: Migrate `src/` to literate sources under `lit/`

## Status
- [ ] Done

## What this is
The self-hosting milestone. Every `.py` file under `src/` gets a corresponding
literate document under `lit/` that is its source of truth. After this task,
`src/` is generated — nothing in it is authored directly.

This is on the cut list (PLAN.md cut item 1) if the schedule slips. Do not
start it unless Phase 3 is complete and there are at least 5 days left.

## Prerequisite
All of Phase 1–3 complete. The round trip must be lossless and proven. If
`lit stitch` has any known bugs, fix them before migrating.

## How to execute

### 1. Create `lit/` directory and documents

One document per logical module. Suggested split:

| Document | Chunks (target files) |
|---|---|
| `lit/format.md` | `parser.py`, `model.py` |
| `lit/tangle.md` | `tangle.py` |
| `lit/stitch.md` | `stitch.py` |
| `lit/merge.md` | `merge.py`, `driver.py` |
| `lit/install.md` | `install.py` |
| `lit/cli.md` | `cli.py` |
| `lit/resolve.md` | `resolve_server.py` |

### 2. Migration process (per file)

For each `.py` file:
1. Write a `lit/*.md` document with prose describing what the module does and
   why, interspersed with the code chunks.
2. Add the `id=` and `file=` attributes to each chunk fence.
3. Run `lit tangle lit/format.md` and diff the output against the current
   `src/literacode/parser.py`. They must be identical except for the sync
   marker lines.
4. If they match, delete `src/literacode/parser.py` and replace it with the
   tangled output.
5. Run the full test suite. If it passes, commit.

### 3. Add sync markers to the literate documents themselves

The documents in `lit/` are now source of truth. Add a comment near the top
of each document:

```markdown
<!-- generated files: src/literacode/parser.py -->
<!-- do not edit generated files directly -->
```

### 4. Update the pre-commit hook

The `.githooks/pre-commit` hook should verify that `src/` files are
up-to-date with `lit/`. If any generated file is stale (tangle would produce
a different result), the commit is blocked.

```bash
# In .githooks/pre-commit
lit tangle lit/*.md --check
# --check: tangle but don't write, exit 1 if any output differs from disk
```

Add `--check` mode to `lit tangle`.

## Done when
- Every `.py` under `src/` has a corresponding chunk in `lit/`
- `lit tangle lit/*.md` regenerates `src/` exactly
- The full test suite passes on the generated files
- The pre-commit hook blocks a commit where `src/` is out of sync
