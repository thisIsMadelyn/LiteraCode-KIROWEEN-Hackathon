# literacode — PLAN

**Head task. Phases, dependencies and cut order live here. Checkboxes for actual
work live in `.kiro/specs/<spec>/tasks.md`. Never duplicate a task across both.**

Deadline: **Fri 4 Dec 2026, 14:00 PT = Sat 5 Dec 00:00 Athens**
Status: Phase 0
Days left: 33

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
- [ ] repo created, MIT license, first commit dated after 30 Oct
- [ ] Kiro steering in place, three specs created through Kiro
- [ ] format grammar decided and written down
- [ ] registered on Devpost, official rules read end to end

### Phase 1 — round trip (3–9 Nov)
- [ ] parser: document → model (prose sections, chunks with ids, references)
- [ ] `lit tangle`, with sync markers
- [ ] `lit stitch`
- [ ] losslessness test: tangle → edit → stitch → tangle is a fixed point

**Gate:** the round trip is lossless on a non-trivial document. Nothing proceeds
past this.

### Phase 2 — the merge driver (10–16 Nov)
- [ ] three-way diff over the model
- [ ] reorder vs edit resolves clean → **Scenario A**
- [ ] `lit install`, driver registered and called by real git
- [ ] exit codes correct, conflict markers written where unresolvable

**Gate:** Scenario A reproduces from two real branches, not a unit test.

### Phase 3 — the human surface (17–23 Nov)
- [ ] `lit resolve` serves the React UI
- [ ] three-way chunk view with surrounding prose
- [ ] conflict-resolver agent wired in, output is a reviewable diff
- [ ] accept / reject / hand-edit, writes the resolution

**Gate:** Scenario B works end to end.

### Phase 4 — self-hosting and polish (24–29 Nov)
- [ ] migrate `src/` to literate sources under `lit/`
- [ ] README with the thesis and a 60-second quickstart
- [ ] the format spec written in the format, tangling to the parser
- [ ] pre-commit hook shipped

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

<!-- 2026-11-01 · <sha> · scope locked, Kiro setup in place · blocked: nothing -->
