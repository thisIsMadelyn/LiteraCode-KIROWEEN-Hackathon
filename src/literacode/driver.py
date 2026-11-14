"""
literacode merge driver — called by git as: lit merge %O %A %B %P

Exit 0 = clean merge.  Exit 1 = conflicts remain.
Output is always written to the %A path (ours).
"""
from __future__ import annotations

import sys
from pathlib import Path

from .merge import MergeResult, three_way_merge
from .model import Chunk
from .parser import parse_document
from .serialiser import serialise


# ---------------------------------------------------------------------------
# Conflict marker format (for lit resolve to find later)
# ---------------------------------------------------------------------------

_CONFLICT_ATTR = " lit:conflict"


def _embed_conflict_markers(result: MergeResult) -> None:
    """
    In-place: replace conflicted Chunk bodies in result.document with a
    conflict-marker block so lit resolve can locate them.

    Conflict marker format embedded in the chunk body:

        <<<<<<< ours
        <ours body>
        =======
        <theirs body>
        >>>>>>> theirs
    """
    conflict_map = {c.chunk_id: c for c in result.conflicts}

    for node in result.document.nodes:
        if not isinstance(node, Chunk):
            continue
        if node.id not in conflict_map:
            continue
        c = conflict_map[node.id]
        marker_body = (
            "<<<<<<< ours\n"
            + (c.ours_body or "")
            + "=======\n"
            + (c.theirs_body or "")
            + ">>>>>>> theirs\n"
        )
        node.body = marker_body
        # Tag the chunk's fence attrs so lit resolve can find it
        if _CONFLICT_ATTR not in node._fence_attrs:
            node._fence_attrs = node._fence_attrs + _CONFLICT_ATTR


def merge_driver(
    base: Path,
    ours: Path,
    theirs: Path,
    path_hint: str = "",
) -> int:
    """
    Main merge driver entry point.

    Args:
        base:      Path to the common ancestor file (%O).
        ours:      Path to our version (%A).  Result is written here.
        theirs:    Path to their version (%B).
        path_hint: The working-tree path of the file (%P), for messages.

    Returns:
        0 if the merge is clean, 1 if conflicts remain.
    """
    base_doc   = parse_document(base)
    ours_doc   = parse_document(ours)
    theirs_doc = parse_document(theirs)

    result = three_way_merge(base_doc, ours_doc, theirs_doc)

    # Embed conflict markers into the document before serialising
    if result.conflicts:
        _embed_conflict_markers(result)

    ours.write_text(serialise(result.document), encoding="utf-8", newline="")

    if result.conflicts:
        for conflict in result.conflicts:
            print(
                f"CONFLICT (literacode): chunk '{conflict.chunk_id}' "
                f"modified on both sides in {path_hint or str(ours)}",
                file=sys.stderr,
            )
        return 1

    return 0
