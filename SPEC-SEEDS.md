# Spec seeds

Do **not** paste these into files. Paste each one into Kiro's Specs panel as the
opening prompt for a new spec, and let Kiro drive the requirements → design →
tasks flow with you.

That interactive flow is what the judges score under "Technological
Implementation". A hand-written `requirements.md` dropped into `.kiro/specs/`
shows nothing.

Create them in order. `format` must reach its design phase before `merge-driver`
starts, because the merge driver operates on the document model the format spec
defines.

---

## 1. `format`

> Build the literate markdown format for literacode and its round trip.
>
> A literate document is ordinary markdown. Fenced code blocks may carry
> attributes: a chunk id, a target file path, and a language. A chunk body may
> reference another chunk by id, so the narrative order and the machine order can
> differ. A plain markdown file with no attributes must still parse without error.
>
> I need:
> - a parser from document to a model of ordered prose sections and identified chunks
> - `lit tangle`: model to `.py` files on disk, with sync markers in comments so the
>   reverse direction is possible
> - `lit stitch`: edited `.py` files back into the chunk bodies of the document
> - the round trip must be lossless, and I want that as an executable property, not a hope
>
> The document is the source of truth. The generated files are not.
>
> Ask me about the marker format before designing it — it is the part I most
> expect to get wrong.

---

## 2. `merge-driver`

> Build the git merge driver that merges literate documents structurally.
>
> Git calls it with three versions of a document: base, ours, theirs. It parses
> all three into the document model from the `format` spec and merges at the level
> of prose sections and identified chunks, not lines.
>
> The case that must work: one side reorders chunks in the narrative, the other
> side edits a chunk body. Line-based git mangles this. Structurally it is two
> orthogonal operations and must merge clean.
>
> The case that must not be guessed: both sides edit the same chunk body. Then the
> driver leaves a conflict and exits non-zero. It never invents content.
>
> Also needed: `lit install`, which writes `.gitattributes` and registers the
> driver in `.git/config`.
>
> I want the merge rules enumerated as an explicit table of cases before any code
> is written — what changed on each side, and what the result is. If a case is
> genuinely ambiguous, it conflicts.

---

## 3. `resolve-ui`

> Build `lit resolve`: a local web UI for the conflicts the driver refuses to guess.
>
> The CLI serves a React app on localhost. For each conflicted chunk it shows base,
> ours and theirs side by side, with the prose immediately before and after the
> chunk from each version — the prose is the authors' statement of intent, so it is
> the context that makes the decision possible.
>
> A conflict-resolver agent proposes a merged body from that context. Its output is
> always a diff the human approves, rejects, or edits. It never writes to disk
> itself.
>
> On accept, the resolution is written into the document and the conflict clears.
>
> No auth, no deployment, no multi-user. Local only. This is a mergetool, not a
> web app.
>
> This UI is what a judge will open and click through, so the clarity of the
> three-way view matters as much as the logic behind it.
