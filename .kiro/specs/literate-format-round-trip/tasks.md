# Implementation Plan: literate-format-round-trip

## Overview

The design changes an existing implementation (`lit/format.md`, `lit/tangle.md`, `lit/stitch.md`, `lit/cli.md`) and adds two literate sources, `lit/markers.md` and `lit/fsio.md`. The implementation language is Python 3.11+, as the design specifies.

**Working mode: literate-first. The bootstrap exception is over.** No task edits `src/literacode/*.py` by hand. Code changes are made in documents under `lit/`, then `lit tangle lit/*.md` regenerates `src/`. Sync markers are never edited by hand. Files that are not generated (`pyproject.toml`, `tests/`, `.githooks/pre-commit`) are edited directly.

**Migration order (design, "Migration of the marker format"):**

1. Stitch pending `.py` edits with the old tool and commit (task 2).
2. Edit `lit/*.md` only (task 3).
3. `lit tangle lit/*.md` once with the old tool, then a second time with the new tool (tasks 4.1, 4.2).
4. `lit tangle --check lit/*.md` exits 0, then run the tests (task 4.3).

**Scope limits.** No weave, HTML or PDF output. No IDE extension. No daemon or file watcher. No references across several `.md` files. No tangled language other than Python. If a task seems to need one of these, stop and report it.

**Property tests are not marked optional.** Requirement 8 requires them. Each runs at least 100 examples (`max_examples=200`). Example-based tests are optional.

## Tasks

- [ ] 1. Confirm design decisions and add the test dependency
  - [ ] 1.1 Get the user's confirmation of decisions D1 to D13 before any implementation
    - Decisions D1 to D13 in the "Additional decisions" table of `design.md` are proposals. They are not covered by `requirements.md` or by the answers to its open questions, and they are pending user confirmation.
    - Present D1 to D13 to the user. Do not start tasks 2 to 13 until each decision is accepted, changed or rejected.
    - For each accepted decision, add it to `requirements.md` as an acceptance criterion or as a resolved open question. Update `design.md` for any decision that was changed or rejected, and adjust the tasks that depend on it.
    - _Requirements: 1.5, 2.2, 4.4, 4.5, 4.10, 6.10, 7.5, 7.6_

  - [ ] 1.2 Add Hypothesis as a development dependency
    - Edit `pyproject.toml` directly (it is not a generated file). Add `[project.optional-dependencies] dev = ["pytest", "hypothesis>=6.100", "ruff"]`.
    - Keep `dependencies = []`. Hypothesis is not a runtime dependency.
    - Install with `pip install -e ".[dev]"`.
    - _Requirements: 8.8_

- [ ] 2. Migration step 1: stitch pending edits with the old tool
  - [ ] 2.1 Stitch every pending `.py` edit into its document and commit
    - Run `git status` and check whether any `src/literacode/*.py` file differs from a fresh `lit tangle` of its document, using the old tool (`lit tangle --check lit/*.md`).
    - For each edited file, run the old `lit stitch <file.py>`, then `lit tangle lit/*.md`, and confirm that `--check` exits 0.
    - Commit the result, so that the work tree is clean. After task 4 the old marker is rejected, and `git restore src` must return to a working tool if the migration fails.
    - _Requirements: 10.2, 10.6_

- [ ] 3. Edit the literate sources (documents under `lit/` only)
  - [ ] 3.1 Update `lit/format.md`: model, parser, serialiser and the format reference
    - Change the chunks that tangle to `model.py`, `parser.py` and `serialiser.py`.
    - `model.py`: `Chunk` gets `_fence`, `_open_eol`, `_close` (all with defaults) next to `_fence_attrs`. Add `attrs()`, `language()`, `lf_text()`, `lines()` and `split_lines()`. Make `_fence_attrs` and the raw fields take part in equality. Check that `merge.py` does not rely on the old `compare=False`.
    - `parser.py`: add `ParseError(message, line)`. Split lines on `\n` and `\r\n` only (D1). Validate the `id` value against `[\w-]+` and reject a repeated `id=` token. Raise on an unterminated chunk fence, on a duplicate id (naming both lines), and on a lone `\r` in a chunk body. `parse_document` decodes strictly and reads with `newline=""`. Keep an unterminated plain fence as prose. Fix the closing fence rule for tags such as `c++`.
    - `serialiser.py`: add `SerialiseError`. Check every chunk before writing anything (no final line ending, a body line that closes the fence, missing `id=` in the attribute text). Write the stored `_fence`, `_open_eol` and `_close`.
    - Rewrite the format specification sections: the `begin`/`end` marker grammar and one section per open question (Q1 to Q12), each with the rule and at least one example. Document D1 to D13 as they were confirmed in task 1.1.
    - Reword any docstring or prose chunk in this document that quotes the old marker, so that no generated body has a line starting with `# lit:` after whitespace (D3).
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 10.1, 10.5_

  - [ ] 3.2 Create `lit/markers.md` (tangles to `src/literacode/markers.py`)
    - Chunks for `BEGIN_RE`, `END_RE`, `REF_RE`, `MARKER_PREFIX`, `Line`, `Region`, `MarkerError`, `classify_line`, `read_regions` and `region_body`, with prose that explains each rule.
    - `classify_line`: a line whose text after leading whitespace starts with `# lit:` must match the begin or end grammar, otherwise `MarkerError`. The old `# lit:chunk` marker gets the message "obsolete marker; run lit tangle" (Q5, Q11).
    - `read_regions`: stack machine. Check indentation nesting, matching ids on end markers, an indent prefix on content lines, rejection of reference lines (D5), blank lines outside regions ignored and other text outside regions an error (Q6, Q7), rejection of `\r`, and an error for an open region at the end of the text. Errors carry 1-based line numbers.
    - `region_body`: nested regions become `<<id>>` lines at their relative indentation. The `noeol` flag removes the final `\n`, and `noeol` on an empty region is an error (Q8).
    - Add the file header chunk for `markers.py`, following the pattern of the other documents.
    - _Requirements: 4.3, 4.4, 6.2, 6.5, 6.7, 7.1, 7.2, 7.5_

  - [ ] 3.3 Create `lit/fsio.md` (tangles to `src/literacode/fsio.py`)
    - Chunks for `FsError`, `find_repo_root`, `doc_ref`, `norm_ref` and `atomic_write_all`.
    - `find_repo_root` returns the nearest ancestor that contains `.git`, else raises `FsError` that names the start path and the `--root` hint (D9). `doc_ref` returns a POSIX path relative to the repository root, and rejects whitespace and documents outside the root (D10).
    - `atomic_write_all(files)` stages every file as a temporary file in the target directory (flush, fsync, copy the mode of an existing target), then calls `os.replace` for each. On any exception it removes all remaining temporary files. It skips a file whose content already equals the new text.
    - _Requirements: 4.7, 4.13, 4.14, 6.11, 6.12, 9.5_

  - [ ] 3.4 Update `lit/tangle.md`
    - Add `TangleError(chunk)`, `render_text(doc, doc_ref)`, `render`, `tangle` and `stale`, with `render_text` as the pure core.
    - Expand references on whole-line `REF_RE` matches only (D2). Indent nested regions cumulatively, and leave empty lines unindented (D4). Emit the begin marker, the body, and the end marker with ` noeol` when the last line has no ending. Write `file=` chunks that are also referenced at top level and nested (Q10). Join top-level regions with two empty lines. Write LF only.
    - Raise `TangleError` for an unknown reference (naming both chunks), a cycle (listing the ids), an absolute or escaping `file=` (also re-check the resolved path against the output root), a non-Python `file=` chunk (accept `python`, `py`, and `lang=`; D8), a body line starting with `# lit:` after whitespace (D3), `\r` in a body, and whitespace in `doc_ref`. Nothing is written until all checks pass.
    - Reword the `tangle-header` docstring so that it no longer quotes the old marker.
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 4.11, 4.12, 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ] 3.5 Update `lit/stitch.md`
    - Add `StitchError(messages)`, `stitch_documents(doc, generated, doc_ref)` and `stitch(py_paths, doc_path, *, out_root, repo_root)`, with `stitch_documents` as the pure core.
    - Phases: read regions; check `doc=` (compare normalised paths); check ids; check structure (top-level ids equal the document's chunks for that file in order, and every nested child list equals the reference list of its body; D6); collect edits (one distinct edit wins, two or more raise a conflict naming the chunk and files; Q4); restore line endings with `difflib.SequenceMatcher(autojunk=False)` as the design specifies (Q12); build the new model.
    - Collect errors per file and raise one `StitchError`. Write the document once with `atomic_write_all`, and only if its text changed. Never edit a generated file.
    - Reword the `stitch-header` docstring so that it no longer quotes the old marker.
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 7.1, 7.2, 7.5, 7.6_

  - [ ] 3.6 Update `lit/cli.md`
    - `lit tangle [--check] [--out DIR] [--root DIR] DOC...`: parse and render every document first, write only when all succeed, print one generated path per line, report a missing file on standard error with exit 1, report parse or tangle errors as `lit tangle: <file>[:<line>]: <message>` with exit 1. Two documents that claim one target is an error (D11). `--check` writes nothing, prints each absent or differing path, and exits 1 if any.
    - `lit stitch [--out DIR] [--root DIR] PY... DOC`: the last positional is the document (D12). Print `stitched <py> -> <doc>` per file on success. Errors go to standard error with exit 1.
    - Root handling per D9: nearest `.git` ancestor, `--root` override, `--out` for the output root.
    - _Requirements: 7.3, 7.4, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 10.3_

- [ ] 4. Migration steps 3 to 5: regenerate `src/` and check it
  - [ ] 4.1 First tangle with the old tool
    - Run `lit tangle lit/*.md`. The old tool writes the new code, but still with old-style markers.
    - If `src/` is broken afterwards, run `git restore src` and fix the documents from task 3. Do not patch `src/`.
    - _Requirements: 10.1_

  - [ ] 4.2 Second tangle with the new tool
    - Run `lit tangle lit/*.md` again. The new tool rewrites every file with `begin`/`end` markers, including the new `markers.py` and `fsio.py` and `__init__.py`.
    - Confirm that every `src/literacode/*.py` starts with a begin marker whose `doc=` names a document under `lit/`.
    - _Requirements: 10.1_

  - [ ] 4.3 Check the regenerated tree
    - Run `lit tangle --check lit/*.md` and require exit 0 with no stale paths.
    - Run `ruff check`. Fix findings in the documents and re-tangle, never in `src/`.
    - _Requirements: 10.2, 10.3, 10.4_

- [ ] 5. Update existing tests for the new formats
  - [ ] 5.1 Update `tests/test_tangle.py`, `tests/test_stitch.py` and `tests/test_round_trip.py`
    - Replace `# lit:chunk id=...` assertions with `begin`/`end` markers. Replace the fake marker in the unknown-id test with a `begin`/`end` pair. Keep the three round-trip examples and pass `repo_root=tmp_path`.
    - _Requirements: 4.3, 4.4, 6.5, 6.6_

  - [ ] 5.2 Update `tests/test_parser.py`
    - Change the unterminated chunk fence expectation from "prose" to `ParseError`. Add cases for duplicate ids, invalid ids, a lone `\r`, invalid UTF-8, and a tag such as `c++`.
    - _Requirements: 1.6, 1.7, 2.4, 2.5, 2.6_

- [ ] 6. Follow-ups: D13 and the pre-commit hook
  - [ ] 6.1 Handle `ParseError` in the merge driver, `merge.py` and `resolve.py` (D13)
    - Edit the documents that tangle to `merge.py`, `driver.py` and `resolve.py` (`lit/merge.md`, `lit/resolve.md`, and the document that holds `driver.py`; find them through the sync markers). Treat `ParseError` as a failed merge: exit 1, a message on standard error, no crash. Then run `lit tangle lit/*.md` and `lit tangle --check lit/*.md`.
    - Keep `tests/test_merge.py`, `tests/test_driver.py` and `tests/test_resolve.py` passing without changes to their `Chunk(...)` calls. Add one test per module for the `ParseError` case, in the same files.
    - _Requirements: 2.4, 2.6, 9.6_

  - [ ] 6.2 Update the pre-commit hook message
    - Edit `.githooks/pre-commit` directly (it is not generated). Change the message from `lit stitch <file.py>` to `lit stitch <file.py> <doc.md>`, and keep the `lit tangle --check` call.
    - _Requirements: 9.2, 10.2_

- [ ] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Property test infrastructure
  - [ ] 8.1 Create `tests/strategies.py`
    - Export `SETTINGS = settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])`.
    - Generators, building models first and serialising them so that every document is valid: unique ids from `[a-z][\w-]*`; 1 to 20 prose sections and 1 to 20 chunks; at least one plain fenced block, some containing chunk-fence lookalikes; `file` from `pkg/a.py`, `pkg/b.py`, `x/y/c.py` or none; references forming a DAG, with one chain of depth 3 to 5, multiple references to one chunk, and reference indentation from `""`, 2 spaces, 4 spaces and a tab; some `file=` chunks that are also referenced.
    - Body lines without `\r`, `# lit:` prefixes or reference syntax unless a property injects them, including blank, whitespace-only, tab, trailing-blank and non-ASCII lines. Line endings per document and per chunk from LF, CRLF and per-line mixes, and some documents with no final line ending.
    - Separate generators: unrestricted line soup (Properties 1 and 3); valid-Python-by-construction bodies (Property 10); model-level bodies with no final line ending (Properties 7, 9, 13).
    - Edit helpers: assign new bodies to a subset of chunks and write each into every region of the chunk at its indentation (D7); a variant that edits chosen regions only (Property 18). Damage helpers, one per kind in Property 19. A text-level permutation helper for chunk nodes.
    - _Requirements: 8.1, 8.8_

  - [ ] 8.2 Write the generator self-test in `tests/test_strategies.py`
    - Check, over a sample, that documents have 1 to 20 prose sections and chunks, at least one plain fence, a reference chain of depth 3 or more, chunks with and without `file`, and all three line-ending styles.
    - _Requirements: 8.1_

- [ ] 9. Property tests for the format (one file per property under `tests/properties/`)
  - [ ] 9.1 `tests/properties/test_p01_parse_serialise_identity.py`
    - **Property 1: Parse then serialise is the identity**
    - Uses the line-soup and document generators. Each test carries the comment `# Feature: literate-format-round-trip, Property 1: ...`.
    - **Validates: Requirements 1.2, 1.4, 1.5, 1.6, 2.7, 3.1, 3.2, 3.3, 3.5**

  - [ ] 9.2 `tests/properties/test_p02_serialise_parse_identity.py`
    - **Property 2: Serialise then parse is the identity on models**
    - **Validates: Requirements 2.1, 2.3, 3.6**

  - [ ] 9.3 `tests/properties/test_p03_no_chunks_without_id.py`
    - **Property 3: Documents without chunk attributes have no chunks**
    - **Validates: Requirements 1.1, 1.3**

  - [ ] 9.4 `tests/properties/test_p04_identity_by_id.py`
    - **Property 4: Chunk identity follows the id attribute only**
    - **Validates: Requirements 2.2**

  - [ ] 9.5 `tests/properties/test_p05_invalid_documents.py`
    - **Property 5: Invalid documents are rejected with a position**
    - Covers duplicate id, empty or invalid id, truncation inside a chunk, lone `\r` and invalid UTF-8 through `parse_document`.
    - **Validates: Requirements 1.7, 2.4, 2.5, 2.6**

  - [ ] 9.6 `tests/properties/test_p06_local_body_change.py`
    - **Property 6: Changing one body changes only that chunk**
    - **Validates: Requirements 3.4**

  - [ ] 9.7 `tests/properties/test_p07_unserialisable_models.py`
    - **Property 7: Unserialisable models are rejected whole**
    - **Validates: Requirements 3.7**

- [ ] 10. Property tests for tangle
  - [ ] 10.1 `tests/properties/test_p08_tangle_structure.py`
    - **Property 8: Tangled output has the structure the document defines**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.5, 4.12, 5.1, 5.2, 5.3**

  - [ ] 10.2 `tests/properties/test_p09_tangle_deterministic_exact.py`
    - **Property 9: Tangle is deterministic, LF-only and exact**
    - **Validates: Requirements 4.7**

  - [ ] 10.3 `tests/properties/test_p10_generated_python_valid.py`
    - **Property 10: Generated Python is valid**
    - Parses every generated file with `ast.parse`.
    - **Validates: Requirements 4.6**

  - [ ] 10.4 `tests/properties/test_p11_narrative_order.py`
    - **Property 11: Narrative order does not change machine order across files**
    - **Validates: Requirements 5.4, 5.5**

  - [ ] 10.5 `tests/properties/test_p12_tangle_errors.py`
    - **Property 12: Tangle errors are loud and write nothing**
    - Covers a missing reference, a cycle, an absolute or escaping `file=`, a non-Python `file=` chunk and a body line starting with `# lit:`.
    - **Validates: Requirements 4.8, 4.9, 4.10, 4.11**

- [ ] 11. Property tests for stitch and the round trip
  - [ ] 11.1 `tests/properties/test_p13_tangle_stitch_identity.py`
    - **Property 13: Tangle then stitch without edits is the identity**
    - Includes line-ending mixes and models with a body that has no final line ending.
    - **Validates: Requirements 6.2, 6.4, 8.2**

  - [ ] 11.2 `tests/properties/test_p14_fixed_point.py`
    - **Property 14: Edit, stitch and re-tangle is a fixed point**
    - **Validates: Requirements 6.1, 8.3**

  - [ ] 11.3 `tests/properties/test_p15_locality.py`
    - **Property 15: Stitch changes only the edited chunk bodies**
    - **Validates: Requirements 6.3, 8.4**

  - [ ] 11.4 `tests/properties/test_p16_idempotence.py`
    - **Property 16: Stitching twice equals stitching once**
    - **Validates: Requirements 8.5**

  - [ ] 11.5 `tests/properties/test_p17_confluence.py`
    - **Property 17: Body edits and reordering commute**
    - **Validates: Requirements 6.5, 8.6**

  - [ ] 11.6 `tests/properties/test_p18_multiple_expansions.py`
    - **Property 18: One edited expansion wins, different edits conflict**
    - **Validates: Requirements 6.8**

  - [ ] 11.7 `tests/properties/test_p19_damage_detected.py`
    - **Property 19: Damage is detected and nothing is written**
    - Covers marker deletion, duplication and alteration, unknown or swapped ids, a wrong `doc=`, a moved nested region, text outside regions, a hand-typed reference, reduced indentation and the old marker. Includes damage in one of several generated files.
    - **Validates: Requirements 6.5, 6.6, 6.7, 6.9, 6.10, 7.1, 7.2, 7.5, 7.6, 8.7**

- [ ] 12. Example, CLI and fault-injection tests
  - [ ]* 12.1 Write CLI tests in `tests/test_cli_format.py`
    - `lit tangle` prints one path per line, creates missing directories, and rewrites only differing files. `--check` exits 1 with the stale paths and writes nothing. A missing file and an unprocessable file print to standard error, exit 1, and write nothing. `lit stitch PY DOC` runs end to end through `main`. Two documents that claim one target fail (D11).
    - _Requirements: 4.13, 7.3, 7.4, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 10.3_

  - [ ]* 12.2 Write file-system tests in `tests/test_fsio.py`
    - Repository-root discovery with and without `.git`, and `--root`. `doc_ref` normalisation, whitespace and outside-root cases. `atomic_write_all` with `os.replace` and the temporary-file write patched to fail: the original is unchanged and no temporary file remains.
    - _Requirements: 4.14, 6.11, 6.12_

  - [ ]* 12.3 Write marker and format examples in `tests/test_markers.py`
    - The exact generated text for the example in the design's "Data Models" section. A zero-byte file, a prose-only document, an empty chunk, a `noeol` marker, the old marker rejected with its message, and a stale generated file rejected by the structure check.
    - _Requirements: 1.2, 4.4, 7.1_

- [ ] 13. Self-hosting checks
  - [ ] 13.1 Write `tests/test_self_hosting.py`
    - `lit tangle --check lit/*.md` exits 0. Every `src/literacode/*.py` begins with a begin marker whose `doc=` names a document under `lit/`. Tangle followed by stitch over `lit/*.md`, with no edits, leaves every document byte-identical.
    - _Requirements: 10.1, 10.2, 10.6_

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Run `ruff check`, `pytest`, and `lit tangle --check lit/*.md`. Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional. Property tests are not optional because Requirement 8 requires them.
- Task 1.1 is a gate. D1 to D13 are proposals pending user confirmation.
- `src/literacode/*.py` is never edited by hand. If a generated file looks wrong, fix the document under `lit/` and re-tangle.
- Each property test runs at least 100 examples (`max_examples=200` in `tests/strategies.py`).
- Out of scope: weave, HTML or PDF output, an IDE extension, a daemon or file watcher, references across several `.md` files, and any tangled language other than Python.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6"] },
    { "id": 3, "tasks": ["4.1"] },
    { "id": 4, "tasks": ["4.2"] },
    { "id": 5, "tasks": ["4.3"] },
    { "id": 6, "tasks": ["5.1", "5.2", "6.1", "6.2", "8.1"] },
    { "id": 7, "tasks": ["8.2", "9.1", "9.2", "9.3", "9.4", "9.5", "9.6", "9.7", "10.1", "10.2", "10.3", "10.4", "10.5", "11.1", "11.2", "11.3", "11.4", "11.5", "11.6", "11.7", "12.1", "12.2", "12.3", "13.1"] }
  ]
}
```
