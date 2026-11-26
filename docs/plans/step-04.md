# Build step 4 plan

Build step 4 of `docs/design.md` section 15 turns an archived PDF into a `Document`: the words,
boxes, styles and drawn rules of each page. It adds the word cache, the codec and the command
that writes word fixtures. It publishes nothing. The work is for step 5, whose parser reads these
words, and for the owner, who lands each pull request and looks over one sheet of row crops. Five
pull requests stack in the order S4-A, S4-B, S4-C, S4-D, S4-E.

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
of the inventory, so these are the archived bytes. "The old options" are `x_tolerance=2`,
`y_tolerance=2`, `use_text_flow=True` and `extra_attrs=["fontname"]` (old `pdfplumber_backend.py`,
lines 106 to 122 and 348 to 360).

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

4. **Fonts and rules.** On page 35 of `qcmr:2022-09-30:none` the glyphs are in
   `KOILBN+Arial-BoldMT` (1,675), `Arial-ItalicMT`, `KOILBM+ArialMT` and `Helvetica`, at sizes
   7.44, 8.88 and 5.88. The 20 pages draw no line object. They draw 410 rects that are at most 3
   points thick and at least 8 long, 220 of them upright: 190 are 0.72 points wide and 30 are
   1.44. Two extractions of page 35 gave equal words, and two renders at 100 dpi in one process
   gave equal PNG bytes.
5. **The old options change one page number.** On the 20 pages the default options and the old
   options give the same words, by text and place, but for one word on each of six pages. The
   three editions `qcmr:2022-09-30:none` to `qcmr:2023-03-31:none` print a sideways page number
   in the left margin, at `x0` 5.63. The default gives it as `25` or `26`, and the old options
   give two words of one digit. No word of a table differs.
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
   pdfplumber builds a word from whole characters. The test helper already builds such a page:
   `text_pdf(r"1\0012")` read with the old options gives the one word `1(cid:1)2`.
10. **A broken box stops every later page.** For `text_pdf("BAD", "WANTED", boxes={1: "/CropBox
    42"})`, `PDFPage.create_pages` raises `TypeError: 'int' object is not iterable` before it
    yields page 2, so pdfminer cannot reach a page past one it cannot build.

## The owner's answers

The owner answered two questions in the Plan session on November 25, 2026. Each row quotes the
question and the option he picked, with that option's text as he saw it.

| # | What he was shown | His choice |
|---|---|---|
| 1 | "None of the 20 archived City QCMR files prints a `(cid:N)` font code on any page (pdfplumber 0.11.10, run over all 20). The codes are only in your older copies and the old repo's cuts, which have other shas. Should step 4 still port the font repair?" The option: "Step 4 builds the adapter, cache, codec and fixtures with no repair. A word that holds `(cid:` lexes as Unreadable in every column. I reword step 4 in the design: the list drops the repair, and the check keeps both tests on the same 20 pages. The repair is designed at the step that takes FY2027 Q1, the one City file that does print codes." Its preview held the new text of step 4, and this reason: "the old repair searches offsets 0 to 64 and scores them on English words (hard rule 4), and no archived page needs it." | "Leave it out (Recommended)" |
| 2 | "The step 4 check compares a rendered crop of the first and last department rows on each of 20 pages with the extracted digits: 40 crops of 11 values each. Who reads the crops?" The option: "A fresh agent that sees only the 40 images types each row. The typed rows are committed as evidence and a test compares them with the word fixtures. You get one contact sheet of the 40 crops to look over before landing." | "Agent reads, I glance (Recommended)" |

The other options of question 1 were to port the repair and prove it on pages 35 and 36 of
FY2027 Q1, and to port it and prove it on built PDFs alone. The preview of the first of those
said that 60 pages repair and 26 stay damaged. A recount gave 56 and 30 (fact 7).

This pull request makes the design say what answer 1 chose: step 4 and the paragraph above the
list in section 15, the font row of section 18.1 and the size line of section 18.5.
`docs/deviations/step-04.md` records it.

## Clauses

"The fixture folder" is `packages/datadesk/tests/fixtures/words/`.

| # | Clause | Owner | Test that proves it |
|---|---|---|---|
| C1 | Word fixtures regenerate byte-identical | S4-D | `test_each_word_fixture_regenerates_byte_identical` in `tests/test_word_fixtures.py`, and `test_a_second_run_writes_the_same_bytes` in `packages/datadesk/tests/shell/test_fixture_command.py` |
| C2 | A cache hit returns an equal `Document` | S4-C | `test_a_cache_hit_returns_an_equal_document` in `packages/datadesk/tests/shell/test_run_parse.py` |
| C3 | On the 20 P-1 grid pages of FY2023 Q1 to FY2025 Q2, no word holds `(cid:` | S4-D | `test_no_word_of_the_twenty_grid_pages_holds_a_font_code` in `tests/test_word_fixtures.py` |
| C4 | A rendered crop of each page's first and last department rows matches the extracted digits | S4-E | `test_each_row_read_from_a_crop_matches_the_extracted_words` and `test_each_page_has_one_first_and_one_last_row` in `tests/test_row_crops.py`, and the owner's words on the contact sheet in the pull request |
| L1 | From the step's list: a word that holds `(cid:` lexes as `Unreadable` | S4-A | `test_a_cell_with_a_font_code_is_unreadable_in_every_column` in `packages/checkedtables/tests/test_lex.py` |

C1 has two halves. The first test reads the PDFs from a folder that `DATADESK_HELD_PDFS` names.
It hashes each file, serves the bytes from a dict store under the archive's keys, and runs
`fixture_command` with an empty cache into a temporary copy of the catalog and the index. Every
file in the fixture folder must come back with the same name and bytes, and no other file. With
the variable unset it skips with a message that names it, as CI does. The S4-D owner runs it on
the held folder under Python 3.12 and 3.14 and records both runs in the pull request. The second
test runs in CI on a PDF it builds. It runs the command twice, and the second run reads the cache
and writes the same bytes.

C2's test builds a dict store, the real reader behind a wrapper, and each cache in turn. The
wrapper counts the calls and keeps the `Document` the reader returned, before any encoding. The
first run calls the reader once. The second run finds the key in `keys()` and calls the reader no
times. Both results must equal the kept `Document`, so a codec that drops a field fails the test,
and the pull request shows it failing with one that drops `size`.

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
   `transliteration_ok` do not change. The kit keeps the lower-case test. S4-C pins fact 9
   through the adapter, and that closes both step 2 follow-ups on the form of a code.
3. **`UnreadableReason`.** A `StrEnum` in `kinds.py` with `not_a_number`, `two_tokens`, `sign`,
   `percent_sign`, `grouping`, `decimals`, `font_code` and `reviewed_null`, the reason that
   `apply_reading` gives an `Amount` on a null reading. `Unreadable.reason` has that type and
   `_read_cell` returns `Decimal | UnreadableReason` (`docs/principles.md`, section 8.3). The list
   is pinned in `test_closed_lists_are_pinned` and in design section 11.4 (hard rule 6).
   `low_confidence` joins at the step that builds the OCR rule. No constructor gains a check.
4. **Extraction options.** The old options, and a word's size is the median size of its glyphs. A
   word's text is what pdfplumber returns, unchanged. `WordRef.index` counts the words in the
   order pdfplumber returns them. `bold` is true when the font name matches
   `bold|semibold|demibold|demi|black|heavy` in any case (old `classification.py`, line 168).
   `rotation`, `width` and `height` are pdfplumber's. The old backend's turn of sideways text is
   not ported, because the 20 pages read upright (fact 3). The six margin page numbers of fact 5
   stay as the two words the options give, and step 5 treats them as page furniture.
5. **Rules.** A rule is a line object, or a rect at most 3 points thick and at least 8 long (old
   `rule_from_box`, line 150). The adapter gives each as its centerline, a `Box` of no width for
   an upright rule and of no height for a level one, so the kit's "vertical when width < 1 pt"
   holds for a stroke 1.44 points wide (fact 4).
6. **The tool string** is `pdfplumber==<version>;pdfminer.six==<version>;words=<n>` and then each
   option. `<n>` is a number in the adapter that a pull request raises when it changes what the
   adapter gives for a page: the size, the style, the rules or the order. `PdfReader` gains
   `tool`, which gives the string, so a caller can make a key before it reads a page.
7. **`words(pdf, sha256, pages)`.** An empty `pages` means every page. It builds the pages up to
   the last one asked for and no later page. A page the file lacks, a broken box on a page at or
   before the last one asked for (fact 10), and any other error of the libraries, is an
   `EffectError` that names the page.
8. **`render(pdf, page, dpi)`** returns the whole page as PNG bytes from pdfplumber's `to_image`.
   Nothing caches a render or compares two by bytes across machines.
9. **`WordKey`, `WordJob` and the word key.** `core/parse_plan.py` gets `WordKey`, a `str`
   subclass that its constructor holds to 64 lowercase hex characters, as `Sha256` is, and design
   section 2.1 stops calling a word key a plain `str`. `word_key(doc_sha256, pages, tool)` returns
   the sha256 of the JSON list of the codec's format number, the sha, the pages and the tool
   string, with no spaces. `WordJob` is as designed, with `cache_key: WordKey`, and its
   constructor refuses pages that are below 1 or not strictly ascending. `ParseJob`, `ParsePlan`,
   `plan_parse` and `plan_ocr` wait for the steps that have tables and OCR.
10. **The words executor and its ports.** `shell/run_parse.py` gets `extract_words(store, pdf,
    cache, jobs)` and `merged_document(cache, keys)`, the word lines of `run_parse` in design
    section 4.4. The caller reads `cache.keys()` once and passes only the jobs that are missing,
    and the executor does not read the cache to decide again. Each function takes the ports it
    reads. `Deps` does not change at step 4, because its `http` needs a saved folder until step
    13 and no word command reads the City's listing. The step 5 plan decides when `cache` joins
    `Deps`. S4-C makes `_pdf_key` of `core/fetch.py` public as `pdf_key`.
11. **The cache.** `LocalCache` is as designed, with `WordKey` for its keys. `cache_dir.py` keeps
    one file for each key, written under another name and then renamed. `cli.py` builds it on
    `.cache/words` in the checkout, which git already ignores.
12. **The codec and the fixture.** `encode_document` writes JSON with sorted keys, no spaces and a
    format number, and refuses NaN. `decode_document` builds each sha with `Sha256` and raises
    `ValueError` for bytes it did not write. The two `ParseResult` functions wait for
    `ParseResult`. `render_fixture(page)` in the same module returns a Python module as text: the
    imports, `SHA = Sha256('...')`, and `PAGE`, with one `Word` and one `Rule` on a line and every
    float as its `repr`. `datadesk fixture <sha> <pages>` takes pages as `35,36`, sorts them and
    drops a repeat, finds the edition of the sha in the index, and writes
    `<series>_<YYYY_MM_DD>_p<n>.py` in the fixture folder, with the stage before `_p` when it is
    not `none`. It builds the store from the four `DATADESK_R2_*` variables, the pdfplumber reader
    and the cache, and no `Http`. A sha that is not 64 hex characters or is not indexed stops the
    command. So does a file of that name whose `SHA` is another sha, since two versions of one
    edition share a name, and the file stays as it was. ruff and prek leave the folder alone.
    `CLAUDE.md` and design section 11.1 get the folder's full path.
13. **The crops** (answer 2). `docs/evidence/crops/qcmr_positions.tsv` has one row for each of the
    40 crops: `edition`, `sha256`, `page`, `row` (`first` or `last`), `page_label`, `crop_label`,
    `values` and `read_by`. A row's identity comes from the rendered page and not from the words:
    `page_label` is typed from an image of the whole page, before any crop exists.
    `datadesk crops <tsv> <folder>` reads each PDF from the store, as `fixture` does. It writes
    each page at 200 dpi through `PdfReader.render`. For a row with a `page_label` it writes the
    band of the one line that begins with the label's words, across the page, and stops when no
    line or two lines begin with them. When `values` are typed it writes `sheet.png`, which
    stacks the crops and prints under each the label and values typed for it. The rule that finds
    the line is one function in `shell/report.py`, on the kit's `group_lines`, and the test calls
    it too. `datadesk` names pillow as a dependency. The first test finds each row's line in the
    fixture by `page_label`, and requires its words, left to right, to equal `crop_label` then
    `values`, and `crop_label` to equal `page_label`. The second requires exactly one `first` and
    one `last` row for each of the 20 pages of the test's own list.
14. **Type rules in the files step 4 changes** (the note "What the type rules leave for later
    steps" in `docs/progress.md`). Shape 3 settles `lex.py` and shape 9 the word key. S4-D, the
    first to change `shell/cli.py`, turns the two `isinstance` tests of `fetch_command` into
    `match` statements that end in `assert_never`. S4-C changes one name in `core/fetch.py`
    (shape 10), so that file's three callers wait for a step that changes what it does. No step 4
    code builds a URL or a new kind of store key, so both stay `str` in `ports.py`.
15. **`Page` and OCR words.** Step 4 builds no OCR adapter, so `Page` stays as it is. The note
    "What an OCR word carries" now names step 7.

## Pull requests

One GitHub stack, bottom first. S4-B builds on S4-A only through the files they share, and the
stack keeps one writer on them. Each pull request also touches `docs/design.md`,
`docs/deviations/step-04.md` and `docs/progress.md` for what it builds, and `tests/test_purity.py`
for the outside names its core modules import. Paths below drop `packages/datadesk/` unless they
start at the root.

### S4-A, `step-04/a-font-code-cells`: a font code is unreadable in every column

Builds on `main`. `feat(checkedtables): read a font code as unreadable in every column`.

- Files: `packages/checkedtables/src/checkedtables/kinds.py`, `cells.py`, `lex.py` and
  `records.py`, their tests, `packages/checkedtables/tests/test_library_shape.py`, and
  `docs/plan-notes.md`, which loses the notes that shapes 2 and 3 settle. The docstring and the
  comment in `lex.py` that speak of a code "that repair left" lose those words.
- Owns L1. Proves: a cell with a font code is `Unreadable` with `font_code` in each of the six
  column kinds, alone and beside other words. A reviewed reading of such a cell is still refused
  and a null reading is still accepted. A null reading of an `Amount` still gives
  `reviewed_null`. The 55 probe inputs of step 2 give the results they gave. The list of reasons
  is pinned.

### S4-B, `step-04/b-codec-cache`: the codec, the word key and the cache

Builds on S4-A. `feat(datadesk): encode a document and cache it by key`.

- Files: `src/datadesk/core/codec.py`, `src/datadesk/core/parse_plan.py`,
  `src/datadesk/shell/ports.py`, `src/datadesk/shell/adapters/cache_dir.py`,
  `tests/core/test_codec.py`, `tests/core/test_parse_plan.py`,
  `tests/shell/test_local_cache_contract.py`, `tests/shell/fakes.py`.
- Proves, with Hypothesis: `decode_document(encode_document(doc)) == doc` for documents with text
  layer and OCR pages, rules, child refs, absent styles and any finite float. Proves by example:
  one document encoded twice gives the same bytes. `decode_document` raises `ValueError` for cut
  bytes, for another format number and for a sha that is not one.
- Proves: `word_key` changes with the sha, the page set, the tool string and the format number.
  `WordKey` refuses text that is not 64 lowercase hex characters, and `WordJob` refuses a page
  twice and pages out of order.
- Proves: the `LocalCache` contract on the dict fake and on a temporary folder. An absent key
  gives `None`, a put is read back, `keys` lists what was put, and a second adapter on the same
  folder reads the first one's entries.

### S4-C, `step-04/c-words`: words, rules and renders from pdfplumber

Builds on S4-B. `feat(datadesk): read a page's words and rules with pdfplumber`.

- Files: `src/datadesk/shell/ports.py`, `src/datadesk/shell/adapters/pdf_pdfplumber.py`,
  `src/datadesk/shell/run_parse.py`, `src/datadesk/core/fetch.py`, `tests/shell/pdfs.py`,
  `tests/shell/fakes.py`, `tests/shell/test_pdf_reader_contract.py`,
  `tests/shell/test_run_parse.py`, and `docs/followups.md`, which loses the two follow-ups that
  shape 2 names.
- Owns C2.
- Proves, on PDFs the tests build (design section 11.5): a text layer with bold words gives each
  word's text, box, `bold`, size and no confidence, and the page's number, size, rotation, source
  and tool string. Refs count from 0. A subset of pages comes back ascending. A page with
  `/Rotate 90` reads upright. One PDF read twice gives equal documents. The tool string changes
  with the adapter's number.
- Proves shape 5 on a grid drawn with thin rects, one of them an upright stroke 1.44 points wide,
  and on line objects: each gives one `Rule` on its centerline, and a filled rect that is thicker
  gives none.
- Proves shape 7 on both sides: a broken box after the last page asked for does not stop the
  read, and one before it is an `EffectError` that names the page. A missing page is one too.
- Proves fact 9 and shape 1: `PdfReader.words` on `text_pdf(r"1\0012")` returns the one word
  `1(cid:1)2`.
- Proves `render`: the PNG has the page's size at the dpi asked for, and ink where the PDF draws a
  word.

### S4-D, `step-04/d-fixtures`: the fixture command and the 20 grid pages

Builds on S4-C. `feat(datadesk): write word fixtures for the 20 P-1 grid pages`.

- Files: `src/datadesk/core/codec.py`, `src/datadesk/shell/cli.py`, the 20 files in the fixture
  folder, `tests/test_word_fixtures.py`, `tests/core/test_codec.py`,
  `tests/shell/test_fixture_command.py`, the root `pyproject.toml` for the ruff exclusion,
  `CLAUDE.md` for the new command and the folder's path, and `docs/plan-notes.md`, which loses
  the note on how a fixture prints its sha.
- Owns C1 and C3. Proves: the text of `render_fixture(page)`, run as a module, gives a `PAGE`
  equal to the page, as a Hypothesis property. `just gates` leaves the 20 files unchanged. A
  second sha of one edition does not overwrite the first one's fixture. `fetch_command` behaves
  as before under its `match` statements (shape 14).
- Runs, each recorded in the pull request with its command and output: C1's first test under
  both Pythons, and `datadesk fixture` for the ten shas against R2. That run starts from an empty
  word cache, runs as `uv run --env-file /Users/nhand/DataProjects/phillyledger/.env` from the
  worktree (`docs/progress.md`, "The archive bucket from a worktree"), and leaves `git status`
  clean.
- Stops for the owner if a fixture differs from the default options in a word of a table. Fact 5
  found the six margin page numbers and nothing else.

### S4-E, `step-04/e-crops`: rendered rows against the extracted digits

Builds on S4-D. `feat(datadesk): check rendered rows against the extracted digits`.

- Files: `src/datadesk/shell/report.py`, `src/datadesk/shell/cli.py`,
  `docs/evidence/crops/qcmr_positions.tsv`, `tests/test_row_crops.py`,
  `tests/shell/test_crops_command.py`, `packages/datadesk/pyproject.toml`, `uv.lock`, `CLAUDE.md`.
- Owns C4. In order: `datadesk crops` writes the 20 page images. A fresh agent whose brief names
  only that folder types, for each page, the label of the first and of the last row that names a
  department and is not a total. `datadesk crops` then writes the 40 row crops, and the same
  kind of reader, with the crops alone, types the label and the ten values of each. Its text goes
  into the file unchanged. The tests then run. A row that differs is not edited to match. It
  stops the pull request until a second fresh reading or the owner settles it on the page.
- Shows, in the pull request, the first test failing on the Auditing row when the last number of
  that row is taken out of a copy of the fixture of page 35 of `qcmr:2022-09-30:none`.
- The session sends the owner `sheet.png`, and his words on it go in the pull request. The page
  images, the crops and the sheet stay out of git.
- Sets the step's row in `docs/progress.md`.

## Risks to probe

1. **A gate rewrites a fixture.** `ruff format`, `ruff check --fix` and prek's hooks pass over
   every Python file. S4-D excludes the folder and shows the files unchanged after `just gates`.
   If `ty check` slows on about 9,200 lines of literals, S4-D says by how much before it excludes
   them.
2. **Bytes that differ by machine.** Word boxes are floats that pdfminer computes in Python, so
   they should be equal wherever the lock is. C1's first test runs under both Pythons of the CI
   matrix. CI itself holds no PDF and cannot regenerate.
3. **Codex's sandbox and the held folder.** The folder is outside the checkout. If the sandbox
   cannot read it, C1's first test skips there, and the owner's recorded runs stand for it
   (`docs/plans/README.md`, "How a pull request is verified").
4. **The gate tests copy `packages/`.** `run_gate` in `tests/test_gates.py` copies `packages/`,
   `pyproject.toml` and `conftest.py` and runs the core suite in the copy. The fixture folder is
   under `packages/` so that a core test of step 5 that imports a fixture still passes there.
5. **The reader of the crops sees the answer.** A reading is evidence only when the reader has
   the images alone. `sheet.png` prints the typed values, so it is made after both readings.
6. **A label that begins two lines.** A department's own row and a row under it can begin with
   the same words. `datadesk crops` stops on two lines, and S4-E then reports the page to the
   owner. It does not pick one.
7. **Vertical rules on P-1 pages.** Shape 5 gives step 5 upright rules on these pages (fact 4),
   and `cut_pages` as designed takes its lanes from rules when a page has them. That choice is
   step 5's, and the note for its plan says so.

## Notes this plan leaves

`docs/plan-notes.md` gets these in this pull request: for the step that takes FY2027 Q1, fact 7;
for step 5, facts 4, 5 and 8; for step 8, facts 1 and 2, since QCASH-Q14 and VAL-Q05 describe a
font code in the cash pages of FY2023 Q1 and Q2; and for the step that first meets sideways text,
shape 4.

## Codex review

Codex reviewed commit `778c9d60` on November 25, 2026. Its report is
`.codex-review/step-04-plan-778c9d60.md`. It raised fourteen findings, four as blocking. Each was
checked against a run, the code or the plan, all fourteen held, and the plan above is revised for
each. Two are answered another way than Codex proposed, findings 2 and 8, and part of finding 11
is left for a later step, with the reason.

| # | Finding | How it was confirmed | What changed |
|---|---|---|---|
| 1 | The reason list left out `reviewed_null` | `records.py`, line 274, and `test_a_null_reading_on_an_amount_gives_reviewed_null` | Shape 3 and S4-A hold eight reasons |
| 2 | A core test that imports a fixture from the root `tests/` fails in the copy the gate tests make | `run_gate` in `tests/test_gates.py` copies `packages/`, `pyproject.toml` and `conftest.py` alone | The fixture folder is under `packages/datadesk/tests/`, which the copy takes. Codex proposed copying the root folder in `test_gates.py`. The extra core test is gone |
| 3 | C2 compared two results that both came through the codec | Design section 4.4: the first run caches and then reads through `merged_document` | C2's test keeps the reader's own `Document` and compares both results with it |
| 4 | C4 let the extracted words choose the row, so a row that lost a number was passed over | The plan's rule: a first row with nine number words is no longer the first line with ten | Shape 13: the row's label is typed from the whole page first, the line is found by that label, and S4-E shows the Auditing case failing |
| 5 | A test of drawn lines misses the rects that draw every rule on the 20 pages | Rerun: no line object, 410 thin rects, 30 upright ones 1.44 points wide | Fact 4, shape 5 and S4-C: centerlines, tested on rects |
| 6 | The extra word of the old options was already known to be a margin page number | Rerun on all 20 pages: six pages differ, each by that word alone | Fact 5, shape 4, and S4-D stops only for a word of a table |
| 7 | The fallback for a font code pinned the library and not the adapter | Rerun: `text_pdf(r"1\0012")` gives `1(cid:1)2` | Fact 9 and S4-C: the adapter must return that word. The fallback is gone |
| 8 | The subset test put the broken page only after the page asked for | Rerun: `create_pages` raises `TypeError` on a broken page 1 | Fact 10 and shape 7 state the limit, and S4-C tests both sides. Codex proposed that page 2 be returned. That needs a walk of the page tree apart from pdfminer, for a file no archive holds, and the result here is an error and never wrong words |
| 9 | Two versions of one edition write the same fixture name | Shape 12's name, and design section 6.3 | Shape 12 and S4-D: the command refuses to overwrite a fixture of another sha |
| 10 | The key did not change when the adapter's own rules or the codec's format did | The plan's tool string, and design section 10 | Shapes 6 and 9: a number in the tool string and the format number in the key |
| 11 | The cache key had no type, `cli.py`'s deferred callers had no owner, and a page could be given twice | `docs/plans/standards-sweep-b.md`, lines 116 to 119 and 338 to 342 | Shapes 9 and 14: `WordKey`, strictly ascending pages, and S4-D rewrites the two callers in `cli.py`. The three in `core/fetch.py` wait, since step 4 changes one name there |
| 12 | `fixture` and `crops` could not build `Deps` without a saved folder, and a warm cache could pass the R2 run | `Deps.http` in `ports.py`, and `SavedHttp` reads `responses.tsv` when built | Shapes 10, 12 and 13: the word functions take the ports they read, and S4-D's R2 run starts from an empty cache |
| 13 | S4-A and S4-B could edit the same four files at once | The plan's own text | One stack of five, S4-A at the bottom |
| 14 | "Equal documents give equal bytes" is false for `-0.0` and `0.0` | Rerun: the two are equal and `json.dumps` writes `-0.0` and `0.0` | S4-B claims only that one document encoded twice gives the same bytes |
