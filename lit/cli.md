<!-- generated files: src/literacode/cli.py -->
<!-- do not edit generated files directly: edit this document, then run `lit tangle`, or edit the .py and run `lit stitch` -->

# The command line

`lit` is a thin dispatcher. Each subcommand parses its arguments and calls into the module that does the work, so the interesting logic lives elsewhere and is tested without going through argparse.

## `src/literacode/cli.py`

Every command returns an exit code that `main` passes to `sys.exit`.

```python id=cli-header file=src/literacode/cli.py
"""
literacode CLI entry point.

Commands:
    lit tangle <file.md>          — document → .py files
    lit stitch <file.py> ...      — edited .py files → chunks in document
    lit install                   — register git merge driver
    lit merge %O %A %B %P         — the merge driver (called by git)
    lit resolve [file.md] [--port N]  — serve the conflict resolution UI
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .driver import merge_driver
from .install import install
from .parser import parse_document
from .stitch import MARKER_RE, StitchError, stitch
from .tangle import TangleError, stale, tangle
```

Tangle accepts several documents. With `--check` it writes nothing and exits 1 if any generated file differs from disk.

```python id=cmd_tangle file=src/literacode/cli.py
def cmd_tangle(args: argparse.Namespace) -> int:
    out_root = Path(args.out) if args.out else Path(".")
    rc = 0
    found_target = False

    for file in args.files:
        doc_path = Path(file)
        if not doc_path.exists():
            print(f"lit tangle: file not found: {doc_path}", file=sys.stderr)
            rc = 1
            continue

        try:
            doc = parse_document(doc_path)
            if args.check:
                paths = stale(doc, doc_path, out_root)
            else:
                paths = tangle(doc, doc_path, out_root)
        except TangleError as e:
            print(f"lit tangle: {e}", file=sys.stderr)
            rc = 1
            continue

        found_target = found_target or any(c.file for c in doc.chunks())
        for p in paths:
            if args.check:
                print(f"  stale {p}  (differs from {doc_path})", file=sys.stderr)
                rc = 1
            else:
                print(f"  wrote {p}")

    if not found_target and rc == 0:
        print("lit tangle: no tangle targets found (no chunk has file= attribute)")
    return rc

def _doc_path_from_markers(py_path: Path) -> Path | None:
    """The source document named by the first sync marker in py_path, if any."""
    for line in py_path.read_text(encoding="utf-8").splitlines():
        m = MARKER_RE.match(line)
        if m:
            return Path(m.group(2))
    return None
```

The source document is found from the sync markers inside the `.py` file, so the command only needs the Python files.

```python id=cmd_stitch file=src/literacode/cli.py
def cmd_stitch(args: argparse.Namespace) -> int:
    rc = 0
    for py_file in args.files:
        py_path = Path(py_file)
        if not py_path.exists():
            print(f"lit stitch: file not found: {py_path}", file=sys.stderr)
            rc = 1
            continue

        doc_path = _doc_path_from_markers(py_path)
        if doc_path is None:
            print(f"lit stitch: no sync markers found in {py_path} - nothing to do")
            continue

        if not doc_path.exists():
            print(
                f"lit stitch: source document {doc_path} not found "
                f"(referenced from markers in {py_path})",
                file=sys.stderr,
            )
            rc = 1
            continue

        try:
            stitch(py_path, doc_path)
        except StitchError as e:
            print(f"lit stitch: {e}", file=sys.stderr)
            rc = 1
        else:
            print(f"  stitched {py_path} -> {doc_path}")

    return rc
```

Installing always targets the current directory.

```python id=cmd_install file=src/literacode/cli.py
def cmd_install(args: argparse.Namespace) -> int:
    return install(Path("."))
```

Git calls this as `lit merge %O %A %B %P`: base, ours, theirs and the path.

```python id=cmd_merge file=src/literacode/cli.py
def cmd_merge(args: argparse.Namespace) -> int:
    # git calls: lit merge %O %A %B %P
    # %O = base, %A = ours (write result here), %B = theirs, %P = path hint
    return merge_driver(
        base=Path(args.base),
        ours=Path(args.ours),
        theirs=Path(args.theirs),
        path_hint=args.path,
    )
```

The server module is imported lazily so the other commands do not load it.

```python id=cmd_resolve file=src/literacode/cli.py
def cmd_resolve(args: argparse.Namespace) -> int:
    # Phase 3: the module does not exist yet, so import lazily.
    from .resolve import serve
    return serve(args.file, port=args.port)
```

Argument parsing is declared in one place, one subparser per command.

```python id=main file=src/literacode/cli.py
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lit",
        description="literacode - literate markdown round-trip and merge driver",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_tangle = sub.add_parser("tangle", help="document -> .py files")
    p_tangle.add_argument("files", nargs="+", help="path(s) to the .md document(s)")
    p_tangle.add_argument(
        "--check", action="store_true",
        help="write nothing; exit 1 if any generated file differs from disk",
    )
    p_tangle.add_argument(
        "--out", default=None, metavar="DIR",
        help="output root directory (default: current directory)"
    )
    p_tangle.set_defaults(func=cmd_tangle)

    p_stitch = sub.add_parser("stitch", help="edited .py files -> document chunks")
    p_stitch.add_argument("files", nargs="+", help=".py file(s) to stitch back")
    p_stitch.set_defaults(func=cmd_stitch)

    p_install = sub.add_parser("install", help="register git merge driver")
    p_install.set_defaults(func=cmd_install)

    p_merge = sub.add_parser("merge", help="merge driver (called by git)")
    p_merge.add_argument("base")
    p_merge.add_argument("ours")
    p_merge.add_argument("theirs")
    p_merge.add_argument("path")
    p_merge.set_defaults(func=cmd_merge)

    p_resolve = sub.add_parser("resolve", help="serve conflict resolution UI")
    p_resolve.add_argument("file", nargs="?", help="conflicted .md file (default: the one unmerged file)")
    p_resolve.add_argument("--port", type=int, default=7777)
    p_resolve.set_defaults(func=cmd_resolve)

    args = parser.parse_args()
    sys.exit(args.func(args))
```

Running the module directly must call `main`. The git driver is registered as `python -m literacode.cli merge`, and without this guard it exited 0 without merging anything.

```python id=main-guard file=src/literacode/cli.py
if __name__ == "__main__":
    main()
```
