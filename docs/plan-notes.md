# Notes for later plans

Notes that a build step left for the plan of a later step, and gaps in the gates that review
reads for. The Plan run of step N lists the titles here and reads each note that names step N
or names no step. A Build session reads a note only when its plan cites it. A note leaves this
file when the step it names has acted on it. A note or an entry named by its title is in this
file, `docs/progress.md`, `docs/followups.md` or `docs/deviations/`.

- **Formal verification skill, deferred to step 6** (November 22, 2026). The repo had no product
  code and no git history when `/pstack:setup-pstack` offered one, so there was nothing to
  verify against. Run `/pstack:create-formal-verification-skill` once `run_release` lands.
  - Target: the release protocol in design section 4.5. The promise is that `latest.json` never
    names a release whose files are not all written, and that a slower run cannot undo a newer
    release. Racing runs and retries suit a TLA+ model.
  - Open question for the model, not verified: `created_at` goes into the manifest (section 10).
    If the manifest is one of the create-only files, a retry with the same release id and a new
    `now` may fail in `put_immutable` instead of resuming.
- **`RawRow.bold` and the pinned `bool` fields, a finding for the step 5 plan** (November 22,
  2026, step corrected November 23). Design section 11.4 pins the kit's `bool` fields to
  `Word.bold` and `Column.printed`. `RawRow.bold` in `checkedtables/rows.py` is also
  `bool | None` (section 2.1), the same annotation as `Word.bold`. The design does not define
  `bool_fields` or `kit_dataclasses`, so it does not say whether `RawRow` counts. Read from the
  design, not run. Step 5 builds `rows.py` (section 15). The design names `RawRow` only in
  `pipeline.py`, `rows.py`, `columns.py` and `grammar.py` of the kit, and step 2 builds none of
  them, so steps 1 to 4 are unaffected. This note first named step 2 by mistake. The owner
  decides, before the step 5 plan, whether `RawRow.bold` joins the pinned set or `RawRow` stays
  out of `kit_dataclasses`. On November 27, 2026 he chose to pin it (design section 16, decision
  20). S5-B removes this note when it builds `RawRow`.
- **`assemble` passes the words of the cut page to `reading_for`, a note for the step 5 plan**
  (November 23, 2026, step 2, S2-E). `reading_for` compares the page words its box holds with
  the cell's words as values. So `assemble` passes the words the cells were cut from, after any
  `split_numeric_runs`, and not the page's raw words. Probed at S2-E: for "TAX434,605,553" on an
  OCR page, a reading around the child "434,605,553" gives `stale_reading` with the raw word as
  `page_words`, and the reading itself with the two children.
- **The loader's digit check and a footnoted reading disagree, a note for the plan of the step
  that builds decision 13**
  (November 23, 2026, step 2, S2-E fix round 2, finding 3 of the second Codex review of S2-E.
  Re-addressed November 27, 2026, by decision 18 of design section 16).
  Design section 3.2 says that `load_records`, which a later step builds in `datadesk`, refuses "a
  reading whose digits fail transliteration_ok" (`docs/design.md`, lines 2069 and 2070 at the
  S2-E head). The loader has only the record's text, so it cannot tell that the last `1` of the
  footnoted cell `$ 2.8 1` is a small raised mark. Run in a scratch copy of `64560f3`:
  `transliteration_ok("$ 2.8 1", "2.8")` is false, and `apply_reading` gives that cell, an
  `Amount` with the mark `1`, a reviewed `Amount` of 2.8 that keeps the mark. The reverse also
  holds: `transliteration_ok("$ 2.8 1", "2.81")` is true, and `apply_reading` gives
  `reading_refused`. So the loader as the design words it would refuse a record that the
  cell-level check accepts, and pass one that it refuses. That plan decides: either the
  loader leaves the digit check to `apply_reading`, or the record carries what the loader needs.
- **The pure packages can still reach effects the gates do not name** (November 22, 2026, step 1,
  S1-D, found in the Codex review of the stack and the build. Rewritten November 23, 2026, S2-A).
  At step 1, ten plants each passed every gate when planted alone in
  `datadesk/core/tables/birt.py`. The forbidden lists and the purity scan named specific modules
  and calls, and every review found more. The owner chose an allow-list on November 23, 2026, and
  S2-A pins it (see `docs/deviations/step-02.md`). Each plant was run again in a scratch copy of the S2-A head. The
  seven that import now fail `test_pure_packages_have_no_effects`, so `uv run pytest` fails. They
  are `from io import FileIO` reading a file, `sys.stdout.write("x")`, `uuid.uuid4()`,
  `sys.modules["os"].getcwd()`, `import posix` with `posix.getcwd()`, `import _socket` with
  `_socket.socket()`, and `defaultdict(list)` assigned at module level. The three that import
  nothing still pass all six gates: `write = print` then `write(1)`, `exec("print(1)")`, and a
  mutable class attribute. A core test that starts a subprocess, which opens a socket, also still
  passes all six gates. At `ad866a9`, before the pin, all ten passed `uv run pytest`. The pin reads
  static imports only. A list of the builtin names pure code may use would be a second closed list
  and a separate decision for the owner (Appendices B and C of `docs/plans/step-02.md`).
  - The S2-A verification lanes found six more routes. Three use the bare module globals:
    `getattr(__loader__, method)(path)` and `getattr(getattr(__spec__, loader), method)(path)`,
    with the names held in variables, and `__builtins__["open"]`. Three took the same objects
    with `from . import __builtins__`, `from . import __loader__` and `from . import __spec__`.
    Each was run again planted alone in `checkedtables/words.py`, with a docstring, in a scratch
    copy of `a4bac18`, the S2-A commit that refuses relative imports. Each plant read
    `pyproject.toml` at run time. The three bare globals still pass all six gates. The three
    relative spellings now fail `test_pure_packages_have_no_effects` with
    `words.py:1 relative import from .`, so `uv run pytest` fails, and the other five gates pass.
    The absolute spellings `from checkedtables import __builtins__`,
    `from checkedtables import __loader__` and `from checkedtables import __spec__`, used the same
    way, pass all six gates, because each full name is inside the kit. Written as
    `__loader__.get_data(path)` or `__spec__.loader.get_data(path)`, with the bare globals or the
    absolute spellings, the line fails `ty check`, which types `__loader__` as
    `LoaderProtocol | None` and `__spec__` as `ModuleSpec | None`. The routes that pass stay open
    because they are module globals that need no outside import, so no import pin sees them. A
    list of the builtin names pure code may use is a separate decision for the owner (Appendix B
    of the step 2 plan).
  - `datadesk.core` can import a name that the kit pins from a `checkedtables` module, with no pin
    of its own. With `dataclasses.dataclass` pinned for `checkedtables` and imported in
    `words.py`, `from checkedtables.words import dataclass` in `birt.py` passed all six gates in
    the same scratch copy. This is by design. Every pinned name is reviewed as legal in pure code,
    and no module object passes that way, because a pinned name that is a module fails.
  - An S2-A verification lane found that source which changes `__path__` at run time makes an
    absolute import bind a module from outside. It was run again in a scratch copy of `cd433543`
    on Python 3.12.15. `datadesk/core/__init__.py` held a function that declares
    `global __path__`, sets `__path__ = [*__path__, "<stdlib>"]` and is called at import, where
    `<stdlib>` is the folder of the standard library. `datadesk/core/tables/birt.py` held
    `from datadesk.core import subprocess` and a function that calls `subprocess.run` on `echo`.
    Importing `birt` bound `datadesk.core.subprocess` to the standard library's `subprocess.py`,
    and the function ran `echo`. With a stub `datadesk/core/subprocess.pyi` that holds
    `from subprocess import run as run`, all six gates exit 0. Without the stub, `ty check` exits
    1 with ``Module `datadesk.core` has no member `subprocess` ``, `prek` exits 1 on its `ty`
    hook, and the other four gates exit 0. The same plant in `checkedtables/__init__.py` and
    `checkedtables/words.py` binds the standard library's `subprocess` the same way, and
    `uv run pytest` exits 1 with or without the stub. The library shape test walks `__path__` and
    imports `asyncio/windows_events.py` from the standard library folder. That import raises
    `ImportError: win32 only`, so three tests in `test_library_shape.py` and the two planted shape
    tests in `tests/test_gates.py` fail. With the stub the other five gates exit 0, and without it
    `ty check` and `prek` also exit 1. The route stays open. `__path__` is a module
    global that source changes at run time, the family that Appendix B of the step 2 plan leaves
    to a separate decision for the owner. A rule against assigning `__path__` would also miss
    `__path__.append(...)`. Review reads for it, as design section 11.1 says.
- **What an OCR word carries, a note for the step 7 plan** (November 23, 2026, step 2, S2-B.
  Updated November 25, 2026, the step 4 plan). `Page` refuses a word with an OCR confidence on a
  text layer page. It does not refuse the converse states: a word on an OCR page with no
  confidence, or with a style, which the design says no OCR word has. Step 4 builds the pdfplumber
  adapter alone, so it does not learn what Textract returns. Step 7 builds the OCR path, so its
  plan decides whether `Page` refuses those states too, and records the choice in design section
  2.1.
- **What the step 2 rules do on real pages, for the plans of steps 5, 8, 10, 11
  and 12** (November 23, 2026, step 2, S2-C, found in the Codex reviews). Decisions 15 to 17 of
  design section 16 settle three of the results below, and decision 18 moves them to the first
  step whose pages print the case. Codex read three PDFs of
  `../gov-budget-data/data/phila/` with `pdftotext -bbox` and ran `group_lines`, `has_values` and
  `parse_label` on their word boxes at `8846f05`. The S2-C fix round reran the command (the
  block "PDF reproduction for findings 1-4" of `.codex-review/step-02-pr-8846f05c.md`) and
  printed the same eight lines. Real pages enter this repository's tests only as word fixtures
  that `datadesk fixture` writes, from step 4 on (`CLAUDE.md`, Tests), so S2-C changed none of
  the three functions for them. The boxes are those of `pdftotext`, not those of the adapter
  that step 4 builds.
  - Margin debris joins a cash row, for the step 8 plan.
    `test_debris_between_two_rows_joins_neither` (QCASH-Q16, VAL-Q13) uses made-up boxes. On
    page 1 of the FY2008 Q4 QCMR cash report (`qcmr/cash/FY08_Q4.pdf`), the run printed the
    words left of x 115 on three lines as `['~']`, `['Debt', 'Service-Long', 'Term']` and
    `['co', 'lnterfund', 'Charges']`. So the debris `~` is a line of its own, and the debris
    `co`, bottom 323.32, lands on the line of "lnterfund Charges", bottom 323.89, inside the
    page's tolerance of 1.859. The step that parses cash tests the real page.
  - A lower-case `n/a` hides a row, for the owner and the step 11 plan. Page 19 of the adopted
    FY2009 Budget in Brief (`budget-in-brief/adopted/FY09.pdf`) prints `n/a` in the last
    column of row 7. The run printed `7 Other Sources 57,353 69,000 0 0 0 n/a False`. The
    design names `N/A` and `NA` only, so `has_values` is false for that row. Under the lexer
    rules of the S2-D section of `docs/plans/step-02.md`, read and not run, the cell would be
    `Unreadable`, which blocks and publishes nothing. The old reader took the marker in any case
    (`tables/amounts.py:26`). Whether a lower-case `n/a` means not applicable is the owner's
    decision. Page 1 of the August 2020 realty transfer report
    (`collections/realty-transfer-tax/2020_08.pdf`) prints it too. Read with `pdftotext -bbox`
    in the S2-D fix round, the "Unclassified" row holds `n/a` in both local-tax cells of the
    percent-change columns, for 2020 against 2019 and 2020 against 2018, and the page repeats the
    row in its second table. At the S2-D head `lex_cell` reads `n/a` as
    `Unreadable not_a_number`, as `test_not_applicable_cells_are_never_numbers` asserts, and a
    copy of the old `is_null_amount_marker("n/a")` returns True.
  - Line formulas other than `(19+20)` stay in the label, for the step 11 plan. On the same
    page, the run printed `Subtotal (12 thru 17) ()` and `Operating Surplus (Deficit) for Fiscal
    Year (8-21) ()`. So rows 19 and 22 keep their line formulas in `Label.text`, because
    `parse_label` reads only the `(19+20)` form (BIB-Q38). The RTT reports print a class code in
    the same shape, "General Commercial (88-2)" (RTT dossier, "Legacy property labels"), so the
    kit cannot take `(8-21)` as a mark unless a table tells it to.
  - A bare digit after a word leaves a capital project's name, for the owner and the step 12
    plan. Page 107 of the FY2023 supplemental report (`supplemental-report/FY23.pdf`) prints the
    project heading `12-CENTER CITY TRAFFIC SIGNALS - PHASE 2` (finding 2 of
    `.codex-review/step-02-pr-6442b4eb.md`). The S2-C fix round 2 reran that command at
    `b6013a6`, in a scratch worktree, with `pdftotext -layout` 26.07.0 and a label built by
    `page_from_text`. It printed `12-CENTER CITY TRAFFIC SIGNALS - PHASE 2` as `Label.printed`,
    `12-CENTER CITY TRAFFIC SIGNALS - PHASE` as `Label.text` and `('2',)` as `Label.marks`. This
    is the bare-digit form that S2-C took from ENT-Q07 for "Sheriff 2", and the risk "A bare
    digit after a word becomes a mark" of Appendix C of `docs/plans/step-02.md` now has a real
    page. `Label.printed` keeps every word, and S2-C keeps the bare-digit form as it is. The
    supplemental capital tables of step 12 key a project by its label as printed (design section
    7.1), and `Label.text` and `Label.norm` drop the phase number that the label prints. The
    owner decides whether the bare-digit form stays in the kit or becomes a rule that a table
    declares.
  - A hyphen U+2010 printed as a dash placeholder hides two valued rows, for the owner and the
    step 12 plan. Page 17 of the FY2021 supplemental report (`supplemental-report/FY21.pdf`)
    prints U+2010 in the last cell of two revenue rows (finding 3 of
    `.codex-review/step-02-pr-0df73f36.md`). The S2-C fix round 3 reran that command at
    `0df73f3`, in a scratch worktree, with `pdftotext -layout` 26.07.0 and lines built by
    `page_from_text`. It printed `Disposal of Salvage (Recyclables) 10,000.00 - - - - -
    '\u2010' False` and `Reimbursement-Other Expenditures 25,000.00 12,000.00 0.00 0.00% 0.00 -
    '\u2010' False`. `Line.text` shows the glyph as `-`, because `normalize_space` reads U+2010
    as a hyphen. `has_values` tests the raw word, and its dash placeholders are `-`, `--`, an en
    dash and an em dash, as design section 3.1 lists them. So `has_values` is false for both
    rows, and the lexer's dash list in S2-D is the same four. Codex says it saw the same with
    `pdfplumber` word boxes, which this repository cannot run until step 4. This is the same kind
    of decision as the lower-case `n/a` above. The design names a closed list, and a real page
    prints another glyph. A dash means no value in this report (SUPOP-Q24), and the same edition
    prints U+2010 for the hyphens of its labels (SUPOP-Q32). The owner decides whether U+2010 and
    U+2011 join the dash placeholders of `has_values` and `lex_cell`. A change would touch both
    `lines.py` of S2-C and `lex.py` of S2-D, and the two lists of design section 3.1.
  - A number in the left margin reads as a recap line number, for the step 5 plan.
    `test_split_line_prefix_takes_recap_line_numbers` (ENT-Q08) and
    `test_split_line_prefix_takes_numbered_recap_labels` (QOBL-Q55) use the text `24 First
    Judicial District`, and ENT-Q08 reads the `24` as a printed line number. `pdftotext -layout`
    prints that text on page 1 of the FY2021 Q1 QCMR positions report
    (`qcmr/positions/FY21_Q1.pdf`) and `25 Records` on page 2, each on line 28 of its page. The
    S2-C fix round 3 reran that and added `pdftotext -bbox`, which puts the `24` of page 1 and
    the `25` of page 2 in the same box, x 9.19 to 18.12 and y 301.55 to 310.45. Finding 2 of
    `.codex-review/step-02-pr-0df73f36.md` says that with `pdfplumber` word boxes the two are
    the only rotated words on their pages, so they are page numbers and not line numbers of the
    departments. That is Codex's statement and not a run of ours, because `pdfplumber` is not
    installed in this repository until step 4. The tests check what `split_line_prefix` and
    `parse_label` do with a declared pattern, and that stays right, so S2-C changed no test for
    this. What the number is, and whether the positions parser of step 5 declares it page
    furniture or a line prefix, is for the step 5 plan. QPOS-Q10 left the origin of the leading
    numbers open, and `test_split_line_prefix_takes_leading_numbers` reads the same `24` and `25`
    before `Recreation`.
  - Join shape 1 joins two printed amounts, for the owner and the plan of the step that builds
    decision 16
    (finding 2 of `.codex-review/step-02-pr-0603fce3.md`). On page 1 of the adopted FY2006 Budget
    in Brief (`budget-in-brief/adopted/FY06.pdf`), the row "Purchase of Services" of the Board of
    L.&I. Review prints `6` under Increase/(Decrease) and `30,223` under FY2005 Estimated
    Obligations. Read with `pdftotext -f 1 -l 1 -bbox` 26.07.0 in the S2-D fix round 2, `6` has
    x0 346.56, top 443.52, x1 351.41 and bottom 454.24, and `30,223` has x0 402.96, top 443.52,
    x1 429.65 and bottom 454.24. The gap between them is 51.55 points, as Codex measured with
    `pdfplumber`. Given both words with those boxes as one cell of a money column on a text
    layer, `lex_cell` at the S2-D head returns `Amount 630223` through join shape 1, and a copy of
    the old `parse_amount` and `parse_decimal` joins them too. Each word alone reads as
    `Amount 6` and `Amount 30223`. This is the risk "Join shape 1 can join two cells" of Appendix
    C of `docs/plans/step-02.md`, which leaves the test of the cut to step 5 and its fixtures, and
    it now has a real page. The join shapes are part of the owner's decision of November 23, 2026,
    so S2-D does not change them. An idea for the owner, not a plan: `lex_cell` receives each
    word's box, so a join could also require the two words to sit close together. The size of
    that limit needs real fixtures, which the step that builds decision 16 holds.
  - Two percents in one row are two words on a real page, for the step 10 plan (finding 4 of
    `.codex-review/step-02-pr-0603fce3.md`). `test_two_percents_in_one_cell_split_apart`
    (RTT-Q22) splits one fused word, `12.3%4.5%`. On page 2 of the August 2020 realty transfer
    report (`collections/realty-transfer-tax/2020_08.pdf`), the Center City Condominiums row
    prints `-33.6%` and `-48.1%` as two separate words under the "% Difference" headings "# of
    records" and "local tax". Read with `pdftotext -f 2 -l 2 -bbox` in the S2-D fix round 2,
    `-33.6%` has x0 718.08, top 359.78, x1 746.60 and bottom 368.10, and `-48.1%` has x0 764.88,
    top 359.78, x1 793.39 and bottom 368.10, a gap of 18.28 points. Codex states that its
    `pdfplumber` run puts a vertical rule at x 748.08 to 748.92 between them. That is Codex's
    statement, since `pdfplumber` is not installed here until step 4. So the test proves the
    split of a fused word, and this page needs two columns bound by the rule between them. Given
    both words as one percent cell, `lex_cell` returns `Unreadable two_tokens`, and each word
    alone reads as an amount. The RTT dossier left the question open: RTT-Q22 is `unsure`, and
    its row asks for the same render and word-box check as RTT-Q21. The step 10 plan decides.
  - A percent and a tax amount are three words on a real page, for the step 10 plan (finding 5
    of `.codex-review/step-02-pr-fae7e17b.md`). `test_a_percent_and_a_tax_cell_fused_split_apart`
    (BSALES-Q36) gives `split_numeric_runs` one word, `12.3%45,678`. Codex states that its
    `pdfplumber` run, with the reference reader's word settings, finds no word with a character
    after its `%` on page 1 of the FY2017, FY2018 and FY2020 sales tax by sector reports
    (`collections/sales-tax-sector/FY17.pdf`, `FY18.pdf` and `FY20.pdf`), and that on the FY2017
    Construction row the percentage, the `$` and the amount are three words. That is Codex's
    statement, since `pdfplumber` is not installed here until step 4. Read with
    `pdftotext -f 1 -l 1 -bbox` 26.07.0 in the S2-D fix round 3, the three pages hold 150, 150
    and 160 words with a `%`, and none has a character after it. On the FY2017 Construction row,
    `2.3%` spans x 442.73 to 462.05, `$` 476.57 to 481.44 and `7,151,643` 501.05 to 540.21. So
    the test proves the split of a fused word. The BSALES dossier describes cells that fuse with
    no whitespace corridor between columns, which puts the separate words of two columns in one
    cell. Binding those two columns is a matter for the step 10 plan.
  - A heading of ZIP codes has values, for the step 10 plan. On page 1 of the March 2013 realty
    transfer report (`collections/realty-transfer-tax/2013_03.pdf`), the table "Realty Transfer
    Tax by Location" opens its Center City section with a heading that lists ZIP codes and ends
    in `92)` (finding 3 of `.codex-review/step-02-pr-7d1aa59d.md`). The S2-C fix round 4 reran
    that command at `7d1aa59`, in a scratch worktree, with `pdftotext -layout` 26.07.0 and a line
    built by `page_from_text`, and left out the part that loads the old `amounts.py`. It printed
    `Center City (19102, 03, 06, 07, 08, 09, 10, 23, 30, 46, 47, 92)` and
    `has_values: True last word: '92)'`. A value word may hold parentheses, and the heading's
    last word holds a digit and a closing parenthesis, so `has_values` is true for it. The
    risks "The design's rule gives a sentence that ends in a number values" and "A value word is
    defined twice" of Appendix C of `docs/plans/step-02.md` accepted this kind of result. The
    predicate in `lines.py` is loose by design. Step 5 adds one condition to `lanes_from_values`,
    for a number beside a label word (`docs/plans/step-05.md`, shape 7). Whether that is enough
    for this heading is for the step 10 plan. Step 10 parses this report, and the RTT dossier finds a zone's columns
    "from amount-bearing lines only" (section 4, rule 3).
  - A spreadsheet error hides two valued rows, for the owner and the step 9 plan (design section
    15, "Monthly City and School"). On page 1 of the July 2020 School report
    (`collections/monthly-school/2020_07.pdf`), the rows `PAYMENT IN LIEU OF TAXES` and
    `OTHER NON TAX` end in the text `#DIV/0!` in the percent column, and `has_values` is false
    for both. The design's rule reads the last word that is not a mark, and `#DIV/0!` is not a
    value word. No dossier records that text. The Codex review of S2-C at `d3dbb428` found it
    (finding 2 of `.codex-review/step-02-pr-d3dbb428.md`). The S2-E fix round 3 reran it at
    `f82950e`, read-only, with `pdftotext -f 1 -l 1 -layout` piped to a script that builds each
    row with `page_from_text` and calls `group_lines` and `has_values`. It printed
    `has_values=False` for `PAYMENT IN LIEU OF TAXES 4,574,002 - 96,584 350,198 (253,614)
    96,584 350,198 (253,614) (96,584) #DIV/0!` and for `OTHER NON TAX 2,557 - - - - - - - -
    #DIV/0!`. The owner decides what the cell publishes. An idea, not a plan: a spreadsheet
    error text could count as a value word, so the row keeps its values while the cell itself
    lexes as `Unreadable`. A reviewed reading of the same cell can also give a number, since the
    reading `0.0%` gives a reviewed `Amount` of 0.0 (the note "What a reviewed reading can still
    do", in its bullet on a confusable letter).
- **Constructor checks the kit does not make** (November 23, 2026, step 2, S2-B). Design section
  2.1 says that the checks a kit type makes at construction are the ones its block shows, and no
  others. Those checks guard what enters the kit from outside: an adapter's words, pages and
  documents, a record file's ids, and a table module's columns. A relation between two fields
  that one kit function computes belongs to that function and its tests. A constructor that
  checked `Label.squash` or `Amount.printed` would copy the label reader and the lexer into the
  types, and the type modules would import them in a cycle. The blocks state the facts below, and
  no constructor checks them. The verifier's log of fix round 2 and the third Codex review of S2-B
  found them. Each value was built again in a scratch copy of `aec4c6c` on Python 3.12.15, and
  each constructor accepted it.
  - The adapters of step 4 meet the word facts. On an OCR page, `Page` accepts a word with
    `bold=True` and a word with no confidence (the note "What an OCR word carries"). Standards
    sweep B made `WordRef`, `Page`, `Document` and `ReviewedReading` refuse a hash that is not a
    `Sha256`, so they no longer accept the hash `"unknown"`. A subclass of `WordRef` with the
    same four fields as a ref on the page compares unequal to that ref, so `Page` holds both
    words.
  - The record lint meets the record ids, at the step that builds the first record loader
    (`docs/plans/step-05.md`, shape 17). `Dash` accepts an empty `rule_id`, and
    `Unreadable` accepts an empty `accepted_by`.
  - The catalog test of step 5 meets the column declarations. `NumberFormat` accepts
    `decimals=-1`. `ColumnSpec` accepts the caption `"Adopted ("`, which `re.compile` refuses
    with `missing ), unterminated subpattern at position 8`.
  - `parse_label` of S2-C and its tests keep the label facts. `Label` accepts a `squash` that is
    not its `norm` without spaces, a `line_no` that is not in `printed`, and a `text` that is not
    drawn from `printed`.
  - `lex_cell` of S2-D, `apply_reading` of S2-E and their tests keep the cell facts. The cell
    constructors accept a direct `Amount` of 65.8 from the text `85.8`, a `ZERO` `Dash` from
    `85.8` and a `NotApplicable` from `85.8`, the digit disagreement of QCASH-Q22. `Amount` also
    accepts `Decimal("NaN")`. The step 2 plan has the number reader of S2-D build a `Decimal`
    from digit text, so it cannot return NaN.
  - `Dash` accepts `NO_VALUE` with a `rule_id`, where the block says the rule set `ZERO`. The
    design names no function yet that applies a `DashRule`, so the step that builds one keeps
    this fact.
  - `Finding` accepts a `subject` with no colon, where the block gives the form
    `<doc sha8>:<table>:<row key or label>`. Each function that makes a finding builds its
    subject, and no step checks the form.

  One idea is for the owner to decide, and no plan holds it. A direct `Amount` could refuse, at
  construction, a `printed` whose ASCII digits differ from the digits of its `text` less the
  digits of its `marks`. Clause C1b of step 2 says "An `Amount`'s digits are the digits of its
  words, always". The check would make that clause a fact of the type, and not only of the
  lexer's tests. A reviewed `Amount` could not make the same check, because its text may hold a
  confusable letter, such as the `o` of `1o4.o`.
- **What a reviewed reading can still do, for the owner and the plan of the step that builds
  decision 13** (November 23,
  2026, step 2, S2-E fix round, found in the Codex review of `ce55ea9a`. Re-addressed November
  27, 2026, by decision 18 of design section 16). Each case below was
  run in a scratch copy of `f479ede`, and the fix round changed none of them. The owner decided
  the direction of the rule on November 23, 2026 (design section 16, decision 13), and
  confirmed the exact rule of section 16.2 the same day (section 16.3).
  - `apply_reading` alone accepts a reading of another cell that prints the same text on the
    same page (Codex finding 4). On a row of `2918 2918`, a reading whose box holds the first
    cell gives `None` from `reading_for` for the second cell, and `apply_reading` of it to the
    second cell gives a reviewed `Amount` of 291.8 on the second cell's word. A cell holds word
    refs with no boxes, so `apply_reading` cannot see the reading's box. `reading_for` binds a
    reading to its box, so step 5's `assemble` calls it first, with the words of the cut page,
    and gives `apply_reading` only the reading it returns.
  - The reading check compares digits only. So a reading can move a printed decimal point. The
    cell `29.18`, a direct `Amount` of 29.18 in a money column, read as `291.8` gives 291.8. It
    can drop a printed sign, since `(29.1)` read as `29.1` gives 29.1, and add one, since `29.1`
    read as `(29.1)` or `-29.1` gives -29.1. Design section 3.1 allows a reading to place a
    separator and a sign that extraction lost. Whether a reading may change one that the cell
    already prints is the owner's decision. A reading can also join two printed numbers by
    dropping a printed decimal point (Codex review of `2e0f4eca`, finding 2). The cell
    `110,626,142.01 92.31`, a balance and the percentage beside it (VAL-Q15), is `Unreadable`
    with the reason `two_tokens`. The reading `1106261420192.31` gives a reviewed `Amount` of
    that value, and the reading `110626142.01` gives `reading_refused`. A rerun at `f82950e`
    printed `reading '1106261420192.31' -> Amount 1106261420192.31 reviewed` and
    `reading '110626142.01' -> reading_refused`. This case falls under the same decision.
  - An `Unreadable` cell that also holds a small raised footnote digit keeps that digit in its
    text, so a reading must carry it. On a text layer, `2918` then a raised `1` in a one-decimal
    column gives `Unreadable` `2918 1` with the reason `decimals`. The readings `291.8` and
    `2918` give `reading_refused`, and `2918.1` and `291.81` give reviewed amounts, so the cell
    reads only as a number that ends in 1. `Unreadable` has no marks field. That plan
    decides whether the cut stage keeps a raised mark out of an unreadable cell.
  - A glyph of `seen` that is not an ASCII digit and not one of the nine pinned confusables
    counts as nothing, so a reading can skip it (found in the verification lanes of fix round
    2, run in a scratch copy of `64560f3`). For the OCR cell `29l8`, where OCR returned a
    lower-case L for a 1, the reading `29.8` gives a reviewed `Amount` of 29.8, and `291.8` gives
    `reading_refused`. For `¹,234` and `①,234`, the reading `234` gives a reviewed `Amount` of
    234, and `1,234` gives `reading_refused`. The confusable glyphs are a pinned closed list
    (`test_confusable_glyphs_are_pinned`, design section 3.1) with no `l` or `I` for 1, so a
    change is the owner's decision under hard rule 6 of `CLAUDE.md`. An idea, not a plan: a
    stricter rule would refuse a reading when `seen` holds a letter that is not a pinned
    confusable.
  - A confusable letter anywhere in the cell's text supplies a digit, in a word that holds no
    digit and on a text layer as well as on OCR (Codex review of `2e0f4eca`, finding 1). In a
    money column the cell `408,491,218 NET PROFITS TAX` is `Unreadable` with the reason
    `not_a_number`. The reading `408491218` gives `reading_refused`, and the reading
    `4084912180` gives a reviewed `Amount` of 4084912180, because the `O` of `PROFITS` reads as
    0. The cell `TOTAL TAX REVENUE *` read as `0` gives a reviewed `Amount` of 0. A rerun at
    `f82950e` on both sources printed `reading '408491218' -> reading_refused`,
    `reading '4084912180' -> Amount 4084912180 reviewed` and, for `TOTAL TAX REVENUE *`,
    `reading '0' -> Amount 0 reviewed`. The code follows design section 3.1 as written ("D, d,
    O, o, Q and q as 0 ... and every other glyph as nothing"), so this is a question about the
    design's rule and not a defect of `records.py`. Such a cell exists only when the cut puts
    label words into a value cell. VAL probes 35 and 40 (VAL section 3.2.1) are these two texts
    in a money column, and each lexes as `Unreadable not_a_number`. VAL section 3.1 lists them
    as a footnote mark and as an amount fused to a label in the collections reports. Codex
    states that on page 2 of the April 2024 City collections statement
    (`collections/monthly-city/2024_04.pdf`) `TOTAL TAX REVENUE *` is a row label, and that the
    first amount to its right is `4,160,607,459`. That is Codex's statement, not checked here.
    The owner decides the rule. Ideas, not a plan: a confusable letter could count only inside a
    word that also holds a digit, or only on an OCR page, or a reading could be refused when
    `seen` holds a letter that is not a pinned confusable. When that plan writes the loader
    for readings, it should run a tighter rule against the old repository's reviewed readings
    before the owner adopts it. The Codex review of S2-E at `73d428e2` (finding 1) found the same
    rule at work on a cell that is cut correctly and sits on a text layer. Page 1 of the July
    2020 School report (`collections/monthly-school/2020_07.pdf`) prints `#DIV/0!` in the
    percent column of two rows (the note "What the step 2 rules do on real pages", in its bullet
    on a spreadsheet error). In a percent column the one-word cell `#DIV/0!` is `Unreadable` with
    the reason `not_a_number`. The reading `0.0%` gives a reviewed `Amount` of 0.0, because the
    `D` reads as 0 and the token prints one 0. The reading `0` gives `reading_refused`, and a
    null reading is accepted. A run at `73d428e2`, with the cell built by `page_from_text`,
    printed `('Amount', "Decimal('0.0')", 'r1', None)` for `0.0%`, `reading_refused` for `0`
    and `('Unreadable', 'None', None, 'r1')` for the null reading. The word holds the digit 0,
    so the idea of counting a confusable only inside a word with a digit would still take
    `0.0%`. The other two ideas would refuse it, since the page is a text layer and `I` and `V`
    are not pinned confusables. That is read from the rule and not run.
- **The City's feed lists QCMR reports back to 2006, a note for the step 7 plan** (November 24,
  2026, step 3, S3-E). Read in a browser on November 23, 2026, the City's feed
  `https://api.phila.gov/phila/document-finder/v1/151831` has a category titled "Quarterly City
  Managers Report" with 99 documents, back to December 31, 2006 (step 3 plan, fact 4). The
  catalog entry of step 3 starts at September 30, 2021 (`first_period_end`), so the fetch asks
  for none of the older ones. Step 7 indexes the owner's whole reports from FY2008 to FY2021.
- **The City refuses a client without a browser's User-Agent, a note for the step 13 plan**
  (November 24, 2026, step 3, S3-E). On November 23, 2026, `curl` asked for the feed as
  `datadesk/0.1` and as `datadesk/0.1 (+https://github.com/Wissahickon-Analytics/phillyledger)`,
  and both got HTTP 403 from `awselb/2.0` behind CloudFront. A browser got the feed (step 3 plan,
  facts 6 and 11). The owner's answer for a run that is his is the string the old repo sends (answer A,
  `publisher_http.py:199`). The step 3 plan also records that the agents that build this repo do
  not send that string themselves, and that the City's permission is the owner's statement, which
  no session has checked. At step 3 the City's files came through a real browser and the saved
  folder, and no `datadesk` command sent the City a request. The live `Http` adapter waits for
  step 13.
- **The FY2027 Q1 report waits for OCR, a note for the step 7 plan** (November 24, 2026, step 3,
  S3-E). The City's report for September 30, 2026 is saved as `qcmr-2026-09-30.pdf` in
  `/Users/nhand/DataProjects/phillyledger-held/qcmr-city`, with sha
  `640068cb7a8a5d6c621f0ac6a0b2e16df6c290fc1036ea95f2260057be58f365`, 1,072,165 bytes and 92 pages.
  Its cover has no text a program can read (QPOS-Q38), so `confirm_period` returns
  `period_unreadable`, and `plan_fetch` rejects it and neither stores nor indexes it (step 3 plan,
  fact 14). Other pages differ. Under `pdftotext -layout`, page 2 prints only shifted glyph codes,
  and page 10 prints its title lines and amounts that way and its row labels as text. Page 6 prints
  "For the Period Ending September 30, 2026", and page 50 prints a table of performance measures.
  The step 3 planning session read pages 1, 2 and 10 with pdfplumber, and the step 3 cleanup read
  pages 1, 2, 6, 10 and 50 with `pdftotext`. No run has sorted the other 87 pages, so no run says
  which pages need OCR. The owner chose to let it wait until a later step can read its cover
  (answer D). Step 7 adds `datadesk ocr --spend` (design section 15), and Textract calls need the
  owner's go-ahead (hard rule 8 of `CLAUDE.md`). Step 4 ports no font repair, because none of the
  20 archived files prints a font code (`docs/plans/step-04.md`, facts 1 and 2, answer 1). This
  file does: pdfplumber 0.11.10 gives a `(cid:N)` code on 86 of its 92 pages. The old repo's
  `repair_cid_words`, run page by page on November 25, 2026, picks offset 29 on 56 of them and
  leaves no code, the P-1 grid pages 35 and 36 among them. It refuses the other 30, the cover
  among them, which has 5 words and one vocabulary hit where the rule wants three. With 29 added
  to every code the cover reads "FOR THE PERIOD ENDING SEPTEMBER 30, 2026". Page 86, set in
  Calibri, gives no words at that offset (fact 7). So the cover may need a font map and no OCR,
  and one offset for each page is not the rule. The plan of the step that takes this report
  designs the repair, and hard rule 4 applies to it.
- **A loader builds each sha with `Sha256`, a note for the plan of the step that builds the TOML
  loaders** (November 25, 2026, standards sweep B). Standards sweep B gave a file's sha the type
  `Sha256`, whose constructor raises `ValueError` for anything but 64 lowercase hex characters,
  and `WordRef`, `Page`, `Document` and `ReviewedReading` refuse a sha that is not one. The
  record files that `load_records` reads (design section 3.2) cite shas as text, so a loader
  builds each with `Sha256` and turns its `ValueError` into a finding, as `gather_repo` turns one
  from `parse_index` into `index_unreadable`. The `PdfReader` adapter of step 4 does not build
  a hash. `parse` hands it the job's doc sha, already a `Sha256` (design sections 4 and 4.4).
  Step 4 turns text into a sha in two places, the `<sha>` word of `datadesk fixture <sha>
  <pages>` and `decode_document` in `core/codec.py`. Each builds it with `Sha256`, since the
  kit's constructors refuse plain text. This note replaces "The kit checks a hash for presence
  only", on which sweep B acted.
- **Sixteen archived reports have a commentary page before the P-1 grid, a note for the step 5
  plan** (November 25, 2026, the step 4 plan). In every archived file from `qcmr:2022-06-30:none`
  on except `qcmr:2023-12-31:none`, the page before the two grid pages has rotation 0, begins
  `TABLE P-1` and goes on "ABOUT THIS SECTION:". The other four files have a 19-word divider page
  there that does not print `TABLE P-1` (`docs/plans/step-04.md`, fact 8). The Codex review
  counted six such pages in the old repo's cut copies, and design section 15 now says 16.
- **Rules and margin page numbers on the P-1 grid pages, a note for the step 5 plan** (November
  25, 2026, the step 4 plan. Extended November 27, 2026, the step 4 cleanup, from pull request
  51). The 20 grid pages of FY2023 Q1 to FY2025 Q2 draw no line object and
  410 thin rects, 220 of them upright, 0.72 or 1.44 points wide (`docs/plans/step-04.md`, fact
  4). The step 4 adapter gives each as a `Rule` on its centerline, so these pages have vertical
  rules, and `cut_pages` in design section 3.1 takes `lanes_from_rules` when a page has them and
  `lanes_from_values` when it has none. The step 5 plan decides which the P-1 pages use. Six of
  the 20 pages, in the three editions `qcmr:2022-09-30:none` to `qcmr:2023-03-31:none`, also
  print a sideways page number in the left margin, at `x0` 5.63, which the adapter gives as two
  words of one digit (fact 5). They are page furniture, and no row's words. On those six pages
  `group_lines` joins the two digits to table lines. Line 27 holds the digit `2` alone, and line
  28 begins with `5` or `6` before `First` or `Records`, so `row_line` finds no line for those
  rows. They sit mid-table, and no row of the step 4 crops is one of them. This note proposed
  dropping the digits before lines are grouped. The step 5 plan takes lanes from values and lets
  the design's prefix rule take each digit off its row (`docs/plans/step-05.md`, shapes 3 and 9).
  Its probe found the margin number in seven editions, on 14 pages (fact 9). S5-E removes this
  note.
- **The archive prints no font code in the cash pages, a note for the step 8 plan** (November
  25, 2026, the step 4 plan). QCASH-Q14 and VAL-Q05 describe `E(cid:121)PENSES` in the cash pages
  of FY2023 Q1 and Q2, and design section 3.2 has `split_grids` match `(cid:N)` in that caption.
  They were read from the old repo's cut copies. No page of the 20 archived files, FY2022 Q1 to
  FY2026 Q4, gives a word that holds `(cid:` (`docs/plans/step-04.md`, facts 1 and 2). Step 8
  reads the archived cash pages before it keeps that branch. The OCR reading `ANO` in the same
  quirk is another matter.
- **The adapter does not turn sideways text, a note for the step that first meets it** (November
  25, 2026, the step 4 plan). The old backend finds a page whose glyphs mostly run sideways and
  turns its words and boxes upright (`dominant_sideways_turn` in old `pdfplumber_backend.py`,
  line 40). Step 4 does not port it, because the 20 P-1 grid pages have rotation 90 and read
  upright through pdfplumber (`docs/plans/step-04.md`, fact 3 and shape 4). The plan of the first
  step whose pages need the turn ports it and adds it to the tool string.
- **Word boxes and `render` use other frames off the origin, a note for the plan of the first
  step that renders or runs OCR on a page outside the 20 grid pages** (November 27, 2026, the
  step 4 cleanup, from pull requests 49 and 51). When a page's media box is off the origin or its
  crop box is smaller, its word boxes are in another frame than `render`. On page 39 of
  `qcmr-2022-03-31.pdf`, the box of word 530, `62`, holds only white pixels in the reader's 72 dpi
  render, and Codex counted 51 such pages across the 20 reports. A `/CropBox [50 50 562 742]`
  page reads as 612 by 792 and renders as 512 by 692. On page 39 of `qcmr-2021-09-30.pdf`, bbox
  `(-8.39, -8.39, 783.6, 603.6)`, `crops` cuts the band of another row. The 20 grid pages have
  both boxes at the origin.
- **`extract_words` never hashes the bytes it reads, a note for the step 6 plan** (November 27,
  2026, the step 4 cleanup, from pull request 49). `extract_words` labels the bytes it reads from
  the store with `job.doc_sha256` and never hashes them. A check would be a design change. Step
  5 adds no command (`docs/plans/step-05.md`, shape 20), so this waits for the step that builds
  `run_parse`.
- **What step 5 leaves for the step 6 plan** (November 27, 2026, the step 5 plan). Fact, shape
  and answer numbers are those of `docs/plans/step-05.md`.
  - Which label a release prints. On 14 rows of seven editions the two digits of the margin
    page number end up on the row's line, before a label such as `First Judicial District`
    (fact 9). The prefix rule takes them off, so `Label.text` is right and `Label.printed` keeps
    the digits (shape 9).
  - The prior-year columns of `Commerce` in the four FY2024 editions. They hold the FY2023 number
    for Commerce with Aviation, 690, under the key of the Commerce department, and Aviation's
    read 0 (fact 13, answer 4). The publisher restated the prior-year columns for `Streets` in
    FY2026 and did not for `Commerce`.
  - Rows that some editions do not print. `City Representative` is absent from nine editions
    and `Office of Arts and Culture` from five, and no page says where their positions are
    counted then (fact 12). The all-funds check will show whether the totals still tie.
  - Two ids that the old release lacks. A department keeps its id from the old
    `config/entities.yml`, so step 6 can compare by entity. The old file files `Streets` through
    FY2025 under `phl_rollup_streets_and_sanitation`, where step 5 has
    `phl_group_streets_sanitation`. It files `Commerce` through FY2023 under `phl_dept_commerce`,
    where step 5 has `phl_group_commerce_aviation` (shapes 14 and 15).
  - The check DSL. `checks/dsl.py`, `checks_for` and the `checks_for` field of `TableEntry` are
    step 6's (shape 18). So is the catalog rule that compares a check's operands with the
    operands of a derived column (shape 19).
  - A total with no parts. Design section 11.2 says that every total or subtotal row of an
    assembled table has children or holds no `Amount`, but for a row that a declared
    `ColumnSum` or `CellsEqual` names. The exception needs the check DSL, so the rule is for the
    coverage of step 6 and not for `assemble`.
- **What step 5 leaves for the step 7 plan** (November 27, 2026, the step 5 plan).
  - A group caption binds by the band between two drawn rules (shape 4). A scanned page has no
    rule, so a column with a `group` cannot bind there. Step 7 reads the scans and decides what
    bounds a group on them.
  - In seven text-layer editions, a digit that leads a row, as in `5 First Judicial District`,
    is half of a sideways page number in the left margin (fact 9). QPOS-Q10 lists leading
    numbers in older editions, such as `24 First Judicial District`, and leaves their origin
    open. Step 7 checks whether they are the same thing.
  - The P-1 captions of step 5 are written as FY2022 to FY2026 print them, in capitals (shape
    5). Older editions may print other forms.
- **The catalog rule on `Quantity`, a note for the plan of the step that builds the last
  table** (November 27, 2026, the step 5 plan). Design section 11.2 has the catalog test require
  that every `Quantity` member is used by at least one table. With one table it cannot hold, so
  step 5 leaves it out (`docs/plans/step-05.md`, shape 19).
