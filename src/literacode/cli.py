"""
literacode CLI entry point.

Commands:
    lit tangle <file.md>          — document → .py files
    lit stitch <file.py> ...      — edited .py files → chunks in document
    lit install                   — register git merge driver
    lit merge %O %A %B %P         — the merge driver (called by git)
    lit resolve                   — serve the conflict resolution UI
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .driver import merge_driver
from .install import install
from .parser import parse_document
from .stitch import MARKER_RE, StitchError, stitch
from .tangle import TangleError, tangle


def cmd_tangle(args: argparse.Namespace) -> int:
    doc_path = Path(args.file)
    if not doc_path.exists():
        print(f"lit tangle: file not found: {doc_path}", file=sys.stderr)
        return 1

    out_root = Path(args.out) if args.out else Path(".")

    try:
        written = tangle(parse_document(doc_path), doc_path, out_root)
    except TangleError as e:
        print(f"lit tangle: {e}", file=sys.stderr)
        return 1

    if not written:
        print("lit tangle: no tangle targets found (no chunk has file= attribute)")
    for p in written:
        print(f"  wrote {p}")
    return 0


def _doc_path_from_markers(py_path: Path) -> Path | None:
    """The source document named by the first sync marker in py_path, if any."""
    for line in py_path.read_text(encoding="utf-8").splitlines():
        m = MARKER_RE.match(line)
        if m:
            return Path(m.group(2))
    return None


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


def cmd_install(args: argparse.Namespace) -> int:
    return install(Path("."))


def cmd_merge(args: argparse.Namespace) -> int:
    # git calls: lit merge %O %A %B %P
    # %O = base, %A = ours (write result here), %B = theirs, %P = path hint
    return merge_driver(
        base=Path(args.base),
        ours=Path(args.ours),
        theirs=Path(args.theirs),
        path_hint=args.path,
    )


def cmd_resolve(args: argparse.Namespace) -> int:
    # Phase 3: the module does not exist yet, so import lazily.
    from .resolve import serve
    return serve(port=args.port)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lit",
        description="literacode - literate markdown round-trip and merge driver",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_tangle = sub.add_parser("tangle", help="document -> .py files")
    p_tangle.add_argument("file", help="path to the .md document")
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
    p_resolve.add_argument("--port", type=int, default=7777)
    p_resolve.set_defaults(func=cmd_resolve)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
