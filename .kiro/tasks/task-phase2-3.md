# task-phase2-3: `lit install` — driver registered and called by real git

## Status
- [x] Done

## What this is
`lit install` does two things: writes `.gitattributes` to tell git which files
use the literacode merge driver, and registers the driver in `.git/config` so
git knows what command to call. After this, `git merge` on any `*.md` file will
call `lit merge` instead of the built-in line-based merge.

## Prerequisite
`lit merge` must exist (even as a stub) before `lit install` is useful.
task-phase2-4 covers `lit merge`; install and merge can be built together.

## How to execute

### 1. Create `src/literacode/install.py`

```python
from pathlib import Path
import subprocess

def install(repo_root: Path) -> None:
    _write_gitattributes(repo_root)
    _register_driver(repo_root)
    print("literacode merge driver installed.")
    print("  .gitattributes updated")
    print("  .git/config updated")

def _write_gitattributes(root: Path) -> None:
    ga = root / ".gitattributes"
    line = "*.md merge=literacode\n"
    if ga.exists():
        existing = ga.read_text()
        if "merge=literacode" in existing:
            return  # already present
        ga.write_text(existing.rstrip("\n") + "\n" + line)
    else:
        ga.write_text(line)

def _register_driver(root: Path) -> None:
    # git config --local merge.literacode.driver "lit merge %O %A %B %P"
    subprocess.run(
        ["git", "config", "--local",
         "merge.literacode.driver", "lit merge %O %A %B %P"],
        cwd=root,
        check=True,
    )
```

### 2. Wire up the CLI

```python
def cmd_install(args):
    from .install import install
    install(Path("."))
```

`lit install` with no arguments, run from repo root.

### 3. Verify it works

After running `lit install` in the literacode repo:

```bash
cat .gitattributes
# should contain: *.md merge=literacode

git config --local merge.literacode.driver
# should print: lit merge %O %A %B %P
```

### 4. Idempotency

Running `lit install` twice must not duplicate the `.gitattributes` line or
error on the git config. The `_write_gitattributes` guard above handles the
file; `git config` overwrites existing values by default (that's fine).

## Done when
- `lit install` exits 0 and writes both files
- Running it twice is safe
- `git config --local merge.literacode.driver` returns the correct command
- `.gitattributes` contains `*.md merge=literacode`
