# task-phase5-1: 3-minute video

## Status
- [ ] Done

## What this is
The video is the primary submission artifact. It is what judges watch first.
It must demonstrate both scenarios — the silent win (Scenario A) and the human
resolution flow (Scenario B) — in three minutes. No fluff.

## How to execute

### 1. Script (write before recording)

```
00:00 – 00:20  The problem
  "Git sees a literate document as text. Two people edit it — the merge
   destroys the structure. Watch."
  [show a git merge producing garbage on a literate file]

00:20 – 01:15  Scenario A — the silent win
  "One author reorders the narrative. The other edits a chunk body.
   literacode merges it structurally."
  [terminal: git merge on the scenario-a branches, exit 0, show the result]
  [open the merged document — correct order, correct edit]

01:15 – 02:10  Scenario B — the real conflict
  "Both authors edited the same chunk. The driver refuses to guess.
   lit resolve opens the review UI."
  [terminal: git merge produces exit 1, conflict markers in document]
  [browser: lit resolve opens, three-way view with prose context]
  [click "Get proposal", diff appears]
  [click Accept, click Resolve, browser shows "All resolved"]
  [terminal: document is resolved, git add completes the merge]

02:10 – 02:40  Self-hosting (if done)
  "literacode is written in literacode."
  [show lit/format.md in a text editor — readable spec + code]
  [run lit tangle lit/format.md — generates parser.py]

02:40 – 03:00  Kiro
  "Built with Kiro: steering files, specs, hooks, custom agent."
  [brief .kiro/ directory walk: steering, specs, agents, hooks]
```

### 2. Recording setup

- Terminal font size: at least 16pt. Judges watch on small screens.
- Browser: 1280px wide, no personal bookmarks visible.
- No background music. Clear narration.
- Record at 1080p or higher.

### 3. Tools

Any of: OBS Studio (free), macOS Screen Recording, QuickTime, Loom.

### 4. Edit

Keep it tight. Cut dead air. Each scene should be as short as it can be while
still being legible. 3 minutes is a hard cap — Devpost may enforce it.

## Done when
- Video is recorded, edited, and under 3 minutes
- Both scenarios are shown
- Kiro usage is mentioned
- Video is uploaded and the URL is ready for the Devpost submission form
