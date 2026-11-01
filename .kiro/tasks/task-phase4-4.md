# task-phase4-4: Pre-commit hook shipped

## Status
- [ ] Done

## What this is
The `.githooks/pre-commit` hook already exists. This task ensures it actually
does something useful and that it is documented. The hook is part of the
submission — a hook that never fires scores worse than no hook.

## Prerequisite
task-phase4-1 (literate migration) is required if the hook is checking sync
status. If the literate migration was cut, the hook can still do useful things
(ruff lint, pytest on changed files).

## How to execute

### 1. Decide what the hook does

At minimum (even without self-hosting):
- Run `ruff check src/` and block the commit if there are linting errors.
- Run `pytest --tb=short -q` and block if tests fail.

With self-hosting (task-phase4-1 done):
- Additionally run `lit tangle lit/*.md --check` to verify generated files
  are up to date. Block if any are stale.

### 2. Read the existing hook

```bash
cat .githooks/pre-commit
```

It already exists — do not overwrite it blindly. Extend it.

### 3. Wire it up

```bash
git config core.hooksPath .githooks
```

This is in `SETUP.md` but confirm it is set in the repo:
```bash
git config core.hooksPath
# should print: .githooks
```

### 4. Test the hook

Stage a change and commit:
```bash
git add .
git commit -m "test hook"
```

The hook should run. Introduce a deliberate ruff violation, confirm the hook
blocks. Fix it, confirm the commit goes through.

### 5. Document the hook

Add a comment block at the top of `.githooks/pre-commit` explaining what it
checks and why, so a judge reading the repo understands it.

## Done when
- The hook runs on `git commit`
- At minimum: ruff and pytest are checked
- A deliberate violation blocks the commit with a clear message
- The hook is documented in its own header comment
