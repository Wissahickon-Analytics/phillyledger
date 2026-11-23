# Step 2: deviations from the design

What step 2 changed in `docs/design.md`, and why. The design holds each rule as it now stands,
so read this file only to learn why the design says what it says. Each entry: what changed,
why, and the design section updated. An entry that names a note by its title means a note in
`docs/progress.md`, `docs/plan-notes.md` or `docs/followups.md`.

- **Step 2: the purity test pins the imports of the pure packages** (November 23, 2026, S2-A).
  This is the owner's allow-list (see the note "The pure packages can still reach effects the
  gates do not name"). `PURE_IMPORTS` in `tests/test_purity.py` maps `checkedtables` and
  `datadesk.core` to the sorted `module.name` pairs that each imports from outside. Both are
  empty, because every file in both packages is empty. The scan parses each file's bytes, so it
  reads a coding cookie as the importer does. It reads imports in function bodies and under
  `if TYPE_CHECKING`. It fails every relative import, an `import` statement that binds an outside
  module, a from-import of a pair the pin does not hold, and a star import from outside whatever
  the pin holds. `checkedtables` counts itself as inside, and `datadesk.core`
  counts itself and `checkedtables`. A name taken from an outside module counts as inside when
  its full name is at or under an inside name, so in `datadesk.core` the import
  `from datadesk import core` passes and `from datadesk import shell` fails.
  `test_pure_imports_are_pinned` fails when the pairs in the source and the pin differ in either
  direction. `test_pinned_imports_are_not_modules` fails on a pinned pair that does not resolve,
  that resolves to a module, such as `dataclasses.sys`, or whose name is `*`. The verification
  lanes and the Codex review of S2-A found that the scan read each file as UTF-8, passed a pinned
  star import and reported `from datadesk import core`. The same pull request fixed each, with a
  test. `BANNED_IMPORTS` is gone, because the
  pin refuses `random` and `builtins` with every other module. Before the change, with
  `from io import FileIO` appended to `datadesk/core/tables/birt.py`,
  `uv run pytest tests/test_purity.py` printed `3 passed`. Now it fails and prints
  `birt.py:1 from io import FileIO`, and `test_planted_import_fails_purity_test` in
  `tests/test_gates.py` holds that plant. The plan said an `import` that names an outside module
  fails. The build judges the module that the statement binds, as section 11.1 says.
  `import datadesk.core.tables` names an inside module and binds `datadesk`, and once any code has
  imported `datadesk.shell`, the shell is an attribute of that binding. So that import fails, and
  `import datadesk.core.tables as tables` passes. The plan resolved a relative import from the
  file's dotted name, and the build refuses every relative import instead. The second Codex
  review of S2-A, at `c103b016`, read `__package__ = "email.mime"` and then `from . import text`
  as `checkedtables.words`. Its command passed that source to `outside_imports` and `impurities`
  and ran it with `exec` in a copy of the module's globals. On Python 3.12.15 it printed
  `outside pairs: []`, `purity findings: []` and `bound module: email.mime.text`. Python resolves
  a relative import through the module global `__package__`, which source can rebind, and a
  static scan cannot know what it holds when the statement runs. A ban on assigning it would miss
  `globals()["__package__"]`. An absolute import does not read `__package__`, and all 64 imports
  from `checkedtables` and `datadesk` in the design's code samples are absolute. The same source
  now fails with `relative import from .`. An absolute import still finds a submodule through its
  package's `__path__`, which source can also change at run time. So the scan shows only that no
  import, read as written, gives pure code a module object from outside, as section 11.1 now says
  (see the note "The pure packages can still reach effects the gates do not name"). A pull
  request that imports a new name adds its pair to `PURE_IMPORTS`. One that imports from a new
  module also adds the module to the list in section 11.1. Design section 11.1.
- **Step 2: step 2 builds five types of `columns` and `table`** (November 23, 2026, S2-B). Design
  section 3.1 gives `lex_cell` a `ColumnSpec`, and `records` takes a `RowKey` and returns
  `Finding`. Step 2 listed neither `columns` nor `table`, and no step listed `table`. S2-B builds
  `NumberFormat` and `ColumnSpec` in `columns.py` and `RowKey`, `Severity` and `Finding` in
  `table.py`, and nothing else of either module. Step 2 now names the five types, and step 5 now
  names `table`, which builds `RowKind`, `Additivity`, `additivity_of`, `TableId`, `Column`, `Row`
  and `Table` with `rows` and `assemble`. Design section 15.
- **Step 2: `WordRef` and `Finding` sort a `None` first** (November 23, 2026, S2-B). The design
  gave both classes `order=True`. That raises `TypeError` when one side holds `None` and the other
  an `int`, so a word and a child that `split_numeric_runs` made from it could not be sorted
  together (Appendix A of `docs/plans/step-02.md`). Both classes now order through written
  `__lt__`, `__le__`, `__gt__` and `__ge__` methods by the design's fields in order, with `None`
  before every `int` in `WordRef.child` and `Finding.page`. `functools.total_ordering` would need
  one method, and it would add `functools` to the closed list of section 11.1.
  `test_word_refs_sort_with_and_without_child` and `test_findings_sort_with_and_without_page`
  check all four operators against a key that puts `None` first. With `order=True` put back on
  `WordRef`, the first fails with `TypeError`. Design section 2.1.
- **Step 2: `RowKey` states its rules** (November 23, 2026, S2-B). The design said that
  `RowKey.parts` is sorted by name and that `parse` serves TOML records. A `RowKey` now raises
  `ValueError` for no parts, for names that are not strictly ascending, for an empty name, and for
  a name or value that holds `|` or `=`, so `RowKey.parse` inverts `str` for every key.
  `RowKey.of` sorts its parts by name. The plan named every rule except the one on no parts.
  `str` of a key with no parts is the empty text, which names no row, and no use in the design
  builds such a key. Design section 2.1.
- **Step 2: a text layer page refuses an OCR confidence** (November 23, 2026, S2-B, found in the
  Codex review). The design calls `Word.confidence` OCR only and lists "a page with two word
  sources" among the states its types make impossible. `Page` checked only each word's file and
  page, so a text layer page took a word with a Textract confidence, and an OCR reading such as
  the 65.8 of QCASH-Q22 could pass as a text layer number. `Page.__post_init__` now raises
  `ValueError` for a word with a confidence on a page whose source kind is `TEXT_LAYER`. The
  converse rules wait for step 4 (the note "What an OCR word carries"). Design section 2.1.
- **Step 2: `Document` and `WordRef` check what they cite** (November 23, 2026, S2-B, found in
  the Codex review). `Document` took a page of another file, so `Document.page` could return it,
  and `WordRef("", 0, 0)` cited no file and page 0. `Document.__post_init__` now raises
  `ValueError` for a page whose `doc_sha256` is not the document's `sha256`, and for page numbers
  that are not strictly ascending, as the design's comment on `pages` already said.
  `WordRef.__post_init__` raises `ValueError` for an empty `doc_sha256`, for a page below 1, which
  the design calls 1-based, and for an index or a child below 0. Design section 2.1.
- **Step 2: the constructor checks are the ones the design blocks show** (November 23, 2026,
  S2-B, found in the second and third Codex reviews and by verifiers). Each Codex round asked for
  a few more constructor checks, and the list had no natural end. Design section 2.1 now opens
  with a closed statement. The checks a kit type makes at construction are the ones its block
  shows, and no others. They guard what enters the kit from outside, and a relation between two
  fields that one kit function computes has no check at construction (the note "Constructor
  checks the kit does not make"). Fix round 3 replaced a wider rule of fix round 2, which promised
  a check for every fact a block states. The blocks state many facts that no constructor checks.
  One check in the code had no line in its block, the refusal of a part with no `=` in
  `RowKey.parse`, and fix round 3 added it to the `table` block. Fix round 2 added six checks.
  Each is shown in its block of section 2.1, and each has a test of the refused value and of its
  nearest legal value. No field changed, so `FIELD_SNAPSHOT` is unchanged.
  - `Amount` refuses an empty `review_id` in either reading. The `cells` block says "a reviewed
    Amount names its review, and only then", and the empty text names no review.
    `Amount(..., Reading.REVIEWED, "")` was accepted.
  - `Dash` refuses no words. The `cells` block lists "a number without words" as impossible, and
    a `ZERO` dash is the operand 0. It also lists "blank" and "dash" as two flags on one field,
    and a dash with no words is a blank cell. `NotApplicable`, `Unreadable` and `Text` get no
    such check. `Dash("", (), DashMeaning.ZERO)` was accepted.
  - `Page` refuses two words with equal refs. The `refs` block says a ref's `index` is the
    "extraction order on that page", so one ref names one word. A word and the children that
    `split_numeric_runs` cuts from it differ in `child`, so they may share a page.
  - `Word` refuses a confidence outside 0 to 100, NaN included. The `words` block says "OCR only,
    0 to 100". A NaN and 101.0 were accepted, and `< 95` is false for both, so both clear a
    confidence floor of 95.
  - `Page` refuses an empty `doc_sha256` and a `number` below 1, and `Document` refuses an empty
    `sha256`. The `words` block lists "a word without its file hash and page" as impossible, and
    the `refs` block calls a page "1-based". A page with no words escaped the word checks, so
    `Page("", 0, ...)` and `Document("", ...)` were accepted. The kit checks a hash for presence
    only (the note "The kit checks a hash for presence only").
  - `ColumnSpec` refuses an empty `name` and an empty `caption`. The `columns` block lists "a
    column without a name and a caption" as impossible, and the empty caption regex matches every
    header.

  The `ColumnSpec` test is in a new `test_columns.py`, and the S2-B file lists of
  `docs/plans/step-02.md` now name it. Design section 2.1.
- **Step 2: `text` and `lines` state four rules and a ninth mark form** (November 23, 2026,
  S2-C). Design section 3.1 left four rules open, and its comments now state them.
  `group_lines` takes words by bottom, then `x0`, then ref, and a word that does not join the
  open line opens the next. A line's words sort by `x0` and lines by top. `has_values` reads the
  last word that is not a mark word. A value word is `N/A`, `NA`, a dash placeholder, or a digit
  with only `,`, `.`, `$`, `%`, parentheses, minus glyphs and trailing marks. `split_line_prefix`
  keeps the line's box, and a line of only prefix words comes back with no words, so a column of
  line numbers seeds no lane. `lines_text` joins the lines' text with a newline. `parse_label`
  also takes one bare digit after a word as a mark, as `entities.py:54-61` of the old code did
  (ENT-Q07). So "Sheriff 2" gives the text "Sheriff" and the mark "2", and "CLASS 100" and
  "10 COMMUNITY DEVELOPMENT" keep every word. With that form removed in a scratch copy, the
  "Sheriff 2" test fails and the "Human Services (1)" test passes. The mark "see note" takes any
  one space between its words, or none, where the design named only "see note" and "seenote".
  With a non-breaking space the mark stayed in the label, so two labels that print the same got
  different `norm` values (WAGE-Q44, found in the second Codex review). The comments also say
  three smaller things. `normalize_label` turns punctuation into a space where the design said
  "drop", as `entities.py:95` did, so "Delivery/couriers" gives "delivery couriers" (BSALES-Q47).
  `normalize_space` trims the ends. `page_from_text` keeps a `**` that opens no bold span, so
  the label "Total RTT records **1" (RTT-Q38) can be built with it. A `**` that starts a word
  opens a span when the word's next character is not `*`, and a `**` that ends a word closes
  one when the character before it is not `*`. Each closer pairs with the nearest unpaired
  opener to its left on the same line, and every other `**` stays in the text. The first build
  paired the first two `**` on a line, so "Total RTT records **1  **1,234**" gave the words
  `1`, bold, and `1,234**` (found in the Codex review). It now gives `**1` and a bold `1,234`.
  A word is a run of characters with no ASCII space, and a `**` opens or closes a span only at
  an ASCII space or a line end. The second Codex review found that a `**` after a non-breaking
  space opened a span inside a word, so `Tax`, a non-breaking space and `**1,234**` lost the
  asterisks and 24 points of the word's box. That word now keeps them and is not bold.
  The comment of `doc_of` also says that it sorts the pages by number and raises `ValueError`
  for no pages, for pages of two files and for a repeated page number. `text`, `lines`
  and `testing` import from `re`, `statistics` and `typing`, which join the list in section
  11.1. The strategy `pages()` of `test_lines.py`, behind clause C1a, draws every field of
  `Page` and of `Word`, so it covers the input type of `group_lines` (fix round 4). A mutation
  that keys on one drawn value, such as dropping OCR words with a confidence above 99.5, can
  still survive a run without the explicit examples, because a property test samples. Design
  sections 3.1 and 11.1.
- **Step 2: the probe clause reads the 55 inputs of VAL section 3.2.1** (November 23, 2026,
  S2-D). VAL section 3.2 prints 16 of the probe's 55 inputs, and no file holds the rest or any
  new result. The owner chose the 55 rows of Appendix E of `docs/plans/step-02.md`, with the
  words "[u]se your list, but make row 4 unreadable." They are now VAL section 3.2.1, and design
  section 16 records the choice as decision 12. The step 2 check gains "(decision 12)" and no
  other word. `test_val_probe_table_is_the_dossier_table` in `tests/test_evidence.py` fails when
  the dossier table and `PROBES` differ. Row 34 writes its backtick inside a double-backtick
  code span, where Appendix E writes the input and result in words. Design sections 15 and 16.
- **Step 2: `lex_cell` states its rules** (November 23, 2026, S2-D). The design's kerning rule
  joined two tokens when one carried a separator and the result was strictly grouped. That
  joins `4727 402.5` into 4727402.5 and `12 3,456` into 123,456, which `tables/amounts.py:63-97`
  names as two values. The comment of `lex_cell` in section 3.1 now gives the old code's two
  shapes with their token limits, in money and percent columns on a text layer only, the minus
  glyphs, the number reader and the six `Unreadable` reasons in order. The build read three
  rules of the plan more narrowly. A `$` word leaves the cell only when it opens it, because
  with `5 $` the plan's rule gives an `Amount` while `has_values` of S2-C is false, and with
  `1 $ 37,332,523` it joins across the `$`. A raised mark is a one-digit word, measured against
  the word just before it, which must hold a digit, so a raised `12` stays a token and the cell
  is `Unreadable`. The reader takes ASCII digits only, because Python's `\d` also matches
  fullwidth and Arabic-Indic digits, which `Decimal` reads. "grouping" is also the reason for a
  `$`, `%` or mark in a place no number uses, such as `$$1,234`, `(12.3)%` and `2*42,096`,
  since no other reason's meaning covers them. The comments of `split_numeric_runs` and
  `transliteration_ok` now state where a cut falls and the nine confusable glyphs. `lex.py`
  imports nothing new. Design section 3.1.
- **Step 2: the lexer refuses five more readings it took** (November 23, 2026, S2-D fix round,
  found in the Codex review and the verification lanes). Each change has a test that failed
  before it. Design section 3.1 and the S2-D boxes of `docs/plans/step-02.md` say the same.
  - A `$` word that opens a cell comes back in front of the number that the other tokens give,
    so the reader sees every `$`. Before, `$ $1,234` read as 1234, and `$ $67,215,504.0 0` as
    67215504.00, which both old readers refuse. Both are now `Unreadable grouping`, and so are
    `$ -$5`, `$ $(5)` and `$ ($5)`. `$ 5`, `$ (1,234)` and `$ 1 37,332,523` read as before.
  - One `$` word and one dash form are a `Dash` with the column's meaning. Before, `$ -` was
    `Unreadable not_a_number`. Page 1 of the August 2020 realty transfer report
    (`collections/realty-transfer-tax/2020_08.pdf`) prints the form. Read with
    `pdftotext -bbox`, its "Unclassified" row holds `56 $ 1,313`, `50 $ -`, `61 $ 0`,
    `6 $ 1,313`, `12.0% n/a`, `(5) $ 1,313` and `-8.2% n/a`, so the August 2019 local-tax cell
    prints `$` and `-` where the August 2018 one prints `$` and `0`. The "Voided transactions"
    row prints `-` or `$ -` in each count and local-tax cell, and the page repeats both rows in
    its second table, by location. A dash then a mark word, `$ N/A` and `- 0` are unchanged.
  - `transliteration_ok` fails when either text holds a character that `str.isdecimal()` holds
    and that is not an ASCII digit. Before, a fullwidth seven then `7,500,000` passed against
    the reading `7,500,000`, because that glyph counted as nothing. A superscript digit is not
    decimal, so `1,234¹` to `1234` still passes.
  - `split_numeric_runs` returns a word that holds `(cid:` unchanged. Before, `(cid:21)5` split
    after its `)`, and the child `5` read as `Amount 5`. Design section 15, step 4, makes such a
    word `Unreadable`, and ten of the twenty editions that step 5 parses extract their grid
    fonts as `(cid:N)` codes.
  - A `)` that digits follow is a sign problem, so `(1).23` and `(1)2` give `sign` where they
    gave `grouping`. The design already named a misplaced parenthesis.
  - The design, the `lex_cell` docstring and the reason table of Appendix E now say that
    `grouping` covers a misplaced mark, such as `2*42,096`, as the code did.
  - Five mutants of `lex.py` passed the tests of `d9d15ed0`. They are a reader that applies
    the `Decimal` context to its result, one that builds `-Decimal(digits)`, a
    `transliteration_ok` that lets a reading drop the last digit, a reader that reads a
    one-digit percent as negative, and a lexer that gives a dash in a one-decimal column the
    meaning zero. Each now fails a test. The round trip draws the sign apart from up to 41
    digits and names `-0.00` and `12345678901234567890.123456789` in every printed form.
- **Step 2: the lexer refuses a font code as a digit and a join after a `$` word** (November 23,
  2026, S2-D fix round 2, found in the second Codex review of S2-D). Each change has a test that
  failed before it. Design section 3.1 and the S2-D boxes and Appendix E of
  `docs/plans/step-02.md` say the same.
  - `transliteration_ok` fails when `seen` holds `(cid:`. Before, it counted the `d` of `cid` as
    a zero and the code number as digits, so `10(cid:28)` passed against `10028` and failed
    against `109`. Codex reports that `pdfplumber` extracts that word on page 1 of the FY2023 Q1
    positions report (`qcmr/positions/FY23_Q1.pdf`), where the page prints 109. That is Codex's
    statement, since `pdfplumber` is not installed here until step 4. A font code is no evidence
    of any digit, so no reading can be checked against a cell that holds one. Such a cell can
    only be accepted as null, or repaired by the font repair of step 4.
  - A pair of parentheses leaves for a join only when it wraps the whole cell, so a `$` word
    before it stops the join. Before, `$ (1 23,456)` read as -123456, `$ (1.2 3)` as -1.23 and
    `$ (67,215,504.0 0)` as -67215504.00. A `cmp`-checked copy of the old `parse_amount` and
    `parse_decimal` returns `None` for each, and Appendix E says no shape joins such a cell. They
    are now `Unreadable two_tokens`. `test_no_cell_joins_that_both_old_readers_refuse` holds 30
    cells, a `$` word or none, three join forms and five sign forms, with all three readers'
    results. Over 448 join cells with every minus glyph and `$` position, these `$ (` cells were
    the only ones that both old readers refuse and the lexer read as an amount. Over 1,183,744
    lexings of generated cells in four columns on both sources, the fix changed the result of
    `$ (` joins only. `-$1.2 3` and `-$67,215,504.0 0` still read as amounts, with any minus
    glyph. The old `parse_decimal` joins them and the old `parse_amount` refuses them.
  - Two mutants of `lex.py` passed the 45 tests of `0603fce3`: one that reads an OCR `(3.0)` as a
    positive text-layer 3.0, and one that keeps only the first word's text and ref in every
    `Unreadable`. The round trip now draws the page's source and asserts that the `Amount` keeps
    it, and the digits property checks the sign in both directions.
    `test_a_cell_keeps_the_text_and_ref_of_every_word` and the probe test assert that an `Amount`
    and an `Unreadable` keep the text of every word joined by one space and every word's ref, so
    row 53, `(29 1)`, keeps both words. In a scratch copy, each mutant fails the new tests.
- **Step 2: the lexer reads a raised `1*` as one mark and a dash from whole words** (November
  23, 2026, S2-D fix round 3, found in the third Codex review of S2-D). Each change has a test
  that failed before it. Design section 3.1 and the S2-D boxes and Appendices C and E of
  `docs/plans/step-02.md` say the same.
  - A raised footnote that extraction returns as one word, `1*`, passes the same size and
    position test as a lone raised digit, and the whole word is one mark as it prints. Before,
    the lexer found no raised digit in `1*`, stripped the `*` and joined the `1` to the fraction
    through join shape 2. So `2.8 1*` read as 2.81 with the mark `*`, while the same marks as
    two words, `1` and `*`, gave 2.8. Both layouts now give `Amount 2.8`, for every digit and
    mark glyph. A raised word of two digits and a mark glyph stays a token, as before.
  - A last word of one digit with mark glyphs after it that is not small and raised reads only
    alone or after one `$` word, so no join takes it. Join shape 2 ends in one digit, and `1*`
    as printed is not one. Before, `2.8 1*` at full size read as 2.81. It is now
    `Unreadable two_tokens`, and so are `1.2 3²`, `1.2 3*` and `67,215,504.0 0¹`. A lone `1*`
    and `$ 1*` still read as 1 with the mark `*`. A shape 1 join keeps a mark glued to its last
    word, so `1 23,456¹` still reads as 123456.
  - One word `N/A` or `NA` gives `NotApplicable`, and one dash word, alone or after one `$`
    word, gives a `Dash`. Before, one word whose text was `$ -`, with the space inside it, read
    as a `Dash`, and `has_values` of S2-C was false for its line. It is now
    `Unreadable not_a_number`. `test_a_lexed_value_is_a_value_word` now also draws each cell as
    one word that holds its spaces. The `N/A` rule gives the same results as before, since two
    words joined by a space never equal `N/A` or `NA`.
  - Appendix E said that no shape joins a cell that both old readers refuse. Both old readers
    refuse every cell with a superscript mark, row 52 included, which the owner accepted as an
    `Amount`. So the sentence now compares the cell without its marks, in Appendix E, in the
    risk "No lexer rule has met a page" of Appendix C, and in the design.
    `test_no_cell_joins_that_both_old_readers_refuse` gains 16 marked cells, each with the
    results of a `cmp`-checked copy of the old `parse_amount` and `parse_decimal` on the cell
    without its marks. On the marked text the old readers differ in both directions. They
    refuse `1 23,456¹`, and they join `1234.5 6 *` into 1234.56 while they refuse `1234.5 6`.
  - `test_amount_digits_are_the_digits_of_its_words` drew a raised `1` or none. With the
    raised-digit rule changed in a scratch copy to take only the digit `1`, a raised `2` turned
    `2.8` into 2.82 and the 48 tests of `fae7e17` passed. The property now draws the raised
    word from all ten digits, with and without a mark glyph after it. In a scratch copy of the
    fix, that mutant still passes the 48 old tests and fails the property on `2.8` with a
    raised `2`.
  - Over 973,752 lexings of generated cells, one to three words from 39 texts, at full size or
    with a small raised last word, in four columns on both sources, the fix changed 4,232
    results from those of `fae7e17`. Each change is one of the three above or a change of
    `Unreadable` reason, and no new `Amount` holds a digit that its words less their marks do
    not print.
- **Step 2: `reading_for` takes the page's words, and `records` states its findings**
  (November 23, 2026, S2-E). Design section 3.1 gave `reading_for` a page number, which every
  word's ref already carries, and section 2.1 makes a reading stale when the words inside its box
  stop joining to `seen`. The function could not see those words. It is now
  `reading_for(cell_words, page_words, source, readings)`. A reading is a candidate when its
  source matches and its box, with 1.0 point of slack, holds a cell word of its file and page.
  Two candidates give `duplicate_reading`. The page words the box holds must be exactly the
  cell's words and join to `seen`, else `stale_reading`, so a box over two cells of `7` is stale
  for both. `apply_reading` gives `reading_refused` for a cell that is not an `Amount` or an
  `Unreadable`, and for a reading that fails `transliteration_ok` or does not read as one signed
  number through the private reader of `lex.py`. It gives `stale_reading` when the cell's text
  differs from `seen`, so a record with `seen` "85.8" cannot put its value on a cell that prints
  `65.8`. A null reading on an `Amount` gives the reason `reviewed_null`. Every finding is BLOCK
  on the reading's page, with the subject `<doc sha8>:reading:<reading id>`, because neither
  function has the table name that the subject form of `Finding` needs. Two rules go past the
  plan's words. `apply_reading` also gives `stale_reading` when the cell's words are not on the
  reading's file and page, so a reading of page 4 never applies to a cell on page 5 that prints
  the same text: a human reading is a record with a page (`CLAUDE.md`, hard rule 4). With that
  test removed in a scratch copy, `test_a_reading_never_lends_its_value_to_another_cell` fails.
  `ReviewedReading` refuses an empty `id` with `ValueError`, because `Amount` refuses an empty
  `review_id` and `apply_reading` must not raise for a record that a file can hold. `records`
  imports no new outside name, so `PURE_IMPORTS` and the list in section 11.1 are unchanged.
  Design sections 2.1 and 3.1.
- **Step 2: a reading keeps footnote digits out, and one id names one record** (November 23,
  2026, S2-E fix round, found in the Codex review of `ce55ea9a` and the verification lanes).
  Each change has a test that failed before it, except the reworded page message of
  `apply_reading`. Design sections 2.1 and 3.1 and the S2-E boxes of `docs/plans/step-02.md` say
  the same.
  - `apply_reading` checks a reading against the cell's text less the mark words that end an
    `Amount`, and the reviewed `Amount` keeps the cell's marks. The whole-word marks of an
    `Amount`, such as a small raised digit, a backtick or `*`, are the last words of its text,
    in order. Before, a review of `$ 2.8` with a small raised `1` refused `2.8` and accepted
    `2.81`, so a footnote digit entered the number (VAL-Q28), and every reviewed `Amount` had no
    marks. A mark inside a word, such as the `*` of `242,096*`, holds no digit, and a reading
    still drops it. An `Unreadable` has no marks, so a reading keeps its whole text (the note
    "What a reviewed reading can still do").
  - `ReviewedReading` refuses an empty `reason`, because a human reading is a record with a page
    and a reason (`CLAUDE.md`, hard rule 4). Before, a reading with no reason changed `2918` to
    `291.8`. `DashRule` refuses an empty `id`, so a `Dash` that a rule sets to zero can name the
    rule. `CellRecords` refuses two readings with one id and two dash rules with one id, because
    `Assembly.used` holds ids and a used id must name the record that was used. Fix round 2
    refuses a reading and a dash rule that share an id too (the entry below). The opening of
    design section 2.1 now names a record file's reasons beside its ids.
  - `reading_for` counts the words the box holds against the cell's words, and joins the cell's
    words in the order given, which is the order `lex_cell` joins a cell's text in. Before, it
    compared sets, so one word given twice passed as the cell, and it joined the held words by
    left edge, then ref. `group_lines` orders two words with one left edge by their bottoms, so
    a cell printed `8 7`, `reading_for` joined `7 8`, and no reading of that cell could pass.
  - The `stale_reading` message of `reading_for` names the words in the box and the cell's
    words, or the cell's text and `seen`. Before, for a box over two cells of `7`, it said that
    the second cell's words read the first cell's `seen`. The page message of `apply_reading`
    says that a word of the cell is not on the reading's file and page.
  - Two rules that the design's comments state and this file did not. With two or more
    candidates, `duplicate_reading` takes the subject of the least id and its message names
    every id. No column format applies to a reading, so the reading `29.18` of `2918` gives a
    reviewed `Amount` of 29.18 in a one-decimal column.
  - New tests fail seven mutants of `records.py` that passed the tests of `ce55ea9a`: the null
    reading checked before the stale tests, the page checked without the file, one word of the
    cell on the reading's page taken as enough, the cell's words joined by ref or by left edge,
    and a slack of 0.6 or 1.9. Three tests show that a reading cannot drop or add a decimal
    digit of another script, such as a fullwidth one before `,234` read as `234`, which S2-D
    fixed in `transliteration_ok`.
- **Step 2: one id names one record of either kind, and a blank id or reason is no id or
  reason** (November 23, 2026, S2-E fix round 2, found in the second Codex review of S2-E, at
  `61704909`, and the verification lanes). Each change has a test that failed before it. Design
  section 2.1 and the S2-E boxes of `docs/plans/step-02.md` say the same.
  - `CellRecords` refuses an id that two of its records share: two readings, two dash rules, or
    a reading and a dash rule. `Assembly.used` is one `frozenset[str]` of ids, so before, a used
    reading `d1` made an unused dash rule `d1` look used, and no `unused_record` finding could
    name the rule.
  - `ReviewedReading` refuses an `id` or a `reason` that is empty after `strip()`, and `DashRule`
    such an `id`. Before, a reason of two spaces and a tab let a reading change `2918` to
    `291.8`. The tests try a space, a tab and a newline.
  - A font code cannot become a reviewed number. The count cell `10(cid:28)`, read as `109` or as
    `10028`, gives `reading_refused` through `reading_for` and `apply_reading`, and a null reading
    of it is accepted. Codex found the word on page 1 of the FY2023 Q1 positions report, where
    the page prints 109. S2-D fixed `transliteration_ok`, and this round adds the records test.
    With the S2-D check removed in a scratch copy, the tests of `61704909` pass and the new test
    fails.
  - Four mutants of `records.py` passed all 191 tests of `61704909`, and each now fails a new
    test: removing only the last mark word, removing the mark words wherever they appear in the
    text, joining the cell's words by left edge, and comparing only how many words the box
    holds. So a cell of `2.8`, a raised `1` and a `*` reads as `2.8` with both marks. A cell of
    `$`, `10` and a raised `1` reads as `10`, where removing every ` 1` would leave `$0`. A box
    over `29` and a `7` on the next line is stale for the cell `29 1`.
- **Decisions 13 to 17 change five rules of section 3.1, to be built at step 5** (November 23,
  2026, after the step 2 run). The run left five questions for the owner, and he adopted its
  recommendations with the words "follow your recommendations". Design section 16 records them
  as decisions 13 to 17, each as he saw it. The recommendations were a few sentences each. What
  the run worked out afterward goes further, and in one place against a recommendation: section
  16.2 holds the exact reading rule, and section 16.3 sets each later piece beside what he
  adopted. He confirmed the reading rule of section 16.2 the same day, after the run told him
  it goes beyond and against his recommendation, with the words "I approve the detailed ruled".
  The other entries of section 16.3 wait for his confirmation. This entry changes no
  code. Section 3.1 keeps each rule as built, with a pointer to its decision, and the step 5
  plan schedules the five changes with their tests.
  - Decision 13, the reading rule. A reading may restore what extraction lost and nothing else.
    Section 16.2 states it as five clauses on the shape of the cell's words, and three tests
    that `apply_reading` and `reading_for` make from the source, the word boxes and the cell. A
    prototype of the five clauses and the source test, run outside this repository at
    `2638173a`, passes all 34 reviewed readings of the old repository and refuses the cases the
    note "What a reviewed reading can still do" and the Codex reviews recorded. The lexer test
    that reads `(59.8j` as `(59.8)` keeps passing, through the one `j` the rule allows. The rule
    took four forms. Three verifiers that built it from its words alone, and three Codex
    reviews, each found a hole or a wrong sentence in the text before, and section 16.2 lists
    them, with the questions the step 5 plan carries. One of those is for the owner: whether
    the size and gap test of decision 16 also covers the lexer's second join shape.
  - Decision 14, a raised footnote mark joins the line it sits on. Where two lines hold it, it
    joins the one whose bottom edge is nearer, and a tie leaves it a line of its own.
  - Decision 15, `N/A` in any case and `#DIV/0!` are value words, and U+2010 alone is a dash.
    The run proposes that U+2010 is also a minus glyph, which the owner has not confirmed. The
    Codex review of this entry found the minus sign:
    the FY2021 supplemental report prints U+2010 before 2.75 on page 15 and before 435.43% on
    page 18 (`pdftotext`, rerun). VAL section 3.2.1 pins `N/A` in upper case at row 28 and holds
    no row with `n/a`, U+2010 or `#DIV/0!` (a search of the table at `2638173a`).
  - Decision 16, the first join shape needs equal sizes and a small gap.
  - Decision 17, a bare digit ends a label as a mark only by its size or by the row schema.
