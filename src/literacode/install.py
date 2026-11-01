"""
literacode install — register the git merge driver.

Writes .gitattributes and registers the driver in .git/config.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


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


def _write_gitattributes(root: Path) -> None:
    ga = root / ".gitattributes"
    line = "*.md merge=literacode\n"
    if ga.exists():
        existing = ga.read_text(encoding="utf-8")
        if "merge=literacode" in existing:
            return  # already present, idempotent
        # Append, ensuring a newline separator
        ga.write_text(
            existing.rstrip("\n") + "\n" + line,
            encoding="utf-8",
        )
    else:
        ga.write_text(line, encoding="utf-8")


def _register_driver(root: Path) -> None:
    """
    Register the literacode merge driver.

    On all platforms we register a wrapper shell script so git's sh.exe
    can invoke Python correctly regardless of spaces in the Python path.
    """
    import sys
    import platform

    python = sys.executable.replace("\\", "/")

    # Write a small sh wrapper script in the repo root so git can call it
    wrapper = root / "lit_merge_driver.sh"
    wrapper.write_text(
        f'#!/bin/sh\n"{python}" -m literacode.cli merge "$@"\nexit $?\n',
        encoding="utf-8",
    )

    subprocess.run(
        [
            "git", "config", "--local", "--replace-all",
            "merge.literacode.driver",
            "sh lit_merge_driver.sh %O %A %B %P",
        ],
        cwd=root,
        check=True,
    )
