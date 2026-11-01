# literacode — Kiro setup kit

Unzip over an empty repo root. Then:

```bash
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
git checkout -b phase-0
```

## What is here

| Path | What it is | Judged? |
|---|---|---|
| `.kiro/steering/product.md` | the Resurrection thesis, in Kiro's context on every turn | **yes** |
| `.kiro/steering/tech.md` | stack, command contract, hard scope limits | **yes** |
| `.kiro/steering/literate-first.md` | the self-hosting rule and its bootstrap exception | **yes** |
| `.kiro/hooks/stitch-on-save.kiro.hook` | `fileEdited` on `src/**/*.py` → `lit stitch` | **yes** |
| `.kiro/hooks/wrap-up.kiro.hook` | manual trigger, end-of-session close-out | **yes** |
| `.kiro/agents/conflict-resolver.md` | the agent prompt — **create the agent through Kiro's UI** | **yes** |
| `.kiro/specs/` | **not here on purpose** — see `SPEC-SEEDS.md` | **yes** |
| `PLAN.md` | head task: phases, critical path, cut order | visible |
| `SPEC-SEEDS.md` | prompts to start the three specs in Kiro | no |
| `.githooks/pre-commit` | branch guard + sync guard | no |

The `.kiro/` directory is part of the submission. Keep it true: a hook that never
fires scores worse than no hook.

## Verify before trusting

Two things were written from documentation, not from your installation:

1. **The hook file format.** `when.type` / `then.type` and the `.kiro.hook`
   extension. Open one hook in Kiro's Agent Hooks panel. If it does not load,
   create one hook through the UI, look at what it writes, and fix these two to match.
2. **The custom-agent schema.** That is why `conflict-resolver.md` is a prompt
   and not a config file — create the agent in Kiro's UI and paste it, attaching
   `{ "resources": ["file://.kiro/steering/**/*.md"] }`.

## Order of operations

1. Install the hooks above, confirm they load in Kiro.
2. Open `SPEC-SEEDS.md`. Create the `format` spec in Kiro from seed 1. Work
   through requirements → design with Kiro, do not hand-write them.
3. Only then create `merge-driver`. The UI spec comes last.
4. End every session with the wrap-up hook.
