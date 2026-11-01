# task-phase5-2: Write-up — how Kiro was used

## Status
- [ ] Done

## What this is
A written account of how Kiro was used throughout the project. Judges score
"Technological Implementation" partly on whether Kiro was used meaningfully —
not just as a code assistant, but as an agent with specs, steering, hooks, and
a custom agent. This write-up is that evidence.

## How to execute

### 1. Where it goes

Two places:
- The Devpost submission form's "Built With" / description section.
- The "How Kiro was used" section in `README.md` (task-phase4-2).

### 2. What to cover

Write one paragraph per Kiro feature used:

**Specs**
Which specs were created, in what order, and how the interactive
requirements → design → tasks flow shaped the implementation. Include a
specific example: a design decision that changed because of the spec conversation.

**Steering**
What the three steering files contain and why they were written.
Specifically: how `literate-first.md` kept every coding session honest about
whether the bootstrap exception still applied.

**Hooks**
Which hooks were set up (`stitch-on-save`, `wrap-up`). When did `stitch-on-save`
actually fire and save time? If it never fired, say so honestly — a hook that
never fires scores worse than no hook.

**Custom agent**
The conflict-resolver agent: what prompt it has, what resources it was given,
and what a real proposal from it looked like during development. Include an
example input and the agent's output.

**Overall**
One paragraph on what it felt like to build a tool *with* the tool you are
building. What broke first when you tested the literate-first rule? What did
Kiro catch that you would have missed?

### 3. Tone

Direct and honest. Do not oversell. If a Kiro feature did not work well for
this project, say so — genuine feedback is more credible than marketing copy.

## Done when
- The write-up exists in README.md and is ready to paste into Devpost
- All four Kiro features (specs, steering, hooks, agent) are covered
- At least one concrete example per feature
