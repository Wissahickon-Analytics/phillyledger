# Step 4: deviations from the design

What step 4 changed in `docs/design.md`, and why. The design holds each rule as it now stands,
so read this file only to learn why the design says what it says. Each entry: what changed,
why, the run that shows it, and the design section updated. Fact and shape numbers refer to
`docs/plans/step-04.md`.

- **Step 4: no font repair, and the check names the pages** (November 25, 2026, the Plan run).
  The design had the PDF adapter port `repair_cid_words`, and its check spoke of "all 20 grid
  pages with font codes" and of "the repaired digits". `page.extract_words()` of pdfplumber
  0.11.10 on every page of the 20 archived files returned no word that holds `(cid:` (fact 1).
  The codes are in the old repo's cut copies and the owner's older whole copies, which have other
  shas, and the Codex review of November 22 surveyed the cut copies (fact 2). The old repair also
  tries offsets 0 to 64 and scores each on English words, a search over hypotheses, which hard
  rule 4 of `CLAUDE.md` forbids. Shown this, the owner chose "Leave it out (Recommended)" (answer
  1). The
  step's list drops the repair. Its check now reads "On the 20 P-1 grid pages of FY2023 Q1 to
  FY2025 Q2, no word holds `(cid:`, and a rendered crop of each page's first and last department
  rows matches the extracted digits." The paragraph above the list says that the archive prints
  no font code, and counts 16 commentary pages where it said six (fact 8). Design sections 15,
  18.1 and 18.5.
- **S4-A: a font code is unreadable in every column, and the reasons are a closed list**
  (November 26, 2026, S4-A). `lex_cell` gave a word that holds `(cid:` `Text` in a year, code
  or text column and `Unreadable` "not_a_number" in the others, and `Unreadable.reason` was an
  open `str`. A font code is no evidence of any glyph (VAL-Q05), so right after the `Blank` test
  such a cell is now `Unreadable` with `font_code` in all six column kinds (shape 2). The
  reasons are `UnreadableReason` in `kinds.py`, eight members with `reviewed_null`, and
  `low_confidence` joins at the step that builds the OCR confidence floor (shape 3).
  `test_a_cell_with_a_font_code_is_unreadable_in_every_column` failed before the rule, and failed
  in the year column with the rule placed after the text-column test. Design sections 2.1, 3.1,
  11.4 and 12.1.
- **S4-B: the codec, a typed word key and the word cache** (November 26, 2026, S4-B). The design
  gave the codec signatures and no format, typed a word key as a `str`, and keyed the word cache
  by the doc sha, the page set and the tool string. `encode_document` now writes one JSON object,
  `asdict(doc)` with a `"format"` of `FORMAT`, sorted keys and no spaces, and refuses NaN and
  infinity (shape 12). A word key is a `WordKey`, held to the rule of `Sha256` but kept apart from
  it, and `word_key` hashes `FORMAT` with the other three inputs, so a new format number gives new
  keys. `WordJob` refuses a page below 1 and pages that are not strictly ascending (shape 9).
  `LocalCache` takes `WordKey`, and `cache_dir` writes each entry under another name and renames
  it onto the key
  (shape 11). `test_a_document_decodes_to_an_equal_document` failed with a codec that drops
  `size`. The codec writes UTF-8 with `surrogatepass`, so every `str` reads back equal. With
  `ensure_ascii`, that property and
  `test_a_high_surrogate_then_a_low_one_read_back_as_two_code_points` failed, because JSON read a
  high surrogate then a low one back as one character. `LocalCache` holds word keys alone, so
  sections 3.2, 4.4 and 10 no longer cache parse results in it, as section 18.4 already dropped
  that cache. Section 1.4 no longer names the reader's cache, keyed by a download sha, as a
  `LocalCache`. Design sections 1.4, 2.1, 3.2, 4, 10 and 12.3.
- **S4-C: what the reader gives for a page, its tool string, and the words executor** (November
  26, 2026, S4-C). The design gave `PdfReader.words` and `render` with no rule for what a page
  holds, and wrote the word lines of `run_parse` inline through `Deps`. `PdfReader` gains `tool`,
  so a caller builds a word key before it reads a page (shape 6). The pdfplumber reader stops
  after the last page asked for (shape 7), runs the old options, keeps a font code as pdfminer
  writes it (fact 9), reads the median glyph size and the old bold rule, and puts each rule on its
  centerline (shapes 1, 4 and 5). Every coordinate, width and height is a
  `float`, since pdfplumber gives a whole-number page width such as 792 as an `int` (follow-ups
  10 and 12 of pull request 47). pdfplumber gives `/Rotate` as written, while pdfminer lays a page
  out at rotation 0 when `/Rotate` is not an integer, so `/Rotate 90.0` gave a word a top of
  -117.5 on a page 792 wide, and the reader refuses a rotation that is not an `int`.
  `extract_words(store, pdf, cache, jobs)` and `merged_document(cache, keys)` take the ports they
  read (shape 10), and `core/fetch.py` makes its PDF key public as `pdf_key`.
  `test_a_cache_hit_returns_an_equal_document` failed on both caches, at `assert first == kept`,
  with a codec that drops `size`. Design sections 2.1, 3.2, 4, 4.4 and 11.5.
- **S4-D: the fixture command and the form of a word fixture** (November 26, 2026, S4-D). The
  design named `datadesk fixture <sha> <pages>` and
  `tests/fixtures/words/<series>_<edition>_p<n>.py`, and gave the file no form.
  `render_fixture(page)` in the codec now writes a module that binds
  `SHA = Sha256('...')` and `PAGE`, writes each field, puts one `Word` or `Rule` on a line, and
  writes every number and text as its `repr`, so a whole-number width stays an `int` (shape 12).
  The folder is `packages/datadesk/tests/fixtures/words/`, which the gate tests copy (plan risk
  4), and a file is `<series>_<YYYY_MM_DD>_p<n>.py`. `fixture_command` takes the store, the reader
  and the cache, and before it reads the PDF it refuses a sha the index lacks and a file of that
  name that names another sha (plan review, finding 9). `fetch_command` tells its two unions apart
  with `match` and `assert_never` (shape 14). The property test failed with a renderer that writes
  the width as a float, and the overwrite test failed with the sha check removed. Design sections
  3.2, 9 and 11.1.
- **S4-E: the crops command, the crop file and the row rule** (November 26, 2026, S4-E). The
  plan's shape 13 named `datadesk crops <tsv> <folder>`, a crop file of eight columns and one rule
  in `shell/report.py` that finds a row's line, and the design held none of them. The
  command writes the page images to `<folder>/pages/` and the row bands to `<folder>/rows/`,
  with `sheet.png` beside them, so a reader's brief can name one folder alone (risk 5). It
  writes the pages on every run that passes the checks made before any PDF is read, one that
  stops on a label included, since the labels are typed from them.
  `test_each_page_is_written_at_200_dpi_whether_or_not_a_row_has_a_label` and
  `test_a_label_that_begins_no_line_or_two_lines_stops_before_any_row_file` show both.
  A band runs across the page from `ROW_PAD`, one point, above the line's box to one point
  below it. On the 20 grid fixtures the median gap from one line's box to the next is 2.158
  points, and so is the fifth percentile of the gaps above zero, so the pad stops more than a
  point short of the next box. The band test failed with the pad dropped and with a pad of three
  points. A row of the file is `CropRow`, a frozen dataclass with `sha256: Sha256` and
  `row: RowEnd`, a `StrEnum` of `first` and `last`, and its header is the dataclass's field
  names. `read_crop_rows` serves the command and the check's test, and raises `ValueError`
  naming the line. `row_line` returns `Line | NoLine | TwoLines`, `TwoLines` holds every line
  that begins with the label, a label of no words begins no line, and both callers end their
  `match` in `assert_never`. The `row_line` tests failed with the rule flipped, with the first
  of two lines picked and with the label matched anywhere in a line. Design sections 4, 9 and
  12.3.
- **The step 4 cleanup** (November 27, 2026, the step 4 cleanup). Design section 4 no longer says
  a broken media box or crop box at or before the last page asked for stops the read, since
  pdfminer reads `/CropBox [0 0]` and `/MediaBox [0 0]` with a warning. It no longer says the
  error for a missing page, or for a PDF with no page, is chained, since its `__cause__` is
  `None`. Sections 1.4 and 12.3 no longer say each command reads the clock once, since `fixture`
  and `crops` read none. Section 1.4 lists the reader's cache adapter again, as sections 4.6 and
  12.2 do, and section 12.3 names `render_fixture`. `decode_document` now refuses a number such
  as `1e400` that reads as an infinity, as its docstring and section 3.2 already said, and
  `test_decode_refuses_bytes_that_are_not_an_encoded_document` failed on it before the guard.
  Design sections 1.4, 4, 4.2 and 12.3.
