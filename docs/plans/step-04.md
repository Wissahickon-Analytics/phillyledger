# Build step 4 plan

Build step 4 of `docs/design.md` section 15 turns an archived PDF into a `Document`: the words,
boxes, styles and drawn rules of each page. It adds the word cache, the codec and the command
that writes word fixtures. It publishes nothing. The work is for step 5, whose parser reads these
words, and for the owner, who lands each pull request and looks over one sheet of row crops. One
kit pull request, S4-A, stands alone on `main`. Four more stack in the order S4-B, S4-C, S4-D,
S4-E.

The step's check, as the owner reworded it on November 25, 2026 (answer 1): "word fixtures
regenerate byte-identical. A cache hit returns an equal `Document`. On the 20 P-1 grid pages of
FY2023 Q1 to FY2025 Q2, no word holds `(cid:`, and a rendered crop of each page's first and last
department rows matches the extracted digits."

## Track

Full track (`docs/plans/README.md`, "Which track a step runs on"). The adapter gives every word
that a later step publishes a number from.

## What a look found

All of this is from November 25, 2026, on Python 3.12.15 with pdfplumber 0.11.10 and pdfminer.six
20260107, the versions in `uv.lock`. "The held folder" is
`/Users/nhand/DataProjects/phillyledger-held/qcmr-city`. `shasum -a 256` of each of its 20 report
files from `qcmr-2021-09-30.pdf` to `qcmr-2026-06-30.pdf` is on one line of the index and one row
of the inventory, so these are the archived bytes.

1. **No archived file prints a font code.** `page.extract_words()` on every page of the 20 files
   returned no word whose text holds `(cid:`.
2. **The font codes are in older copies.** The old repo's cut `qcmr/positions/FY23_Q1.pdf` (sha
   `a76e2b81...`, two pages) gave 308 and 249 words with a code, and `FY23_Q2.pdf`, `FY24_Q4.pdf`
   and `FY25_Q2.pdf` gave codes on both pages. `FY22_Q4.pdf` and `FY25_Q3.pdf` gave none. The
   owner's older whole copy `~/Software/phl-budget-data2/data/qcmr/FY23_Q1.pdf` (sha
   `5f238d57...`, 1,605,573 bytes) gave codes on pages 35 and 36 and on most others. The City's
   file for that quarter has 1,645,726 bytes and the sha `cbddaf2f...`. The Codex review of
   November 22 surveyed the cut copies (`docs/reviews/codex-2026-11-22.md`, line 102), so design
   section 15 named a defect that the archive does not have.
3. **The 20 grid pages.** Each is 792 by 612 points with rotation 90, begins `TABLE P-1`, and
   reads upright. Word counts are for pdfplumber's default options.

   | Edition | Grid pages | Words |
   |---|---|---|
   | `qcmr:2022-09-30:none` | 35, 36 | 522, 394 |
   | `qcmr:2022-12-31:none` | 35, 36 | 522, 394 |
   | `qcmr:2023-03-31:none` | 34, 35 | 522, 394 |
   | `qcmr:2023-06-30:none` | 32, 33 | 522, 394 |
   | `qcmr:2023-09-30:none` | 33, 34 | 525, 394 |
   | `qcmr:2023-12-31:none` | 32, 33 | 525, 394 |
   | `qcmr:2024-03-31:none` | 32, 33 | 525, 394 |
   | `qcmr:2024-06-30:none` | 32, 33 | 552, 394 |
   | `qcmr:2024-09-30:none` | 33, 34 | 521, 392 |
   | `qcmr:2024-12-31:none` | 34, 35 | 521, 392 |

4. **Page 35 of `qcmr:2022-09-30:none`.** Its glyphs are in `KOILBN+Arial-BoldMT` (1,675),
   `Arial-ItalicMT`, `KOILBM+ArialMT` and `Helvetica`, at sizes 7.44, 8.88 and 5.88. It draws 15
   rects and no line, and page 36 draws 27 rects. Two extractions gave equal words. Two renders
   at 100 dpi in one process gave equal PNG bytes.
5. **The old backend's options change one word.** With `x_tolerance=2`, `y_tolerance=2`,
   `use_text_flow=True` and `extra_attrs=["fontname"]` (old `pdfplumber_backend.py`, lines 106 to
   122 and 348 to 360), pages 34, 35 and 36 gave 292, 523 and 395 words, one more than the
   default on each. Which word splits was not read.
6. **A crop reads.** A 200 dpi crop of the "Mural Arts Program" row of page 35 shows
   `8 0 8 10 0 10 9 0 9 1`, read from the image, and the extracted words of that row are the same.
7. **FY2027 Q1 does print font codes**, and it is not one of the 20. In `qcmr-2026-09-30.pdf`,
   86 of 92 pages hold a code. The old `repair_cid_words`, run page by page, picks offset 29 on
   56 of them and leaves no code, pages 35 and 36 among them. It refuses the other 30, among them
   the cover (5 words and one vocabulary hit, where it wants three) and page 34. With 29 added to
   every code, the cover reads "City of Philadelphia Quarterly City Managers Report FOR THE
   PERIOD ENDING SEPTEMBER 30, 2026". Page 86 is set in Calibri and gives no words at that
   offset.
8. **Sixteen files have a commentary page before the grid.** In every file from
   `qcmr:2022-06-30:none` on except `qcmr:2023-12-31:none`, the page before the grid has rotation
   0, begins `TABLE P-1` and goes on "ABOUT THIS SECTION:". The other four have a 19-word divider
   page that does not print `TABLE P-1`. The design said six.
9. **pdfminer writes a font code in lower case, inside one glyph.** `handle_undefined_char` in
   `pdfminer/converter.py`, line 268, returns `f"(cid:{cid})"` as the text of one character, and
   pdfplumber builds a word from whole characters.

## The owner's answers

The owner answered two questions in the Plan session on November 25, 2026. Each row quotes the
question and the option he picked, with that option's text as he saw it.

| # | What he was shown | His choice |
|---|---|---|
| 1 | "None of the 20 archived City QCMR files prints a `(cid:N)` font code on any page (pdfplumber 0.11.10, run over all 20). The codes are only in your older copies and the old repo's cuts, which have other shas. Should step 4 still port the font repair?" The option: "Step 4 builds the adapter, cache, codec and fixtures with no repair. A word that holds `(cid:` lexes as Unreadable in every column. I reword step 4 in the design: the list drops the repair, and the check keeps both tests on the same 20 pages. The repair is designed at the step that takes FY2027 Q1, the one City file that does print codes." Its preview held the new text of step 4, and this reason: "the old repair searches offsets 0 to 64 and scores them on English words (hard rule 4), and no archived page needs it." | "Leave it out (Recommended)" |
| 2 | "The step 4 check compares a rendered crop of the first and last department rows on each of 20 pages with the extracted digits: 40 crops of 11 values each. Who reads the crops?" The option: "A fresh agent that sees only the 40 images types each row. The typed rows are committed as evidence and a test compares them with the word fixtures. You get one contact sheet of the 40 crops to look over before landing." | "Agent reads, I glance (Recommended)" |

The other options of question 1 were to port the repair and prove it on pages 35 and 36 of
FY2027 Q1, and to port it and prove it on built PDFs alone.

This pull request makes the design say what answer 1 chose: step 4 and the paragraph above the
list in section 15, the font row of section 18.1 and the size line of section 18.5.
`docs/deviations/step-04.md` records it.

## Clauses

| # | Clause | Owner | Test that proves it |
|---|---|---|---|
| C1 | Word fixtures regenerate byte-identical | S4-D | `test_each_word_fixture_regenerates_byte_identical` in `tests/test_word_fixtures.py`, and `test_a_second_run_writes_the_same_bytes` in `packages/datadesk/tests/shell/test_fixture_command.py` |
| C2 | A cache hit returns an equal `Document` | S4-C | `test_a_cache_hit_returns_an_equal_document` in `packages/datadesk/tests/shell/test_run_parse.py` |
| C3 | On the 20 P-1 grid pages of FY2023 Q1 to FY2025 Q2, no word holds `(cid:` | S4-D | `test_no_word_of_the_twenty_grid_pages_holds_a_font_code` in `tests/test_word_fixtures.py` |
| C4 | A rendered crop of each page's first and last department rows matches the extracted digits | S4-E | `test_each_row_read_from_a_crop_matches_the_extracted_words` and `test_the_rows_read_are_the_first_and_last_department_rows` in `tests/test_row_crops.py`, and the owner's words on the contact sheet in the pull request |
| L1 | From the step's list: a word that holds `(cid:` lexes as `Unreadable` | S4-A | `test_a_cell_with_a_font_code_is_unreadable_in_every_column` in `packages/checkedtables/tests/test_lex.py` |

C1 has two halves. The first test reads the PDFs from a folder that `DATADESK_HELD_PDFS` names.
It hashes each file, serves the bytes from a dict store under the archive's keys, and runs
`fixture_command` with an empty cache into a temporary copy of the catalog and the index. Every
file under `tests/fixtures/words/` must come back with the same name and bytes, and no other file.
With the variable unset it skips with a message that names it, as CI does. The S4-D owner runs it
on the held folder under Python 3.12 and 3.14 and records both runs in the pull request, beside
one run of `datadesk fixture` against R2 that leaves `git status` clean. The second test runs in
CI on a PDF it builds. It runs the command twice, and the second run reads the cache and writes
the same bytes.

C3's test holds its own list of the ten edition ids and their pages (fact 3), and fails when one
of the 20 fixtures is missing. Each fixture's sha must be the indexed sha of its edition, its
first words `TABLE P-1` and its rotation 90. C1's first test ties each fixture to the archived
bytes. A later step adds fixtures to the folder, so S4-D prints the folder's listing in its pull
request and no test counts the files.

C4's tests read `docs/evidence/crops/qcmr_positions.tsv` and the fixtures. See shape 12.

## Shapes the design leaves open

The Build sessions skip `how` and `architect`, so this plan names what the design does not. The
pull request that builds a shape records it in `docs/design.md` and in
`docs/deviations/step-04.md` (hard rule 7).

1. **No font repair** (answer 1). The adapter gives a font code as pdfminer writes it, and no code
   changes a word's text. The tool string names no repair.
2. **A cell with a font code.** `lex_cell` returns `Unreadable` with the reason `font_code` when
   any word of the cell holds `(cid:`. The test comes right after the `Blank` test, so it holds in
   every column kind. Today a `YEAR`, `CODE` or `TEXT` column gives `Text` and the others give
   `not_a_number` (the note "A word that still holds a font code" in `docs/plan-notes.md`).
   `test_a_word_with_a_font_code_never_splits` expects the new reason. `split_numeric_runs` and
   `transliteration_ok` do not change. The kit keeps the lower-case test, and S4-C pins fact 9 on
   a PDF it builds, which answers both step 2 follow-ups on the form of a code.
3. **`UnreadableReason`.** A `StrEnum` in `kinds.py` with `not_a_number`, `two_tokens`, `sign`,
   `percent_sign`, `grouping`, `decimals` and `font_code`. `Unreadable.reason` has that type and
   `_read_cell` returns `Decimal | UnreadableReason` (`docs/principles.md`, section 8.3). The list
   is pinned in `test_closed_lists_are_pinned` and in design section 11.4 (hard rule 6).
   `low_confidence` joins at the step that builds the OCR rule. No constructor gains a check.
4. **Extraction options.** The old backend's options for an upright page (fact 5), and a word's
   size is the median size of its glyphs. A word's text is what pdfplumber returns, unchanged.
   `WordRef.index` counts the words in the order pdfplumber returns them. `bold` is true when the
   font name matches `bold|semibold|demibold|demi|black|heavy` in any case (old
   `classification.py`, line 168). A rule is a line or a rect at most 3 points thick and at least
   8 long (old `rule_from_box`, line 150). `rotation`, `width` and `height` are pdfplumber's. The
   old backend's turn of sideways text is not ported, because the 20 pages read upright (fact 3).
5. **The tool string** is `pdfplumber==<version>;pdfminer.six==<version>` and then each option, so
   a change to a library or an option changes every word key. `PdfReader` gains `tool`, which
   gives it, so a caller can make a key before it reads a page.
6. **`words(pdf, sha256, pages)`.** An empty `pages` means every page. It builds only the pages
   asked for, as `page1_text` does. A page the file lacks, and any error of the libraries, is an
   `EffectError` that names the page.
7. **`render(pdf, page, dpi)`** returns the whole page as PNG bytes from pdfplumber's `to_image`.
   Nothing caches a render or compares two by bytes across machines.
8. **`WordJob` and the word key.** `core/parse_plan.py` gets `WordJob` as designed and
   `word_key(doc_sha256, pages, tool)`, the sha256 of the JSON list of the sha, the sorted pages
   and the tool string, with no spaces. `ParseJob`, `ParsePlan`, `plan_parse` and `plan_ocr` wait
   for the steps that have tables and OCR.
9. **The words executor.** `shell/run_parse.py` gets `extract_words(deps, jobs)` and
   `merged_document(cache, keys)`, the word lines of `run_parse` in design section 4.4. The
   caller reads `deps.cache.keys()` once and passes only the jobs that are missing, and the
   executor does not read the cache to decide again. `run_parse` itself waits for step 5.
10. **The cache.** `LocalCache` and `Deps.cache` as designed. `cache_dir.py` keeps one file for
    each key, written under another name and then renamed, and refuses a key that is not lowercase
    hex. `cli.py` builds it on `.cache/words` in the checkout, which git already ignores.
11. **The codec and the fixture.** `encode_document` writes JSON with sorted keys and no spaces,
    and refuses NaN. `decode_document` builds each sha with `Sha256` and raises `ValueError` for
    bytes it did not write. The two `ParseResult` functions wait for `ParseResult`.
    `render_fixture(page)` in the same module returns a Python module as text: the imports,
    `SHA = Sha256('...')`, and `PAGE`, with one `Word` and one `Rule` on a line and every float
    as its `repr`. `datadesk fixture <sha> <pages>` takes pages as `35,36`, finds the edition of
    the sha in the index, and writes `tests/fixtures/words/<series>_<YYYY_MM_DD>_p<n>.py`, with
    the stage before `_p` when it is not `none`. A sha that is not 64 hex characters or is not
    indexed stops the command. ruff and prek leave that folder alone.
12. **The crops** (answer 2). `docs/evidence/crops/qcmr_positions.tsv` has one row for each of the
    40 crops: `edition`, `sha256`, `page`, `row` (`first` or `last`), `top` and `bottom` in
    points, `label`, `values` and `read_by`. `datadesk crops <tsv> <folder>` renders each page at
    200 dpi through `PdfReader.render` and writes one PNG for each row, the band from `top` to
    `bottom` across the page, and `sheet.png`, which stacks the crops and prints under each the
    label and values typed for it. The image code is in `shell/report.py`, and `datadesk` names
    pillow as a dependency. The first test joins the fixture words whose vertical middle lies in
    the band, left to right, and requires the text to equal `label` then `values`. The second
    groups each fixture's words with the kit's `group_lines` and requires the two bands of a page
    to be its first and last lines that hold ten number words and do not begin `TOTAL`.
13. **`Page` and OCR words.** Step 4 builds no OCR adapter, so `Page` stays as it is. The note
    "What an OCR word carries" now names step 7.

## Pull requests

S4-A is alone on `main` and lands first. S4-B to S4-E are one GitHub stack, bottom first, which
may be cut before S4-A lands and then takes it by `gh stack rebase`. Each pull request also
touches `docs/design.md`, `docs/deviations/step-04.md` and `docs/progress.md` for what it builds,
and `tests/test_purity.py` for the outside names its core modules import. Paths below drop
`packages/datadesk/` unless they start at the root.

### S4-A, `step-04/a-font-code-cells`: a font code is unreadable in every column

Builds on `main`. `feat(checkedtables): read a font code as unreadable in every column`.

- Files: `packages/checkedtables/src/checkedtables/kinds.py`, `cells.py`, `lex.py` and
  `records.py`, their tests, `packages/checkedtables/tests/test_library_shape.py`, and
  `docs/plan-notes.md` and `docs/followups.md`, which lose the notes that shapes 2 and 3 settle.
  The docstring and the comment in `lex.py` that speak of a code "that repair left" lose those
  words.
- Owns L1. Proves: a cell with a font code is `Unreadable` with `font_code` in each of the six
  column kinds, alone and beside other words. A reviewed reading of such a cell is still refused
  and a null reading is still accepted. The 55 probe inputs of step 2 give the results they gave.
  The list of reasons is pinned.

### S4-B, `step-04/b-codec-cache`: the codec, the word key and the cache

Builds on `main`. `feat(datadesk): encode a document and cache it by key`.

- Files: `src/datadesk/core/codec.py`, `src/datadesk/core/parse_plan.py`,
  `src/datadesk/shell/ports.py`, `src/datadesk/shell/adapters/cache_dir.py`,
  `src/datadesk/shell/cli.py`, `tests/core/test_codec.py`, `tests/core/test_parse_plan.py`,
  `tests/shell/test_local_cache_contract.py`, `tests/shell/fakes.py`, and the tests that build
  `Deps`.
- Proves, with Hypothesis: `decode_document(encode_document(doc)) == doc` for documents with text
  layer and OCR pages, rules, child refs, absent styles and any finite float. Equal documents
  give equal bytes. Proves by example: `decode_document` raises `ValueError` for cut bytes, for
  another format number and for a sha that is not one. `word_key` changes with the sha, the page
  set and the tool string, and not with the order the pages are given in.
- Proves: the `LocalCache` contract on the dict fake and on a temporary folder. An absent key
  gives `None`, a put is read back, `keys` lists what was put, and a second adapter on the same
  folder reads the first one's entries.

### S4-C, `step-04/c-words`: words, rules and renders from pdfplumber

Builds on S4-B. `feat(datadesk): read a page's words and rules with pdfplumber`.

- Files: `src/datadesk/shell/ports.py`, `src/datadesk/shell/adapters/pdf_pdfplumber.py`,
  `src/datadesk/shell/run_parse.py`, `tests/shell/pdfs.py`, `tests/shell/fakes.py`,
  `tests/shell/test_pdf_reader_contract.py`, `tests/shell/test_run_parse.py`.
- Owns C2. The test builds `Deps` with a dict store, the real reader behind a counter, and each
  cache in turn. The first run extracts once. The second run finds the key in `keys()`, calls the
  reader no times, and returns a `Document` equal to the first. The pull request shows the test
  failing with a codec that drops `size`.
- Proves, on PDFs the tests build (design section 11.5): a text layer with a drawn grid and bold
  words gives each word's text, box, `bold`, size and no confidence, a `Rule` for each drawn line,
  and the page's number, size, rotation, source and tool string. Refs count from 0. A subset of
  pages comes back ascending. A missing page is an `EffectError`. A broken box on a later page
  does not stop an earlier page. A page with `/Rotate 90` reads upright. One PDF read twice gives
  equal documents.
- Proves fact 9 and shape 1 on a PDF whose font has no Unicode map: each code arrives whole in one
  word, in lower case, and the word's text keeps it.
- Proves `render`: the PNG has the page's size at the dpi asked for, and ink where the PDF draws a
  word.

### S4-D, `step-04/d-fixtures`: the fixture command and the 20 grid pages

Builds on S4-C. `feat(datadesk): write word fixtures for the 20 P-1 grid pages`.

- Files: `src/datadesk/core/codec.py`, `src/datadesk/shell/cli.py`, the 20 files under
  `tests/fixtures/words/`, `tests/test_word_fixtures.py`, `tests/core/test_codec.py`,
  `tests/shell/test_fixture_command.py`, the root `pyproject.toml` for the ruff exclusion, and
  `CLAUDE.md` for the new command.
- Owns C1 and C3. Proves: the text of `render_fixture(page)`, run as a module, gives a `PAGE`
  equal to the page, as a Hypothesis property. `just gates` leaves the 20 files unchanged.
- Runs, each recorded in the pull request with its command and output: `datadesk fixture` for the
  ten shas against R2, C1's first test under both Pythons, and the name of the word that fact 5
  leaves unread on page 35, with the reason it splits.

### S4-E, `step-04/e-crops`: rendered rows against the extracted digits

Builds on S4-D. `feat(datadesk): check rendered rows against the extracted digits`.

- Files: `src/datadesk/shell/report.py`, `src/datadesk/shell/cli.py`,
  `docs/evidence/crops/qcmr_positions.tsv`, `tests/test_row_crops.py`,
  `tests/shell/test_crops_command.py`, `packages/datadesk/pyproject.toml`, `uv.lock`, `CLAUDE.md`.
- Owns C4. In order: the owner of the pull request fills the bands, which the second test checks.
  `datadesk crops` writes the 40 PNG files. A fresh agent whose brief names only that folder
  types the label and the ten values of each image, and its text goes into the file unchanged.
  The first test then runs. A row that differs is not edited to match. It stops the pull request
  until a second fresh reading or the owner settles it on the page.
- The session sends the owner `sheet.png`, and his words on it go in the pull request. The crops
  and the sheet stay out of git.
- Sets the step's row in `docs/progress.md`.

## Risks to probe

1. **A gate rewrites a fixture.** `ruff format`, `ruff check --fix` and prek's hooks all pass over
   `tests/`. S4-D excludes the folder and shows the files unchanged after `just gates`. If `ty
   check` slows on about 9,200 lines of literals, S4-D says by how much before it excludes them.
2. **Bytes that differ by machine.** Word boxes are floats that pdfminer computes in Python, so
   they should be equal wherever the lock is. C1's first test runs under both Pythons of the CI
   matrix. CI itself holds no PDF and cannot regenerate.
3. **Codex's sandbox and the held folder.** The folder is outside the checkout. If the sandbox
   cannot read it, C1's first test skips there, and the owner's recorded runs stand for it
   (`docs/plans/README.md`, "How a pull request is verified").
4. **A fixture imported from an empty working directory.** Step 5's core tests import these
   modules by name. S4-D adds one core test that imports a fixture, so the path is proven now.
5. **A PDF with no Unicode map.** `tests/shell/pdfs.py` writes PDFs by hand. If pdfminer needs an
   embedded font program to give a code, S4-C says so and pins fact 9 on the library's own
   function, since no PDF goes in git.
6. **The reader of the crops sees the answer.** The reading is evidence only when the reader has
   the images alone. `sheet.png` prints the typed values, so it is made after the reading.
7. **The extra word of fact 5.** Step 5 lexes these words. If the old options split a number, S4-D
   stops and reports it, and does not tune an option to hide it.
8. **A row band that clips its neighbor.** C4's first test fails when a band takes a word of the
   next row, and the second fails when a band is not on the first or last department row.

## Notes this plan leaves

`docs/plan-notes.md` gets these in this pull request: for the step that takes FY2027 Q1, fact 7;
for step 5, fact 8; for step 8, facts 1 and 2, since QCASH-Q14 and VAL-Q05 describe a font code in
the cash pages of FY2023 Q1 and Q2; and for the step that first meets sideways text, shape 4.
