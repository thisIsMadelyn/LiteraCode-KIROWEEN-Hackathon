<!-- generated files: src/literacode/install.py -->
<!-- do not edit generated files directly: edit this document, then run `lit tangle`, or edit the .py and run `lit stitch` -->

# Installing the driver

`lit install` makes git use the merge driver for markdown files in this repository. It adds one line to `.gitattributes` and registers the driver command in the local git config.

## `src/literacode/install.py`

The driver is registered under the name `literacode`, and `.gitattributes` maps markdown files to it.

```python id=install-header file=src/literacode/install.py
"""
literacode install — register the git merge driver.

Writes .gitattributes and registers the driver in .git/config.
"""
from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

GITATTRIBUTES_LINE = "*.md merge=literacode\n"
```

Installing is idempotent. It reports what it changed and how to check it.

```python id=install file=src/literacode/install.py
def install(repo_root: Path) -> int:
    """
    Register the literacode merge driver for this git repository.

    Returns 0 on success, 1 on error.
    """
    try:
        _write_gitattributes(repo_root)
        _register_driver(repo_root)
    except subprocess.CalledProcessError as e:
        print(f"lit install: git config failed: {e}")
        return 1
    except OSError as e:
        print(f"lit install: {e}")
        return 1

    print("literacode merge driver installed.")
    print("  .gitattributes updated")
    print("  .git/config updated")
    print()
    print("Verify with:")
    print("  cat .gitattributes        # should contain: *.md merge=literacode")
    print("  git config --local merge.literacode.driver")
    return 0
```

The attribute line is appended once and never duplicated.

```python id=_write_gitattributes file=src/literacode/install.py
def _write_gitattributes(root: Path) -> None:
    ga = root / ".gitattributes"
    if not ga.exists():
        ga.write_text(GITATTRIBUTES_LINE, encoding="utf-8")
        return
    existing = ga.read_text(encoding="utf-8")
    if "merge=literacode" in existing:
        return  # already present, idempotent
    ga.write_text(existing.rstrip("\n") + "\n" + GITATTRIBUTES_LINE, encoding="utf-8")
```

The command runs the interpreter that ran `lit install`, not whatever `lit` is on PATH when git runs it. Git runs the command through `sh`, so the path is shell-quoted.

```python id=_driver_command file=src/literacode/install.py
def _driver_command() -> str:
    """
    The command git runs for a merge.

    Uses the interpreter that ran ``lit install`` rather than relying on
    ``lit`` being on PATH when git invokes the driver.  git runs this through
    ``sh``, so the interpreter path is shell-quoted.
    """
    python = shlex.quote(sys.executable.replace("\\", "/"))
    return f"{python} -m literacode.cli merge %O %A %B %P"
```

The driver is stored in the local repository config, not the global one.

```python id=_register_driver file=src/literacode/install.py
def _register_driver(root: Path) -> None:
    subprocess.run(
        [
            "git", "config", "--local", "--replace-all",
            "merge.literacode.driver", _driver_command(),
        ],
        cwd=root,
        check=True,
    )
```
