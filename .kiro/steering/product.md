---
inclusion: always
---

# literacode — what this project is

## The thesis

Literate programming (Knuth, WEB, 1984) did not die because it was a bad idea.
It died because **it does not survive a team**. Git sees a literate document as
lines of text, not as a structure of named chunks and narrative. Two people, one
document, and the merge destroys it. That is why the paradigm survived only as
solo tooling and nowhere as a team practice.

literacode fixes it at the level where it broke: **the merge**.

## What it is

A literate markdown format plus a git merge driver that merges at the level of
**named code chunks and prose sections**, not lines.

- The markdown document is the source of truth.
- `lit tangle` generates ordinary `.py` files on disk.
- `lit stitch` brings edits made in those `.py` files back into the document.
- The merge driver resolves structurally. Where it genuinely cannot, a local web
  UI (`lit resolve`) presents the conflict with the surrounding prose as context,
  and an agent proposes a resolution as a reviewable diff.

## The two cases that matter

**Case A — the silent win.** One author reorders the narrative (moves a chunk for
pedagogical reasons) while another edits that chunk's body from the IDE.
Line-based git produces garbage; literacode merges cleanly, because reordering
and editing are orthogonal operations on an object that has an identity.

**Case B — the real conflict.** Both authors edit the same chunk body. The driver
does not guess. It hands the decision to a human, with context.

## What it is not

- Not a commercial product.
- Not a replacement for Jupyter, Quarto or Org-mode.
- Not an IDE plugin. Tangled output is valid Python; every IDE already supports it.

## Non-negotiable

**The agent never writes silently.** Every agent-produced resolution is a diff a
human approves. Structure resolves first; the agent is the fallback, never the trick.
