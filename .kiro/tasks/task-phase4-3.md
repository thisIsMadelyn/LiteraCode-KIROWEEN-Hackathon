# task-phase4-3: The format spec written in the format, tangling to the parser

## Status
- [ ] Done

## What this is
The self-referential proof. `lit/format.md` is both the specification of the
literacode format *and* a literate document that tangles to the parser
implementation. Reading the document teaches you the format; running
`lit tangle lit/format.md` produces the parser.

This is a strong demo artifact — it is the best possible answer to "does the
tool work?" It is also on the cut list if time runs short.

## Prerequisite
task-phase4-1 must be done. `lit/format.md` is created there — this task
turns it into something worth reading.

## How to execute

### 1. Rewrite `lit/format.md` as a proper literate document

The document should read as a specification, not as code with comments. Structure:

```markdown
# The literacode format

## Overview
A literate document is ordinary markdown...

## Chunk attributes
A fenced code block becomes a chunk when its info string contains `id=`.

The attribute syntax is:
    ```python id=<id> [file=<path>]
    ```
...

## The parser

We implement a line-by-line state machine. The parser has two states:
`PROSE` and `CHUNK`.

```python id=parser-states file=src/literacode/parser.py
from enum import Enum, auto
class State(Enum):
    PROSE = auto()
    CHUNK = auto()
```

The main parsing loop...
```

### 2. Verify it tangles correctly

```bash
lit tangle lit/format.md
diff src/literacode/parser.py <(lit tangle lit/format.md --stdout)
```

(Add `--stdout` mode to tangle if useful for testing.)

The output must match the current parser exactly (modulo sync markers).

### 3. Verify the full test suite still passes

After regenerating from the literate source:
```bash
pytest
```

## Done when
- `lit/format.md` reads as a coherent specification and implementation
- `lit tangle lit/format.md` regenerates the parser correctly
- The full test suite passes on the generated code
