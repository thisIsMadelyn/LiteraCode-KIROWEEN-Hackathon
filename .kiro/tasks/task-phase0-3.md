# task-phase0-3: Format grammar decided and written down

## Status
- [ ] Done

## What this is
Before writing a single line of parser code, the chunk attribute syntax must be
agreed on and documented. This is a design decision, not an implementation task.
`SPEC-SEEDS.md` calls it out explicitly: "Ask me about the marker format before
designing it — it is the part I most expect to get wrong."

## How to execute

### Decision: chunk fence attributes

A literate chunk is a fenced code block with extra attributes. You need to
decide the exact syntax. The main question is the attribute format — GitHub
Flavored Markdown only supports a single info string (e.g. ` ```python `), but
you need at minimum:

| Attribute | Purpose | Example value |
|---|---|---|
| `id` | chunk identity (used by stitch, merge driver) | `parse-header` |
| `file` | target output path for tangle | `src/literacode/parser.py` |
| `lang` | language for syntax highlighting | `python` |

**Option A — space-separated key=value after the language:**
```
```python id=parse-header file=src/literacode/parser.py
```

**Option B — curly-brace attribute block (Pandoc style):**
```
```python {#parse-header file="src/literacode/parser.py"}
```

**Option C — separate HTML comment on the next line:**
```
```python
<!-- chunk: id=parse-header file=src/literacode/parser.py -->
```

Recommendation: **Option A**. Simplest to parse with a regex, no external
dependency, human-readable, and does not break GitHub rendering (GitHub ignores
unknown tokens after the language tag).

### Decision: sync marker format

When `lit tangle` writes a `.py` file it must embed a marker so `lit stitch`
can find its way back. The marker must:
- Be valid Python (a comment)
- Name the source document and the chunk id
- Be tamper-evident (so an accidental edit is detectable)

Proposed format:
```python
# lit:chunk id=parse-header src=lit/format.md
```

One marker at the start of each chunk region in the generated file.

### Write it down

Once decided, document the grammar in one of:
- The `format` spec design doc (preferred — this is where it belongs)
- A short `lit/format-grammar.md` file if the spec isn't started yet

## Done when
- The attribute syntax is chosen and written down somewhere reviewable
- The sync marker format is chosen and written down
- No code has been written yet that assumes a different format
