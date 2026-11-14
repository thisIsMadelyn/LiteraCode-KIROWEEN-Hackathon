# literacode — PLAN

**Head task. Phases, dependencies and cut order live here. Checkboxes for actual
work live in `.kiro/specs/<spec>/tasks.md`. Never duplicate a task across both.**

Deadline: **Fri 4 Dec 2026, 14:00 PT = Sat 5 Dec 00:00 Athens**
Status: Phase 3
Days left: 24

---

## Specs

| Spec | Covers |
|---|---|
| `format` | the literate markdown grammar, the document model, tangle and stitch |
| `merge-driver` | three-way merge over the document model, git integration |
| `resolve-ui` | the local web UI and the conflict-resolver agent |

---

## Critical path

```
format: tangle + stitch round trip
   └── merge-driver: document model diff
          └── Scenario A clean merge      ← the demo stands or falls here
                 └── resolve-ui: Scenario B
```

Everything outside this chain is optional.

---

## Phases

### Phase 0 — foundation (1–2 Nov)
- [x] repo created, MIT license, first commit dated after 30 Oct
- [x] Kiro steering in place, three specs created through Kiro
- [x] format grammar decided and written down
- [x] registered on Devpost, official rules read end to end

### Phase 1 — round trip (3–9 Nov)
- [x] parser: document → model (prose sections, chunks with ids, references)
- [x] `lit tangle`, with sync markers
- [x] `lit stitch`
- [x] losslessness test: tangle → edit → stitch → tangle is a fixed point

**Gate:** the round trip is lossless on a non-trivial document. Nothing proceeds
past this. ✅ Gate passed — all 22 tests green.

### Phase 2 — the merge driver (10–16 Nov)
- [x] three-way diff over the model
- [x] reorder vs edit resolves clean → **Scenario A**
- [x] `lit install`, driver registered and called by real git
- [x] exit codes correct, conflict markers written where unresolvable

**Gate:** Scenario A reproduces from two real branches, not a unit test. ✅ Gate passed — `git merge scenario-a-theirs` exits 0 with correct order and body.

### Phase 3 — the human surface (17–23 Nov)
- [ ] `lit resolve` serves the React UI
- [x] three-way chunk view with surrounding prose
- [x] conflict-resolver agent wired in, output is a reviewable diff
- [x] accept / reject / hand-edit, writes the resolution

**Gate:** Scenario B works end to end.

**Gate status: PENDING manual sign-off (owner: user).** API path verified on real git; still to do by hand: build the UI (`npm.cmd run build` in `ui/`), run `lit resolve` on a real conflicted merge, click Get proposal / Accept / Edit / Reject / Resolve, and try once with an API key set. Tick this gate only after that pass.

### Phase 4 — self-hosting and polish (24–29 Nov)
- [x] migrate `src/` to literate sources under `lit/`
- [ ] README with the thesis and a 60-second quickstart
- [ ] the format spec written in the format, tangling to the parser
- [x] pre-commit hook shipped

### Phase 5 — submission (30 Nov – 3 Dec)
- [ ] 3-minute video
- [ ] write-up: how Kiro was used — specs, steering, hooks, custom agent
- [ ] Devpost submission, repo public, `.kiro/` committed
- [ ] submit by 2 Dec

**4 Dec is buffer. Do not plan into it.**

---

## Cut order

If the schedule slips, cut in this order and do not negotiate:

1. Self-hosting migration (Phase 4) — keep the claim out of the write-up if not done
2. The conflict-resolver agent — the UI still works with manual resolution
3. Chunk references (`<<chunk-id>>` composition) — single-chunk-per-file only
4. The React UI → a plain terminal three-way view

**Never cut:** the round trip, Scenario A, the video.

---

## Risks

| Risk | Mitigation |
|---|---|
| Stitch is harder than it looks (ambiguous marker recovery) | Phase 1 gate is hard. If it slips past 9 Nov, cut item 3 immediately. |
| Scenario A does not actually beat git in a real repo | Test with real branches in Phase 2, not fixtures. If git handles it, the demo premise is wrong — find out by 16 Nov, not 30 Nov. |
| University coursework | Phases are sized for ~3 h/day, not full days. |
| Agent output unreliable in the video | Scenario A carries the demo. The agent is the second half, not the first. |

---

## Session log

Append only. One line per session: date, SHA, what moved, what is blocked.

2026-11-01 · bc81b67 · 24 task breakdowns created, SESSION_HISTORY.md added, steering files populated · blocked: nothing
2026-11-01 · ca63ba0 · Phase 1 complete · parser, tangle, stitch, losslessness gate — 22/22 tests green · Phase 2 (merge driver) next
2026-11-01 · 9e0946c · Phase 2 complete · merge driver, Scenario A gate on real branches · Phase 3 (resolve UI) next
2026-11-10 · 960ef25 · simplification pass on branch simplify-core · fixed no-op driver (missing __main__ guard), merge.py and stitch.py slimmed, wrapper script removed · open: theirs-side prose edits dropped by merge, simplify-core not yet merged to main · Phase 3 (resolve UI) next
2026-11-14 · 00d9089 · simplify-core merged to main; prose now merged per slot (theirs-side prose edits kept, both-sided prose edits conflict); lit resolve server + /api/conflicts done (task 3-1 server half, React app not started) · Phase 3 continues
2026-11-14 · 4800d3f · React UI (ui/, Vite) with three-column view, line highlighting, prev/next and jump nav; screenshot-checked at 1280px · open: agent, resolve button and /api/resolve · next: tasks 3-3, 3-4
2026-11-14 · be4b41e · /api/propose + agent call (OpenAI/Anthropic/stub) + proposal diff with Accept/Edit/Reject in UI · open: not exercised against a live provider, Resolve button and /api/resolve · next: task 3-4
2026-11-14 · 738af7b · /api/resolve + Resolve button + all-done screen; Scenario B driven through the HTTP API on a real git merge (conflict, propose, resolve, git add, commit) · open: Phase 3 gate not signed off, UI buttons never clicked in a browser, agent never run against a live provider · next: manual browser pass, then Phase 4
2026-11-14 · branch self-host · src/ migrated to lit/*.md (7 documents, 12 files, 59 chunks); lit tangle takes several documents and --check; parser now treats a plain fence body as prose; pre-commit hook blocks stale src/ (tested with Git bash) · open: self-host not merged to main, no escape for a literal chunk reference in code · bootstrap exception is over: edit lit/, not src/
