# task-phase0-2: Kiro steering in place, three specs created through Kiro

## Status
- [ ] Done

## What this is
Two things bundled in one checkbox:
1. The `.kiro/steering/` files are written and loaded by Kiro.
2. All three specs (`format`, `merge-driver`, `resolve-ui`) exist in
   `.kiro/specs/` and were created interactively through Kiro's Spec panel
   (not hand-written). This matters for judging.

## How to execute

### Part A — Steering files

Confirm these three files exist and are non-empty:

- `.kiro/steering/product.md` — the Resurrection thesis
- `.kiro/steering/tech.md` — stack, commands, scope limits
- `.kiro/steering/literate-first.md` — the self-hosting rule

If any are missing, create them from the content in `SETUP.md` and the
workspace rules already in `.kiro/`.

### Part B — Three specs via Kiro Spec panel

Open Kiro's Spec panel (not this chat). For each seed in `SPEC-SEEDS.md`,
paste the seed text as the opening prompt of a **new spec** and iterate
requirements → design → tasks with Kiro interactively.

Create in this order:
1. `format` — must reach design phase before `merge-driver` starts
2. `merge-driver`
3. `resolve-ui`

Each spec will produce:
- `.kiro/specs/format/requirements.md`
- `.kiro/specs/format/design.md`
- `.kiro/specs/format/tasks.md`
(and equivalents for the other two)

**Do not hand-write these files.** The judge workflow scores the interactive
spec creation, not the presence of markdown files.

## Done when
- All three steering files exist
- `.kiro/specs/format/`, `.kiro/specs/merge-driver/`, `.kiro/specs/resolve-ui/`
  each contain `requirements.md`, `design.md`, and `tasks.md`
