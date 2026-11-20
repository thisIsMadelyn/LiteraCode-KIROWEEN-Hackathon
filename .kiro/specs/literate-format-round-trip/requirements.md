# Requirements Document

## Introduction

literacode treats a markdown document as the source of truth for Python code. This feature covers the literate document format and its round trip: parsing a document into a model of ordered prose sections and identified chunks, `lit tangle` (document to `.py` files with sync markers), and `lit stitch` (edited `.py` files back into chunk bodies in the document).

The round trip must be lossless, and that is stated as an executable property-based test.

### Existing state (reviewed)

The workspace already contains an implementation, authored under the bootstrap exception of the literate-first rule. `SESSION_HISTORY.md` records that the exception is over. The relevant sources are `lit/format.md` (model, parser, serialiser and the format specification), `lit/tangle.md` and `lit/stitch.md`, with tests in `tests/test_parser.py`, `tests/test_tangle.py`, `tests/test_stitch.py` and `tests/test_round_trip.py`.

Consequences for this spec:

- Every change to `src/**/*.py` is made by editing the document under `lit/` and running `lit tangle`, or by editing the `.py` and running `lit stitch`.
- The current sync marker is a single line, `# lit:chunk id=<id> src=<doc>`, which opens a region that ends at the next marker or end of file. The decided format is paired `begin`/`end` markers. Requirements 4 to 7 therefore replace the current marker, and `lit/format.md` section 4 must be updated with them.
- The current round-trip tests are single examples. Requirement 8 adds the property-based test.
- The merge driver and `lit resolve` consume the model but are out of scope here.

## Glossary

- **Document**: A markdown file that is the source of truth for the tangled code.
- **Parser**: The component that converts Document text into a Model.
- **Model**: The in-memory representation of a Document, an ordered list of Prose_Sections and Chunks.
- **Prose_Section**: A run of Document text that is not a Chunk, preserved verbatim.
- **Chunk**: A fenced code block whose opening fence carries an `id` attribute.
- **Chunk_Id**: The explicit identifier given by the `id` attribute of a Chunk. It matches `[\w-]+`.
- **Fence_Attributes**: The space-separated `key=value` tokens after the language tag on an opening fence. The recognised keys are `id`, `file` and `lang`. Unrecognised keys are preserved and otherwise ignored.
- **Target_File**: The relative path named by the `file` attribute of a Chunk.
- **Chunk_Reference**: The text `<<Chunk_Id>>` inside a Chunk body, naming another Chunk.
- **Serialiser**: The component that converts a Model back into Document text.
- **Tangler**: The component behind `lit tangle`.
- **Stitcher**: The component behind `lit stitch`.
- **Begin_Marker**: The comment line `# lit:begin doc=<path> chunk=<id>` that opens a Region.
- **End_Marker**: The comment line `# lit:end chunk=<id>` that closes a Region.
- **Region**: The text between a Begin_Marker and its matching End_Marker in a Generated_File, including nested Regions.
- **Generated_File**: A `.py` file written by the Tangler.
- **Round_Trip**: Tangle followed by an edit of Region contents followed by stitch.
- **Lossless**: A transformation is Lossless when no byte of Document content other than the edited Chunk bodies changes, and every edit made in a Generated_File appears in the Document.
- **Round_Trip_Test**: The property-based pytest test that checks the Lossless property over generated Documents.

## Requirements

### Requirement 1: Parse any markdown document

**User Story:** As a developer, I want any markdown file to parse, so that I can adopt literacode on existing documents without preparing them.

#### Acceptance Criteria

1. WHEN a markdown file containing no Fence_Attributes is provided, THE Parser SHALL produce a Model containing Prose_Sections only, SHALL produce zero Chunks, and SHALL report no error.
2. WHEN a file of zero bytes is provided, THE Parser SHALL produce a Model with zero nodes and SHALL report no error.
3. WHEN a fenced code block has no `id` attribute, THE Parser SHALL keep the block, including its opening fence line, body lines, and closing fence line, inside a Prose_Section.
4. WHEN a plain fenced block with no `id` attribute contains lines that resemble Chunk fences, THE Parser SHALL keep all of those lines inside the enclosing Prose_Section and SHALL produce zero Chunks from them.
5. THE Parser SHALL preserve the original line ending of every line it reads, whether LF, CRLF, or absent on the final line, so that serialising the Model yields output byte-identical to the input.
6. IF a plain fenced block with no `id` attribute is opened and the file ends before a closing fence, THEN THE Parser SHALL keep the unterminated block's lines inside a Prose_Section, SHALL report no error, and SHALL preserve every line byte-for-byte. (An unterminated Chunk fence is an error under Requirement 2.6.)
7. IF the input file is not valid UTF-8, THEN THE Parser SHALL fail with an error indicating the file is not valid UTF-8 and SHALL produce no Model.

### Requirement 2: Identify chunks by explicit attributes

**User Story:** As a developer, I want chunks identified by an explicit id, so that reordering or editing a chunk never changes which chunk it is.

#### Acceptance Criteria

1. WHEN an opening fence carries an `id` attribute, THE Parser SHALL produce a Chunk with that Chunk_Id, the value of the `file` attribute as Target_File when a `file` attribute is present (and no Target_File when it is absent), and the language tag from the fence.
2. THE Parser SHALL derive Chunk identity from the `id` attribute only, so that two Chunks with different `id` values are distinct Chunks even when their position, body, or `file` attribute are identical, and a Chunk keeps its Chunk_Id after it is moved to a different position in the Document.
3. THE Parser SHALL list Prose_Sections and Chunks in the order they appear in the Document, with one entry per Prose_Section and per Chunk and no entry omitted or duplicated.
4. IF two Chunks in one Document share a Chunk_Id, THEN THE Parser SHALL report an error naming the duplicated Chunk_Id and the line numbers of both Chunks, and SHALL NOT return a parsed Document.
5. IF an `id` attribute value is empty or does not match `[\w-]+` over its entire length, THEN THE Parser SHALL report an error naming the line number of the fence, and SHALL NOT return a parsed Document.
6. IF a Chunk fence is not closed before the end of the Document, THEN THE Parser SHALL report an error naming the line number of the opening fence, and SHALL NOT return a parsed Document.
7. WHEN a Chunk fence carries an unrecognised attribute, THE Parser SHALL preserve the attribute text, including its order and spacing within the fence, so that the Serialiser reproduces the fence byte-for-byte unchanged.

### Requirement 3: Serialise the model back to the document

**User Story:** As a developer, I want the model to print back to the exact document text, so that parsing never alters my document.

#### Acceptance Criteria

1. WHEN the Serialiser serialises a Model, THE Serialiser SHALL write every Prose_Section byte for byte as parsed, including line endings, trailing whitespace, and blank lines.
2. WHEN the Serialiser serialises a Model, THE Serialiser SHALL write every Chunk as its opening fence, body and closing fence, using the current body of the Chunk, and SHALL write the opening and closing fences byte for byte as parsed, including the fence attributes and the Chunk id.
3. WHEN the Serialiser serialises a Model, THE Serialiser SHALL write the Prose_Sections and Chunks in the order they appear in the Model.
4. WHEN a Chunk body has been changed after parsing, THE Serialiser SHALL write the changed body and SHALL leave every other Prose_Section and Chunk byte for byte unchanged.
5. FOR ALL Documents accepted by the Parser, serialising the Model produced by parsing SHALL produce text identical to the original Document (round-trip property). This includes the empty Document (0 bytes) and a Document with no trailing newline.
6. FOR ALL Documents accepted by the Parser, parsing the serialised Model SHALL produce a Model equal to the first Model (round-trip property).
7. IF the Model cannot be serialised byte for byte (for example a Chunk lacks the fence text needed to reproduce its opening fence), THEN THE Serialiser SHALL raise an error naming the affected Chunk id or Prose_Section position, and SHALL NOT write any partial output.

### Requirement 4: Tangle chunks into Python files

**User Story:** As a developer, I want `lit tangle` to write ordinary `.py` files, so that every IDE and tool works on my code.

#### Acceptance Criteria

1. WHEN `lit tangle` runs on a Document and no error condition in criteria 8 to 11 or 14 applies, THE Tangler SHALL write one Generated_File for each distinct Target_File and SHALL exit with code 0.
2. THE Tangler SHALL write the Chunks of one Target_File in Document order.
3. THE Tangler SHALL wrap each written Chunk in a Region, with a Begin_Marker line before the body and an End_Marker line after it.
4. THE Tangler SHALL write the Begin_Marker as `# lit:begin doc=<path> chunk=<id>` and the End_Marker as `# lit:end chunk=<id>`, each on its own line, where `<path>` is the Document path relative to the output root. (Subject to open question 9.)
5. WHEN a Chunk body contains a Chunk_Reference, THE Tangler SHALL replace the Chunk_Reference with the Region of the referenced Chunk, nested inside the Region of the referencing Chunk, at the line where the Chunk_Reference appeared and with that line's indentation applied to every line of the nested Region. (Subject to open question 2.)
6. THE Tangler SHALL produce Generated_Files that are syntactically valid Python whenever the Chunk bodies, joined as the Document specifies, are valid Python.
7. WHEN `lit tangle` runs twice on an unchanged Document, THE Tangler SHALL produce byte-identical Generated_Files.
8. IF a Chunk_Reference names a Chunk_Id that does not exist, THEN THE Tangler SHALL report an error naming the referencing Chunk and the missing Chunk_Id, SHALL write no Generated_File, SHALL leave existing files on disk unmodified, and SHALL exit with a non-zero code.
9. IF Chunk_References form a cycle, THEN THE Tangler SHALL report an error listing the Chunk_Ids in the cycle, SHALL write no Generated_File, SHALL leave existing files on disk unmodified, and SHALL exit with a non-zero code.
10. IF a Target_File path is absolute or resolves outside the output root, THEN THE Tangler SHALL report an error naming the Chunk, SHALL write no Generated_File, SHALL leave existing files on disk unmodified, and SHALL exit with a non-zero code.
11. IF a Chunk with a Target_File has a language other than Python, THEN THE Tangler SHALL report an error naming the Chunk, SHALL write no Generated_File, SHALL leave existing files on disk unmodified, and SHALL exit with a non-zero code.
12. WHEN a Chunk has no Target_File and is not referenced by any other Chunk, THE Tangler SHALL write nothing for that Chunk and SHALL NOT report an error.
13. WHEN a Target_File lies in a directory that does not exist, THE Tangler SHALL create the missing directories before writing the Generated_File.
14. IF a Generated_File cannot be written because of a filesystem error, THEN THE Tangler SHALL report an error naming the Target_File, SHALL leave no partially written Generated_File on disk, and SHALL exit with a non-zero code.

### Requirement 5: Reference expansion lets narrative order differ from machine order

**User Story:** As a developer, I want to reference one chunk from another, so that I can explain code in teaching order while the output is in machine order.

#### Acceptance Criteria

1. WHEN a Chunk contains a Chunk_Reference to another Chunk, THE Tangler SHALL replace the Chunk_Reference with the code of the referenced Chunk at the position of the Chunk_Reference, whether the referenced Chunk appears before or after the referencing Chunk in the Document.
2. WHEN Chunk A references Chunk B and Chunk B references Chunk C, THE Tangler SHALL write the Region of C nested inside the Region of B, nested inside the Region of A.
3. WHEN a Chunk is referenced by N Chunk_References (N from 2 to 100), THE Tangler SHALL expand the referenced Chunk at each of the N positions.
4. WHEN two Chunks swap positions in the Document and no single Target_File contains both of them, THE Tangler SHALL produce Generated_Files that are byte-identical to those produced before the swap.
5. WHEN Chunks that belong to one Target_File change order in the Document, THE Tangler SHALL write their Regions in that Target_File in the new Document order.

### Requirement 6: Stitch edits back into the document

**User Story:** As a developer, I want edits I make in a `.py` file to flow back into the document, so that I can work in my IDE and keep the document as the source of truth.

#### Acceptance Criteria

1. WHEN `lit stitch` runs on an edited Generated_File, THE Stitcher SHALL replace the body of each Chunk whose Region content differs from the content tangled for that Chunk with the edited content, and SHALL exit with code 0.
2. WHEN a nested Region is present inside a Region, THE Stitcher SHALL restore the Chunk_Reference to the nested Chunk in the parent Chunk body and SHALL apply the content of the nested Region to the nested Chunk. (Subject to open question 1.)
3. THE Stitcher SHALL leave every Prose_Section, every fence line and every Chunk whose Region content is unchanged byte for byte identical to the Document before stitching.
4. WHEN no Region content changed, THE Stitcher SHALL leave the Document byte for byte identical, including line endings, and SHALL exit with code 0.
5. THE Stitcher SHALL identify the Chunk of a Region by the `chunk` value of its Begin_Marker, and SHALL NOT use Region position or content similarity to identify a Chunk.
6. IF a Begin_Marker names a Chunk_Id that does not exist in the Document, THEN THE Stitcher SHALL report an error naming the Chunk_Id and the Generated_File, SHALL exit with a non-zero code, and SHALL leave the Document unchanged.
7. IF a Begin_Marker has no matching End_Marker, or an End_Marker has no matching Begin_Marker, or the `chunk` values of a pair differ, THEN THE Stitcher SHALL report an error naming the Generated_File and the line number of the offending marker, SHALL exit with a non-zero code, and SHALL leave the Document unchanged.
8. IF a Generated_File contains the same Chunk_Id in two Regions with different content, THEN THE Stitcher SHALL report an error naming the Chunk_Id and the Generated_File, SHALL exit with a non-zero code, and SHALL leave the Document unchanged. (Subject to open question 4.)
9. IF the `doc` value of a Begin_Marker differs from the Document being stitched, THEN THE Stitcher SHALL report an error naming both paths, SHALL exit with a non-zero code, and SHALL leave the Document unchanged. (Subject to open question 9.)
10. IF stitching any one of several Generated_Files fails, THEN THE Stitcher SHALL write no change to the Document, including changes derived from Generated_Files that were valid, and SHALL exit with a non-zero code.
11. WHEN the Stitcher writes the Document, THE Stitcher SHALL write the complete new content to a temporary file in the same directory as the Document and then replace the Document with it in a single atomic rename, so that an interruption at any point leaves either the old Document or the complete new Document on disk.
12. IF the Stitcher cannot write the Document (for example the directory is read-only or the disk is full), THEN THE Stitcher SHALL report an error naming the Document path, SHALL exit with a non-zero code, SHALL leave the original Document unchanged, and SHALL remove any temporary file it created.

### Requirement 7: Failing loudly on marker damage

**User Story:** As a developer, I want stitch to refuse damaged files, so that I never get a half-synced document.

#### Acceptance Criteria

1. IF a Begin_Marker or End_Marker line in a Generated_File no longer matches its format, THEN THE Stitcher SHALL report an error that names the Generated_File and the 1-based line number of the first damaged marker line, and SHALL leave the Document byte-for-byte unchanged. (Subject to open question 5.)
2. IF Regions in a Generated_File were reordered relative to the nesting that the Document defines, THEN THE Stitcher SHALL report an error that names the Generated_File and the id of each Chunk whose Region is out of order, and SHALL leave the Document byte-for-byte unchanged. (Subject to open question 3.)
3. IF the Stitcher reports an error, THEN THE Stitcher SHALL write the error to standard error and SHALL exit with a non-zero status code.
4. IF the Tangler reports an error, THEN THE Tangler SHALL write the error to standard error and SHALL exit with a non-zero status code.
5. IF a Generated_File was changed in a way that stitch cannot map to a Chunk body, THEN THE Stitcher SHALL report an error that names the Generated_File and the 1-based line range of the unmappable change, SHALL leave the Document byte-for-byte unchanged, and SHALL leave the Generated_File unmodified so that the change remains on disk. (Subject to open questions 6 and 7.)
6. IF the Stitcher reports an error for any Generated_File during a single stitch run, THEN THE Stitcher SHALL apply no Chunk body changes from any Generated_File in that run, including files that had no errors.

### Requirement 8: Lossless round trip as an executable property

**User Story:** As a maintainer, I want the round trip stated as a property-based test, so that losslessness is checked over many documents rather than assumed.

#### Acceptance Criteria

1. THE Round_Trip_Test SHALL generate Documents that each contain 1 to 20 Prose_Sections and 1 to 20 Chunks, including Chunks with and without a Target_File, at least 1 plain fenced block, Chunk_References nested to a depth of 3 to 5 levels, and line endings drawn from LF, CRLF, and a mix of both within one Document.
2. FOR ALL generated Documents, WHEN the Document is tangled and then stitched with no edit, THE System SHALL produce a Document byte for byte identical to the original (identity property).
3. FOR ALL generated Documents and FOR ALL edits to Region contents, WHEN the Document is tangled, the edits are applied, the result is stitched, and the stitched Document is tangled again, THE System SHALL produce Generated_Files byte for byte equal to the edited Generated_Files (fixed-point property).
4. FOR ALL generated Documents and FOR ALL edits to Region contents, WHEN the edited Generated_Files are stitched, THE System SHALL change no byte of the Document outside the bodies of the edited Chunks (locality property).
5. FOR ALL generated Documents, WHEN the same Generated_File content is stitched twice in succession, THE System SHALL produce a Document byte for byte identical to the Document produced by stitching once (idempotence).
6. FOR ALL generated Documents, FOR ALL reorderings of Chunks in the Document, and FOR ALL body edits, THE System SHALL produce a byte for byte identical final Document whether the body edit is stitched before the reorder or after it (confluence property).
7. FOR ALL generated Documents and FOR ALL damaged Generated_Files (a marker deleted, duplicated, altered, or with an unknown Chunk id), WHEN the damaged Generated_File is stitched, THE System SHALL either leave the Document byte for byte unchanged, exit non-zero, and report an error identifying the damaged Generated_File, or produce a Document that parses without error (error-condition property).
8. THE Round_Trip_Test SHALL run under `pytest` and SHALL execute at least 100 generated examples for each of the properties in criteria 2 through 7.
9. IF the Round_Trip_Test finds a failing example, THEN THE Round_Trip_Test SHALL fail the pytest run and report the shrunk failing Document together with the name of the violated property.

### Requirement 9: Command line behaviour

**User Story:** As a developer, I want `lit tangle` and `lit stitch` to behave predictably, so that I can use them in hooks and scripts.

#### Acceptance Criteria

1. WHEN `lit tangle <document>` completes successfully, THE Tangler SHALL write each Generated_File, print the path of each Generated_File written to standard output (one path per line), and exit with status 0.
2. WHEN `lit stitch <python-file> <document>` completes successfully, THE Stitcher SHALL write the edited chunks of the Python file into the Document and exit with status 0.
3. WHERE the `--check` option is given to `lit tangle`, THE Tangler SHALL write no file, SHALL print to standard output the path of each Generated_File that is absent on disk or whose content differs from the tangle of the Document, SHALL exit with status 1 when at least one path is printed, and SHALL exit with status 0 when none is printed.
4. IF a command-line argument names a file that does not exist, THEN THE CLI SHALL print the missing path to standard error, exit with a non-zero status, and leave the Document and all Generated_Files unmodified.
5. WHEN `lit tangle <document>` is run without `--check`, THE Tangler SHALL treat the Document as the source of truth and SHALL overwrite each Generated_File whose content differs from the tangle of the Document.
6. IF `lit tangle` or `lit stitch` fails because the Document or Python file cannot be processed (for example, malformed chunk attributes or a duplicate chunk id), THEN THE CLI SHALL print an error to standard error that identifies the failing file and the cause, exit with a non-zero status, and leave the Document and all Generated_Files unmodified, with no partially written file.

### Requirement 10: Self-hosting and conventions

**User Story:** As a maintainer, I want the implementation written in literacode itself, so that the tool proves itself on its own source.

#### Acceptance Criteria

1. THE System SHALL keep the implementation of every `src/literacode/*.py` file, including `__init__.py`, in a chunk of a Document under `lit/`, so that each such file has Regions naming its source Document and chunk ids.
2. WHEN `lit tangle --check` runs on all Documents under `lit/`, THE Tangler SHALL exit with code 0 and report zero stale Generated_Files after this feature is complete.
3. IF `lit tangle --check` finds one or more stale Generated_Files, THEN THE Tangler SHALL exit with code 1, list the path of each stale Generated_File, and leave every file on disk unmodified.
4. WHEN `ruff check` and `pytest` run on Python 3.11 and later, THE System SHALL complete `ruff check` with zero violations and `pytest` with zero failures and zero errors.
5. THE System SHALL update `lit/format.md` so that it describes the Begin_Marker syntax, the End_Marker syntax, and the chosen rule for each open question, with one section per open question stating the rule and at least one example.
6. WHEN `lit tangle` followed by `lit stitch` runs on the Documents under `lit/` with no edits to the generated files, THE System SHALL leave every Document byte-identical to its state before the run.
## Open Questions

The decided marker format is paired `begin`/`end` comments with nested Regions for references. The following details are not decided and are left for the user. Requirements marked "subject to" depend on the answer.

1. **Nesting and chunk boundaries.** When Chunk A contains `<<B>>`, the Region of B sits inside the Region of A. Does the body of A, as seen by stitch, equal the text of A's Region with each nested Region replaced by its `<<B>>` line? This spec assumes yes. Confirm.
2. **Indentation of references.** When `<<B>>` appears indented inside A, the expansion of B must be indented to match for the Python to be valid. Options: (a) the Begin_Marker, End_Marker and body of B are all indented by the indentation of the reference line, and stitch removes that indentation before storing B; (b) the Regions are not indented and the reference is allowed only at column 0. Which option?
3. **Reordered or moved regions.** If someone moves a nested Region to a different parent inside the `.py` file, should stitch (a) fail, or (b) treat it as a body edit of both parents (new reference position)? This spec assumes (a) per "fail loudly". Confirm.
4. **Same chunk expanded more than once.** If B is referenced from two places, B appears in two Regions. When both are edited differently, this spec fails (Requirement 6.8). When only one is edited, should that edit win? This spec assumes yes. Confirm.
5. **Marker damage policy.** Requirement 7.1 fails on any malformed marker. Should a marker inside a string literal or docstring that happens to look like a marker also fail, or be ignored? This spec fails, because stitch does not parse Python.
6. **Blank lines between Regions.** Current output separates top-level Regions of one file with one blank line. Is the separator part of the format (stitch ignores blank lines outside Regions), or must it be preserved exactly in the Document? This spec assumes stitch ignores text outside Regions and that edits outside Regions are an error under Requirement 7.5. Confirm.
7. **Text outside Regions in a Generated_File.** Imports or comments a developer adds above the first Region have no Chunk to go to. Fail (this spec's assumption) or ignore?
8. **Trailing newline of a body.** The Tangler currently adds a final newline when a body lacks one, which would make the round trip add a byte. Should a body without a final newline be rejected by the Parser, or should the model normalise bodies to end in one newline? Lossless requires one of these.
9. **Marker `doc=` path.** Relative to what: the output root, the repository root, or the current directory? The current implementation uses the output root and compares only the file name on stitch. Which rule?
10. **Chunks that are only referenced.** A Chunk with no `file` attribute that is referenced from a Target_File chunk appears only as a nested Region. Should a Chunk with a `file` attribute that is also referenced appear both as a top-level Region and a nested Region? This spec allows both.
11. **Migration of the old marker.** `lit/*.md` was tangled with `# lit:chunk id=... src=...` markers. This spec replaces it outright and `lit tangle` regenerates `src/`. Should stitch also accept the old marker for one release, or not?
12. **Line endings in Generated_Files.** `.gitattributes` pins LF for some paths. Should Generated_Files always be written with LF regardless of the Document's line endings, and how does stitch restore the Document's original line endings?
