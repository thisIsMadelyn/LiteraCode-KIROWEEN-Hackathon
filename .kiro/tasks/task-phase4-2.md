# task-phase4-2: README with the thesis and a 60-second quickstart

## Status
- [ ] Done

## What this is
The public face of the project. A judge landing on the repo should understand
the thesis in 30 seconds and be able to run the demo in 60 seconds. This is
also the document that carries the "how Kiro was used" story.

## How to execute

### 1. Structure

```markdown
# literacode

One-line thesis.

## The problem (3–4 sentences)
Why literate programming dies in a team. The merge problem.

## The solution (3–4 sentences)
Named chunks, structural merge, the two scenarios.

## Quickstart (60 seconds)

pip install literacode

# tangle a demo document
lit tangle examples/demo.md

# run a merge between two branches (Scenario A)
git clone ...
cd demo-repo
lit install
git merge scenario-a-theirs   # merges cleanly

## Commands

| Command | Does |
...

## How Kiro was used
(see task-phase5-2 for the content of this section)

## License
MIT
```

### 2. The demo document

Create `examples/demo.md` — a short but real literate document that:
- Has 3–4 chunks
- Tangles to working Python
- Is the document used in the Scenario A demo

This is what a judge will run. Make it self-contained.

### 3. Quickstart must actually work

Before publishing, run the quickstart steps yourself in a fresh virtualenv:
```bash
python -m venv /tmp/lit-test
source /tmp/lit-test/bin/activate
pip install .
lit tangle examples/demo.md
```

Fix any installation or dependency issues found.

## Done when
- `README.md` exists at repo root
- The quickstart commands work in a fresh environment
- `examples/demo.md` tangles to valid Python
