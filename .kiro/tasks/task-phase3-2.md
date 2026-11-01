# task-phase3-2: Three-way chunk view with surrounding prose

## Status
- [ ] Done

## What this is
The core UI component. For each conflict, the user sees base / ours / theirs
side by side, plus the prose immediately before and after the chunk from each
version. The prose is what makes the decision possible — it is the authors'
stated intent.

## Prerequisite
task-phase3-1 (server running and API returning conflict data) must be done.

## How to execute

### 1. API payload shape

The `/api/conflicts` endpoint must return enough data to render the view:

```json
[
  {
    "chunk_id": "parse",
    "lang": "python",
    "base":   { "body": "...", "prose_before": "...", "prose_after": "..." },
    "ours":   { "body": "...", "prose_before": "...", "prose_after": "..." },
    "theirs": { "body": "...", "prose_before": "...", "prose_after": "..." }
  }
]
```

`prose_before` / `prose_after`: the nearest prose node before and after the
chunk in each respective version of the document. Can be empty string if none.

### 2. React component: `ConflictView.tsx`

Layout: three columns (base | ours | theirs). Each column shows:
1. **Prose before** — rendered as markdown (use a small library like
   `react-markdown` or just render in a `<pre>`)
2. **Code block** — the chunk body with syntax highlighting
   (`react-syntax-highlighter` or Prism via CDN)
3. **Prose after** — same treatment as prose before

Below the three columns: a text area pre-filled with the `ours` body where
the human can edit the resolution.

Accessibility: each column has a `<h2>` label (Base / Ours / Theirs).
Keyboard navigation between columns must work (tab order is sensible).

### 3. Diff highlighting (optional but high-value)

Highlight lines that differ between ours/theirs and base. A simple line-diff
in the frontend (compare arrays of lines, mark added/removed/changed) is
enough. No dependency on a diff library is required.

### 4. Multi-conflict navigation

If there are multiple conflicts, show them one at a time with
Prev / Next navigation and a counter ("Conflict 1 of 3").

Show a summary list in a sidebar or header that lets the user jump to any
conflict directly.

## Done when
- Each conflict shows base / ours / theirs with prose context in three columns
- The resolution text area is pre-filled and editable
- Multi-conflict navigation works
- The page is readable at 1280px wide without horizontal scroll
