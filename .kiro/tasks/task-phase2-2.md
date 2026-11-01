# task-phase2-2: Reorder vs edit resolves clean → Scenario A

## Status
- [ ] Done

## What this is
The demo. One author reorders chunks in the narrative; the other edits a chunk
body. Line-based git mangles this; literacode merges it cleanly. This must work
end to end — not in a unit test, but from two real git branches in this repo.

## Prerequisite
task-phase2-1 must pass the Scenario A smoke test.

## How to execute

### 1. Create the demo document

`tests/demo/scenario_a.md` — a literate document with at least three chunks:

````markdown
# Scenario A demo

The parser comes first.

```python id=parse file=src/demo/main.py
def parse(text):
    return text.split()
```

Then we validate.

```python id=validate file=src/demo/main.py
def validate(tokens):
    return [t for t in tokens if t.isalpha()]
```

Finally we format the output.

```python id=fmt file=src/demo/main.py
def fmt(tokens):
    return ", ".join(tokens)
```
````

### 2. Create two branches

```bash
git checkout -b scenario-a-base
git add tests/demo/scenario_a.md
git commit -m "demo: add scenario A base document"

git checkout -b scenario-a-ours
# edit scenario_a.md: reorder chunks to [validate, parse, fmt]
git add tests/demo/scenario_a.md
git commit -m "demo: reorder narrative (validate first)"

git checkout -b scenario-a-theirs
git checkout scenario-a-base -- tests/demo/scenario_a.md
# edit scenario_a.md: change the parse function body
git add tests/demo/scenario_a.md
git commit -m "demo: improve parse to strip punctuation"
```

### 3. Run the structural merge

```bash
git checkout scenario-a-ours
git merge scenario-a-theirs
```

Without `lit install` active, this will use git's line-based merge and
probably produce a mess. That mess is your before-state — screenshot it.

Then install the driver (task-phase2-3) and re-run the merge. The after-state
must be a clean merge with the reordered narrative and the edited parse body.

### 4. Verify the result

After the merge:
1. The document has chunks in the `ours` order: [validate, parse, fmt].
2. The `parse` chunk body contains the theirs edit.
3. `lit tangle` on the merged document produces valid Python without errors.
4. Exit code of the merge driver was 0.

## Done when
- The merge succeeds on real branches with exit code 0
- The merged document has the right order and the right edit
- `lit tangle` on the result produces valid Python
- Before/after screenshots or a git log exist to demonstrate in the video
