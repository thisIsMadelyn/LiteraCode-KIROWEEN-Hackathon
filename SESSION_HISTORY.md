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

## Session [2026-11-10-1406]

- **Start status:** commit `755a26b` on `main`, Phase 2 gate passed, 38/38 tests green, Phase 3 next
- **End status:** branch `simplify-core` at `960ef25`, 37/37 tests green, Phase 3 not started
- **Badges:**
  - 🐛 Bug fix — `python -m literacode.cli` had no `__main__` guard, so the git driver wrapper exited 0 without merging; Scenario A re-verified on real git (plain git conflicts, driver merges clean) (`ccd3054`)
  - 🐛 Bug fix — `lit stitch` crashed on a non-UTF console printing `→`; printed output is now ASCII (`ccd3054`)
  - `merge.py` collapsed from 263 to 118 lines: one per-chunk resolve rule, deterministic conflict order; checked against the old implementation on 20,000 random documents with 0 differences (`393ee49`)
  - `stitch.py` simplified from 113 to 76 lines; fuzzy `src` path check replaced by a basename check (`205c17d`)
  - Merge driver now registered directly as `<python> -m literacode.cli merge`; `lit_merge_driver.sh` removed (`80727a7`)
  - Removed unused `Chunk.refs` and `driver.merge_driver_on_docs`; one test removed (`960ef25`)

**Open:** Prose edits made only on the "theirs" side are dropped by the merge (prose is taken from ours). Four-backtick fences, CRLF closing fences and trailing blank lines in a stitched chunk body are not lossless. No `.gitignore`, and `core.autocrlf` behaviour is undecided. `ruff` was not run (not installed). `simplify-core` is not merged to `main`. Phase 3 (`lit resolve`) is next.

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
