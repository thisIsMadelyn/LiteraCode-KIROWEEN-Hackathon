# literacode format grammar

**Status:** decided. This is the authoritative reference for the parser and the
merge driver. Edit only with a concrete reason; changing this after Phase 1 is
done breaks the round trip.

---

## 1. What a literate document is

A literacode document is ordinary CommonMark markdown. Any `.md` file is valid
input. Fenced code blocks may carry extra attributes that promote them from
"illustration" to "named chunk". A file with no chunk attributes parses without
error and produces a Document with only Prose nodes.

---

## 2. Chunk fence attributes

A chunk is a fenced code block whose opening fence line carries at least an `id=`
attribute. The format is **Option A** — space-separated key=value tokens after
the language tag:

```
```<lang> id=<id> [file=<path>] [key=value …]
```

Rules:

| Rule | Detail |
|---|---|
| Language tag is first, no `=` | `python`, `bash`, etc. |
| `id=` is required for a chunk | Any identifier matching `[\w-]+` |
| `file=` is optional | Relative path to the target `.py` file |
| Unknown keys are ignored | Forward-compatible |
| A plain ` ```python ` fence with no `id=` | Parsed as Prose, not a Chunk |
| Values must not contain spaces | Quote-free syntax; spaces delimit tokens |

### Examples

```
```python id=parse-header file=src/literacode/parser.py
```

```
```python id=helper
```
(no file= → not a tangle target, but has an identity for the merge driver)

```
```python
```
(no id= → plain prose fence, invisible to the tool)

---

## 3. Chunk references

Inside a chunk body, `<<other-id>>` is a reference that is expanded inline at
tangle time. References are resolved depth-first in document order. Circular
references are a hard error.

Pattern: `<<([\w-]+)>>`

---

## 4. Sync marker format

When `lit tangle` writes a `.py` file, it precedes each chunk region with a
sync marker comment. The marker is the single source of truth for `lit stitch`.

```python
# lit:chunk id=<id> src=<doc_path>
```

Rules:

| Rule | Detail |
|---|---|
| Must be the first line of the chunk region | No blank line before it |
| `id=` names the chunk | Matches the `id=` in the fence |
| `src=` is the path to the source document | Relative to the repo root |
| Never hand-edit | The tool writes and reads it; humans don't touch it |
| Regex to parse it | `^# lit:chunk id=([\w-]+) src=(.+)$` |

### Example output file

```python
# lit:chunk id=parse-header src=lit/format.md
import re

FENCE_RE = re.compile(r'^```(\w+)(.*)$')

# lit:chunk id=parse-body src=lit/format.md
def parse_document(path):
    ...
```

---

## 5. Document model

```
Document
  nodes: list[Prose | Chunk]

Prose
  text: str          # raw markdown bytes, verbatim

Chunk
  id:   str          # required
  file: str | None   # tangle target path
  lang: str          # language tag
  body: str          # code body, no fence lines, trailing newline preserved
  refs: list[str]    # ids found via <<id>> in the body
```

Order in `nodes` reflects source order — this is what the merge driver diffs.

---

## 6. Round-trip invariant

`parse → serialise` must be byte-for-byte identity when no bodies are changed.
Any change to Prose nodes is forbidden by the serialiser — they are written
verbatim. Any change to a Chunk's body is reflected in the output; everything
else about the fence (language, attributes, closing fence) is reproduced
exactly as parsed.
