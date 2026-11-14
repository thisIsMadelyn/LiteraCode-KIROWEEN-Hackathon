# lit:chunk id=install-header src=lit/install.md
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


# lit:chunk id=install src=lit/install.md
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


# lit:chunk id=_write_gitattributes src=lit/install.md
def _write_gitattributes(root: Path) -> None:
    ga = root / ".gitattributes"
    if not ga.exists():
        ga.write_text(GITATTRIBUTES_LINE, encoding="utf-8")
        return
    existing = ga.read_text(encoding="utf-8")
    if "merge=literacode" in existing:
        return  # already present, idempotent
    ga.write_text(existing.rstrip("\n") + "\n" + GITATTRIBUTES_LINE, encoding="utf-8")


# lit:chunk id=_driver_command src=lit/install.md
def _driver_command() -> str:
    """
    The command git runs for a merge.

    Uses the interpreter that ran ``lit install`` rather than relying on
    ``lit`` being on PATH when git invokes the driver.  git runs this through
    ``sh``, so the interpreter path is shell-quoted.
    """
    python = shlex.quote(sys.executable.replace("\\", "/"))
    return f"{python} -m literacode.cli merge %O %A %B %P"


# lit:chunk id=_register_driver src=lit/install.md
def _register_driver(root: Path) -> None:
    subprocess.run(
        [
            "git", "config", "--local", "--replace-all",
            "merge.literacode.driver", _driver_command(),
        ],
        cwd=root,
        check=True,
    )
