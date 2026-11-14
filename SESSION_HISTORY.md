# Session History

A running log of every Claude Code session on this repository. This file is
public — keep entries factual and free of secrets, keys, or internal-only detail.

Each session is logged as it ends. Sessions are listed newest first.

## Format

```
## Session [YYYY-MM-DD-HHMM]

- **Start status:** <commit, tree state, active phases, and what was open>
- **End status:** <commit, tree state, what closed, what stayed open and why>
- **Badges:**
  - 🆕 Addition — <short description> (`<sha>`)
  - 🐛 Bug fix — <short description> (`<sha>`)
  - <plain bullet for a change that is neither: a move, a rename, a
    deletion, a config change, a PLAN tick> (`<sha>`)
```

Badge legend: 🆕 Addition (new capability, file, or feature) · 🐛 Bug fix
(corrects a defect in existing work). A session may carry zero, one, or several
badges of either kind. Changes that are neither get a plain bullet.

**Rules**
- Append only. Never edit or delete a past entry.
- Reference commits by short SHA, in parentheses, after the claim.
- Say what stayed open and why, not only what closed.
- No keys, no paths that are not already public in the repo, no internal-only
  detail.

## Session [2026-11-14-1200]

- **Start status:** branch `simplify-core` at `39d89b1`, 37/37 tests green, not merged to `main`
- **End status:** `main` at `47d019b`, 57/57 tests green, Phases 1 to 4 built, Phase 3 gate pending a browser pass, Phase 5 not started
- **Badges:**
  - simplify-core merged to `main` (merge commit)
  - 🐛 Bug fix — theirs-side prose edits were dropped by the merge; prose now merges per slot (the prose before each chunk), and edits on both sides conflict with git-style markers (`00d9089`)
  - 🆕 Addition — `src/literacode/resolve.py`: `lit resolve [file] [--port N]` serves `ui/dist` and `/api/conflicts` with base/ours/theirs bodies and surrounding prose, read from git index stages 1-3 (`9516c6b`)
  - 🆕 Addition — `tests/test_resolve.py` and three prose-merge tests (`9516c6b`)
  - 🆕 Addition — `ui/`: Vite + React app with base/ours/theirs columns, prose context, changed-line highlighting, editable resolution area, prev/next and jump navigation; checked in a headless browser at 1280px
  - 🆕 Addition — `src/literacode/propose.py` and `POST /api/propose`: runs the conflict-resolver agent prompt through OpenAI or Anthropic (stdlib HTTP), falls back to an ours-body stub with a visible note; UI shows the proposal as a diff against Ours with Accept / Edit / Reject. The endpoint never writes the document. 7 new tests with the provider mocked
  - 🆕 Addition — `POST /api/resolve` and the Resolve button: writes the chosen body, drops `lit:conflict` from the fence, replaces the file atomically via a `.lit_resolved` temp file, answers 409 if the file changed since the server started, refuses empty bodies and bodies that still hold conflict markers, stops the server 3 s after the last conflict, and the UI then shows `git add <file>`. 6 new tests. Scenario B driven over the HTTP API on a real git merge, ending in a clean `git commit`

**Phase 4 (branch `self-host`):**
  - Every `.py` under `src/literacode/` is now tangled from `lit/*.md` (format, tangle, stitch, merge, install, cli, resolve). The tangled files equal the old sources except for the sync marker lines; 57/57 tests pass on them. A `tangle` then `stitch` over all files leaves the documents byte-identical, and an edit made in a `.py` file stitched into the right chunk only.
  - 🆕 Addition — `lit tangle` accepts several documents and `--check` (writes nothing, exits 1 on drift); the pre-commit hook uses it. Hook checked with Git for Windows bash: blocks a drifted `src/`, passes a clean one.
  - 🐛 Bug fix — a plain fence (no `id=`) containing chunk-looking fence lines was parsed as real chunks. `lit/format-grammar.md` therefore declared a chunk targeting `parser.py`, which `lit tangle lit/*.md` would have overwritten. A plain fence body is now prose, as in CommonMark.
  - 🐛 Bug fix — tangling `tangle.py` failed because its docstring contained a literal chunk reference, which tangle tried to expand. The docstring was reworded. There is still no escape syntax for a literal reference in code.
  - `.gitattributes` pins LF for `lit/*.md`, `src/literacode/*.py` and `.githooks/*`. The bootstrap exception of the literate-first rule is over.

- The format specification (grammar sections 1-6) now lives in `lit/format.md` beside the model, parser and serialiser chunks; `lit/format-grammar.md` is a pointer. The spec's model section no longer lists `Chunk.refs`, which was removed earlier. README and two docstrings updated to match.

**Open:** (1) The Phase 3 gate is pending a manual browser pass: build the UI with `npm.cmd run build` in `ui/`, run `lit resolve` on a real conflicted merge, click Get proposal, Accept, Edit, Reject and Resolve, once with an API key set. The agent call has only been tested with mocked providers. (2) `.kiro/specs/` was never committed, so the PLAN tick for the Phase 0 specs is unsupported; the specs must come from Kiro's Specs panel. (3) The conflict-resolver agent exists only as prompt text in `.kiro/agents/`. (4) `ui/dist` is gitignored; README documents the build. (5) Prose conflicts are not shown in `lit resolve`. (6) No escape for a literal chunk reference in code. (7) Four-backtick fences, CRLF closing fences and trailing blank lines in a stitched chunk body are not lossless. (8) `ruff` has not been run (not installed). (9) No `.lit_resolved` backup is kept; recovery is via git index stages.

---

## Session [2026-11-01-1700]

- **Start status:** commit `f9ad7b3`, Phase 2 files committed, Scenario A branches not yet created
- **End status:** commit `f476709`, Phase 2 gate passed; `lit install` working; Scenario A verified on real git branches; 38/38 tests green; Phase 3 next
- **Badges:**
  - 🆕 Addition — `src/literacode/merge.py` — three_way_merge() with full change taxonomy including reorder-vs-edit (Scenario A) and two-sided conflict (Scenario B)
  - 🆕 Addition — `src/literacode/driver.py` — merge_driver(), conflict marker embedding, exit codes 0/1
  - 🆕 Addition — `src/literacode/install.py` — lit install, writes .gitattributes + git config via sh wrapper
  - 🆕 Addition — `lit_merge_driver.sh` — sh wrapper so git's sh.exe can find Python regardless of path spaces
  - 🆕 Addition — `tests/test_merge.py` / `tests/test_driver.py` — 16 new tests
  - Scenario A verified on `scenario-a-ours` + `scenario-a-theirs` branches; driver exits 0, order [validate,parse,fmt], parse body has theirs' strip edit
  - `install.py` updated to write sh wrapper script (Windows-compatible)

**Open:** Phase 3 (lit resolve, React UI, conflict view, agent) is next.

---

## Session [2026-11-01-1600]

- **Start status:** commit `bc81b67`, Phase 0 active, steering files in place, model.py skeleton only, no parser/tangle/stitch
- **End status:** Phase 1 complete, 22/22 tests green; Phase 0 items 1 and 3 retroactively ticked; Phase 2 (merge driver) is next
- **Badges:**
  - 🆕 Addition — `src/literacode/parser.py` — parse_document / parse_string, full state machine (`bc81b67`+)
  - 🆕 Addition — `src/literacode/serialiser.py` — Document → markdown, byte-for-byte lossless
  - 🆕 Addition — `src/literacode/tangle.py` — tangle with sync markers, ref expansion, circular-ref detection
  - 🆕 Addition — `src/literacode/stitch.py` — stitch from sync markers back to document
  - 🆕 Addition — `src/literacode/cli.py` — `lit tangle` and `lit stitch` wired, stubs for install/merge/resolve
  - 🆕 Addition — `tests/fixtures/round_trip.md` — non-trivial fixture document
  - 🆕 Addition — 22 tests across test_parser, test_tangle, test_stitch, test_round_trip — all passing
  - pyproject.toml build-backend corrected to `setuptools.build_meta`

**Open:** Phase 0 item 4 (Devpost registration) — requires manual browser action, not automatable. Phase 2 (merge driver: three-way diff, Scenario A) is the next implementation target.

---

## Session [2026-11-01-1503]

- **Start status:** commit `6b7c3e9`, Phase 0 active, repo structure minimal (LICENSE, PLAN.md, SETUP.md, SPEC-SEEDS.md, .githooks/, .kiro/ subdirs empty)
- **End status:** commit `bc81b67`, Phase 0 still active, 24 task breakdown files committed, SESSION_HISTORY.md committed, two steering files remain uncommitted (product.md, tech.md modifications)
- **Badges:**
  - 🆕 Addition — created 24 phase-task breakdown files in `.kiro/tasks/` covering all PLAN.md checkboxes (`5dcdc80`)
  - 🆕 Addition — SESSION_HISTORY.md file tracking Claude sessions (`bc81b67`)
  - Populated `.kiro/steering/` with product.md and tech.md (uncommitted)

**Open:** All Phase 0 tasks remain open. The task breakdown is complete but no implementation has started. Steering files populated but not committed. Next session should begin with Phase 0 tasks (steering completion, spec creation via Kiro, grammar decision) or move to Phase 1 implementation.
