# task-phase5-3: Devpost submission — repo public, `.kiro/` committed

## Status
- [ ] Done

## What this is
The actual submission. Everything must be in order before clicking Submit:
the repo is public, `.kiro/` is committed and pushed, the video URL is ready,
and the write-up is in the description.

Deadline: **2 Dec 2026** (4 Dec is buffer — do not plan into it).

## How to execute

### 1. Final repo checks

```bash
# Confirm .kiro/ is tracked by git
git ls-files .kiro/

# Confirm no secrets are committed (.env, API keys)
git log --all --full-history -- "**/.env"
git log --all --full-history -- "**/secrets*"

# Confirm .gitignore does not exclude .kiro/
grep -n "\.kiro" .gitignore  # should return nothing, or a comment
```

### 2. Final test run

```bash
pip install -e .
pytest
lit tangle examples/demo.md
lit install
# Run Scenario A manually one more time
```

Everything must pass cleanly.

### 3. Make the repo public

On GitHub: Settings → Danger Zone → Change visibility → Public.

Confirm the URL works in an incognito window.

### 4. Devpost submission form

Fill in:
- **Project name:** literacode
- **Tagline:** Structural git merges for literate programming documents
- **What it does:** (2–3 paragraphs from the README thesis section)
- **How I built it:** (the Kiro write-up from task-phase5-2)
- **Challenges:** (be specific — stitch serialiser, conflict marker format, etc.)
- **Accomplishments:** Scenario A working on real branches. Self-hosting.
- **What I learned:**
- **Built with:** Python, React, Vite, ruff, pytest, Kiro
- **GitHub URL:** (repo URL)
- **Video URL:** (from task-phase5-1)
- **Try it:** `pip install literacode` or link to a demo branch

### 5. Submit

Click Submit. Screenshot the confirmation.

## Done when
- Submission is confirmed on Devpost
- Screenshot of confirmation saved
- Repo is public and `.kiro/` is visible on GitHub
