---
inclusion: always
---

# Stack and conventions

## Stack

| Part | Choice |
|---|---|
| CLI, parser, merge driver | Python 3.11+ |
| Conflict UI (`lit resolve`) | React, served locally by the CLI |
| Tests | pytest |
| Lint / format | ruff |
| Packaging | a single installable console script `lit` |

Target platforms: Linux and macOS. Windows is not tested and not claimed.

## Commands

| Command | Does |
|---|---|
| `lit tangle` | document → `.py` files on disk, with sync markers in comments |
| `lit stitch` | edited `.py` files → chunks in the document |
| `lit install` | writes `.gitattributes` (`*.md merge=literacode`) and registers the driver in `.git/config` |
| `lit merge %O %A %B %P` | the merge driver entry point git calls |
| `lit resolve` | serves the local conflict UI |

## Merge driver contract

- Exit 0 = merged cleanly. Exit 1 = conflicts remain.
- The driver writes its result to the `%A` path, as git expects.
- Structural resolution is attempted **before** any agent call. An agent call
  happens only for a chunk edited on both sides.
- Never invent chunk content. If the structure is ambiguous, conflict rather than guess.

## Hard scope limits

Do not implement, propose or scaffold any of these:

- weave / HTML / PDF output
- an IDE extension of any kind
- a daemon or file watcher
- references across multiple `.md` files
- any language other than Python in tangled output
- auth, deployment, or multi-user features in the UI

If a task seems to need one of these, stop and say so instead of building it.

## Correctness rules

- The round trip `tangle` → edit → `stitch` must be lossless. Any change that
  risks that is wrong, however convenient.
- Chunk identity is explicit (the id in the fence attributes), never inferred
  from position or content similarity.
- Prefer failing loudly over writing a half-synced file.
