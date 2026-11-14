# lit:chunk id=parser-header src=lit/format.md
"""
literacode parser — document → model.

State machine over lines.  A fenced code block with an `id=` attribute becomes
a Chunk; everything else (including plain fences without id=) accumulates as
Prose.
"""
from __future__ import annotations

import re
from pathlib import Path

from .model import Chunk, Document, Prose

# Opening fence: ```[lang][attrs]  (the language may be absent)
# Group 1 = fence marker, 2 = lang, 3 = rest of attribute string (may be empty)
FENCE_OPEN_RE = re.compile(r"^(```+)(\w*)([ \t].*)?\s*$")

# Key=value tokens in the attribute string
ATTR_RE = re.compile(r"([\w-]+)=(\S+)")


# lit:chunk id=_parse_attrs src=lit/format.md
def _parse_attrs(attr_str: str) -> dict[str, str]:
    """Return {key: value} from a space-separated key=value string."""
    return {m.group(1): m.group(2) for m in ATTR_RE.finditer(attr_str)}


# lit:chunk id=parse_document src=lit/format.md
def parse_document(path: Path) -> Document:
    """
    Parse a literacode markdown file and return a Document.

    Any .md file is valid input.  A file with no chunk attributes produces
    a Document with a single Prose node (or an empty Document for empty files).
    """
    text = path.read_text(encoding="utf-8", newline="")
    return parse_string(text)


# lit:chunk id=parse_string src=lit/format.md
def parse_string(text: str) -> Document:
    """Parse a literacode document from a string."""
    lines = text.splitlines(keepends=True)
    doc = Document()

    prose_lines: list[str] = []
    chunk_lines: list[str] = []
    in_chunk = False
    plain_fence_marker = ""             # set while inside a fence with no id=
    current_fence_marker: str = ""      # the backtick prefix (``` or ````)
    current_fence_attrs: str = ""       # the raw attribute string after lang
    current_lang: str = ""
    current_id: str = ""
    current_file: str | None = None
    current_attrs_raw: str = ""

    def flush_prose() -> None:
        if prose_lines:
            doc.nodes.append(Prose(text="".join(prose_lines)))
            prose_lines.clear()

    def flush_chunk() -> None:
        doc.nodes.append(
            Chunk(
                id=current_id,
                file=current_file,
                lang=current_lang,
                body="".join(chunk_lines),
                _fence_attrs=current_attrs_raw,
            )
        )
        chunk_lines.clear()

    for line in lines:
        if plain_fence_marker:
            # Inside a plain fence: everything up to its closing fence is
            # prose, even lines that look like chunk fences (CommonMark rule).
            prose_lines.append(line)
            if line.rstrip("\n\r") == plain_fence_marker:
                plain_fence_marker = ""
        elif not in_chunk:
            # Check for an opening fence
            m = FENCE_OPEN_RE.match(line)
            if m:
                fence_marker = m.group(1)   # ``` or ````
                lang = m.group(2)
                attr_str = m.group(3) or ""
                attrs = _parse_attrs(attr_str)
                if "id" in attrs:
                    # This is a literacode chunk
                    flush_prose()
                    # Stash opening fence line as prose so we can reconstruct it
                    in_chunk = True
                    current_fence_marker = fence_marker
                    current_lang = lang
                    current_id = attrs["id"]
                    current_file = attrs.get("file")
                    # Preserve the original attribute string (after lang) exactly
                    current_attrs_raw = (m.group(3) or "").rstrip()
                    chunk_lines.clear()
                    continue
                # Plain fence without id= → prose
                prose_lines.append(line)
                plain_fence_marker = fence_marker
            else:
                prose_lines.append(line)
        else:
            # Inside a chunk — look for the closing fence
            stripped = line.rstrip("\n\r")
            if stripped == current_fence_marker:
                # Closing fence
                flush_chunk()
                in_chunk = False
                current_fence_marker = ""
            else:
                chunk_lines.append(line)

    # Flush any remaining content
    if in_chunk:
        # Unclosed fence — treat accumulated lines as prose (be lenient)
        # Re-emit the opening fence line and the body as prose
        prose_lines.append(
            f"{current_fence_marker}{current_lang}{current_attrs_raw}\n"
        )
        prose_lines.extend(chunk_lines)
        flush_prose()
    else:
        flush_prose()

    return doc
