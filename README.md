# literacode

Literate programming did not die because it was a bad idea. It died because it
does not survive a team. Git sees a literate document as lines of text, not as
named chunks of code and the narrative around them, so two people editing one
document produce a merge that destroys it.

literacode fixes it where it broke: the merge. It is a markdown format plus a
git merge driver that merges at the level of named code chunks and prose, not
lines.

- The markdown document is the source of truth.
- `lit tangle` writes ordinary `.py` files from it. Every IDE already supports those.
- `lit stitch` brings edits made in the `.py` files back into the document.
- The merge driver merges chunks by id. When it cannot, `lit resolve` opens a
  local page that shows base, ours and theirs with the surrounding prose, and
  an agent can propose a resolution as a diff for a human to accept or reject.

**The agent never writes silently.** A proposal only reaches the document after
a person puts it in the resolution box and presses Resolve. Structure resolves
first; the agent is the fallback.

## 60-second quickstart

Needs Python 3.11+ and git. Tested on Windows; the target platforms are Linux
and macOS.

```bash
pip install -e .          # from a clone of this repo; gives you the `lit` command
cd your-repo
lit install               # registers the merge driver for *.md in this repo
```

Write a document. A fenced block with an `id=` is a chunk; `file=` says where it tangles to.

````markdown
# Hello

Say hello.

```python id=greet file=hello.py
def greet(name):
    return f"Hello, {name}!"
```
````

```bash
lit tangle hello.md       # writes hello.py, with a sync marker above each chunk
# ...edit hello.py in your IDE...
lit stitch hello.py       # the edit goes back into the matching chunk of hello.md
```

Now merge. Say one branch moves the `greet` chunk up for readability and another
edits its body. Plain git conflicts. literacode merges cleanly, because
reordering and editing are different operations on an object that has an
identity.

If two branches edit the same chunk body, the driver does not guess. It leaves
conflict markers in the chunk, exits 1, and you run:

```bash
lit resolve               # serves the page for the one conflicted .md file
git add hello.md          # when the page says all conflicts are resolved
```

The page needs a one-time build: `cd ui && npm install && npm run build`.
For agent proposals, set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`. With neither,
"Get proposal" returns the ours body unchanged and says so.

## Commands

| Command | Does |
|---|---|
| `lit tangle <doc.md>... [--check]` | documents to `.py` files. `--check` writes nothing and exits 1 if a file differs from disk |
| `lit stitch <file.py>...` | edited `.py` files back into the document chunks |
| `lit install` | writes `.gitattributes` and registers the merge driver in `.git/config` |
| `lit merge %O %A %B %P` | the driver entry point git calls. Exit 0 merged, 1 conflicts remain |
| `lit resolve [doc.md] [--port N]` | serves the local conflict page |

## Rules of the format

- A chunk is a fenced block whose opening line has `id=<id>`. The id is its identity.
  It is never inferred from position or content.
- A fence without `id=` is prose, and so is everything inside it.
- `<<other-id>>` inside a chunk is expanded at tangle time. There is no escape
  for a literal one yet.
- The grammar is in [`lit/format-grammar.md`](lit/format-grammar.md).

## Where things stand

literacode is written in literacode. Everything under `src/literacode/` is
tangled from the documents in `lit/`. Edit those (or edit a `.py` and run
`lit stitch`), then run `lit tangle lit/*.md`. The pre-commit hook
(`git config core.hooksPath .githooks`) blocks a commit when `src/` has drifted
from `lit/`.

```bash
pytest                    # the test suite
```

Known limits:

- Four-backtick fences, CRLF closing fences and trailing blank lines in a
  stitched chunk body are not lossless.
- Prose is merged per slot (the prose before each chunk). If both sides edit the
  same slot, the merge conflicts with markers in the prose, and `lit resolve`
  does not show those; fix them by hand.
- The agent call has only been tested against mocked providers.
- Not implemented on purpose: HTML or PDF output, an IDE extension, a daemon or
  file watcher, references across several `.md` files, languages other than Python.

MIT licensed.
