# task-phase1-1: Parser — document → model (prose sections, chunks with ids, references)

## Status
- [ ] Done

## What this is
The foundation of everything. A Python function that reads a `.md` file and
returns a structured model: an ordered list of **prose sections** and **chunks**,
where each chunk has an explicit id, a target file, a language, and a body.

No parser = no tangle, no stitch, no merge driver.

## Prerequisite
task-phase0-3 must be done. The parser is written against the agreed grammar,
not a guess.

## How to execute

### 1. Create the project skeleton

```
src/
  literacode/
    __init__.py
    model.py      ← data classes
    parser.py     ← parse_document()
pyproject.toml
```

`pyproject.toml` minimum:
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "literacode"
version = "0.1.0"
requires-python = ">=3.11"

[project.scripts]
lit = "literacode.cli:main"

[tool.ruff]
line-length = 88
```

Install in editable mode: `pip install -e .`

### 2. Define the model (`model.py`)

```python
from dataclasses import dataclass, field

@dataclass
class Prose:
    text: str          # raw markdown, including leading/trailing newlines

@dataclass
class Chunk:
    id: str
    file: str | None   # target output path; None if not a tangle target
    lang: str
    body: str          # raw code, no fence lines
    refs: list[str]    # chunk ids referenced via <<id>> inside the body

@dataclass
class Document:
    nodes: list[Prose | Chunk] = field(default_factory=list)
```

### 3. Write the parser (`parser.py`)

State machine over lines:
- Outside a fence → accumulate prose
- Fence open line (` ``` ` with attributes) → parse attributes, switch to chunk mode
- Inside a fence → accumulate body lines
- Fence close line (` ``` ` alone) → emit Chunk, switch back to prose mode

Attribute parsing (from the grammar decided in task-phase0-3):
```python
import re
FENCE_RE = re.compile(r'^```(\w+)(.*)$')
ATTR_RE  = re.compile(r'(\w+)=(\S+)')
```

Reference scanning inside body:
```python
REF_RE = re.compile(r'<<([\w-]+)>>')
```

Edge cases to handle:
- A plain ` ```python ` fence with no `id=` → emit as Prose (not a Chunk)
- An empty document → returns `Document(nodes=[])`
- Nested fences are not supported; the first closing ` ``` ` ends the chunk

### 4. Write a smoke test

`tests/test_parser.py` with one round-trip fixture: a short document with one
prose section and one chunk. Assert the model fields exactly.

## Done when
- `parse_document(path: Path) -> Document` exists and is importable
- The smoke test passes: `pytest tests/test_parser.py`
- A plain markdown file with no chunk attributes parses without error
