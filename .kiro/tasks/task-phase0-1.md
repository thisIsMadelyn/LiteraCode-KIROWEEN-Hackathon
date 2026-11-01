# task-phase0-1: Repo created, MIT license, first commit dated after 30 Oct

## Status
- [x] Done

## What this is
Confirm that the git repository exists, has an MIT license file, and the initial
commit timestamp is after 30 October 2026. This is a Devpost eligibility
requirement — the project must have been created within the hackathon window.

## How to execute

1. **Verify the repo exists and has commits:**
   ```bash
   git log --oneline
   ```
   The first (oldest) commit should show a date after 30 Oct 2026.

2. **Verify the LICENSE file is present and is MIT:**
   The file `LICENSE` already exists at the repo root. Open it and confirm it
   says "MIT License" and has your name on it.

3. **Fix the commit date if wrong (only if needed):**
   If the first commit predates 30 Oct, you will need to rebase or amend.
   Do not do this silently — confirm with the plan owner first.

## Done when
- `git log --format="%ai %s" | tail -1` shows a date ≥ 2026-10-31
- `LICENSE` contains "MIT License"
- No action needed if both are already true
