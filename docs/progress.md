# Build progress

The build order and each step's check are in `docs/design.md` section 15. Update this file in the
same branch as the work: status, the date the check passed, and anything a later session needs.

| Step | What | Status | Branch | Check passed |
|---|---|---|---|---|
| 1 | Workspace, tooling, purity and shape tests | check passed | `step-01/a-workspace`, `step-01/b-import-contracts`, `step-01/c-kit-shape`, `step-01/d-test-isolation` | November 22, 2026, runs 45093444380, 45094817250, 45094829990 and 45092206629 |
| 2 | Kit, words to cells | check passed | `step-02/a-import-pin`, `step-02/b-value-types`, `step-02/c-words-to-lines`, `step-02/d-lexer`, `step-02/e-records` | November 23, 2026, head `73d428e2`, run 45130645501 |
| 3 | Archive for the QCMR from FY2022 | not started | | |
| 4 | Words: PDF adapter with font repair, word cache, codec | not started | | |
| 5 | QCMR positions parser, registry, row schemas, column vocabulary | not started | | |
| 6 | Checks, gate and release for positions (first release-quality dataset) | not started | | |
| 7 | Older QCMR positions | not started | | |
| 8 | Cash, O-2, O-3, source comparison, `suggest` | not started | | |
| 9 | Monthly City and School collections | not started | | |
| 10 | Five tax families | not started | | |
| 11 | Budget in Brief | not started | | |
| 12 | Supplemental reports, one statement at a time | not started | | |
| 13 | `watch`, the reader, first full release | not started | | |
| 14 | QSMR, the held-out test of the kit | not started | | |

The step 1 check passed in four `pull_request` runs of `.github/workflows/ci.yml`:

- Clean: run 45093444380 at `d3a9477dad72aa38751277fd2d4f3ee684b49ce1`, the head of
  `step-01/d-test-isolation` after the restack and before the commit that set this row. Every
  gate passed on Python 3.12 and 3.14.
- C2: run 45094817250 at `57b19ab8a77c2756903ea7479706838000c477ce`, with `import boto3` planted
  in `datadesk.core`. The `uv run lint-imports` step failed with `datadesk core is pure BROKEN`.
- C3: run 45094829990 at `b843fa8f426df090c28213c6bf6898d5b83bb935`, with a `bool` parameter
  planted in `checkedtables`. The `uv run pytest` step failed with `AssertionError: planted`.
- C4: run 45092206629 at `71a76f3d16b74a8bb5c604dac03a3c170f7d8636`, with a `socket.socket()`
  call planted in a core test. The `uv run pytest` step failed with `SocketBlockedError`.

The three plant runs came from temporary pull requests 14, 15 and 13, which are closed. Each plant
is one commit on a stack head. C2 ran on `8979428`, the final head of
`step-01/b-import-contracts`, and C3 on `7189a67`, the final head of `step-01/c-kit-shape`. C4
ran on `b4eda02` of `step-01/d-test-isolation`, which has the same patch id as `d3a9477`, the
restacked S1-D head that the clean run used.

## Deviations from the design

Each entry: step, what changed, why, and the design section updated.

- **Step 1: the helper contract forbids the 20 table modules** (November 22, 2026, S1-B). The
  contract "family helpers do not import table modules" forbade only
  `datadesk.core.tables.catalog`. A planted `from datadesk.core.tables import birt` in
  `qcmr_common.py` kept all eight contracts. With the 20 table modules of the independence
  contract added to `forbidden_modules`, the same plant breaks the helper contract. The QSMR table
  modules join the list in step 14, and `qsmr_common` joins the sources. Design section 12.5.
- **Step 1: import-linter forbids listed standard-library modules** (November 22, 2026, S1-B).
  The design marked this "Not verified". Planted one at a time in `datadesk.core`, `import os`,
  `from pathlib import Path`, `import logging`, `import time` and `import random` each broke
  `datadesk core is pure` under import-linter 2.16. Section 12.5 now states the result, and the
  item leaves the list in section 17.4.
- **Step 1: a test fails a source folder with no `__init__.py`** (November 22, 2026, S1-B, found
  in the Codex reviews). import-linter does not scan a folder with no `__init__.py`, and Python
  still imports the modules in it. With `import subprocess` and `RUN = subprocess.run` in a new
  `datadesk/core/sneaky/mod.py`, `uv run lint-imports --no-cache` printed `Contracts: 8 kept, 0
  broken.` and `uv run ruff check .` passed. `test_source_folders_are_packages` in
  `tests/test_gates.py` now fails, naming the folder, when a folder under the three
  `packages/*/src` trees holds a `.py` file, directly or below it, and has no `__init__.py`. It
  first proves its own check on small trees. A first fix used ruff's `INP001`. The build dropped
  it because ruff passed two modules. For `core/reports/probe.py` with `import boto3` and
  `SDK = boto3`, ruff reported `INP001`, and with `#!/usr/bin/env python3` as the first line it
  printed `All checks passed!`. Ruff also passed `import subprocess` in `core/venv/mod.py`, a
  folder it excludes by name, with all eight contracts kept. Design section 12.5.
- **Step 1: the pure packages forbid `importlib`** (November 22, 2026, S1-B, found in the Codex
  review). With `from importlib import import_module` and `import_module("boto3")` in
  `datadesk/core/tables/birt.py`, `uv run lint-imports --no-cache` printed `Contracts: 8 kept, 0
  broken.` The contracts `checkedtables holds no I/O and no Philadelphia` and `datadesk core is
  pure` now forbid `importlib`, and the same plant breaks `datadesk core is pure`. The design
  never uses `importlib`, `import_module` or `__import__`. The purity test that S1-D writes
  reports a call to the builtin `__import__`. Design section 12.5.
- **Step 1: the shape test fails on `bool | None` and `Optional[bool]`** (November 22, 2026,
  S1-C). The design's assertion, `p.annotation in (bool, "bool")`, passed `flag: bool | None` and
  `flag: Optional[bool]`, which `CLAUDE.md` hard rule 5 bans. Section 11.4 now asserts
  `not bool_parameters(fn)`. `bool_parameters` names a parameter whose annotation is `bool` or a
  union with `bool` as a member. Planted in `checkedtables/lex.py`, both forms fail the test,
  with and without `from __future__ import annotations`, and `tuple[bool, ...]` and `int | None`
  pass. The first version read annotations through `inspect.signature(fn, eval_str=True)`. The
  Codex review of the step 1 stack found that it passed `flag: Optional["bool"]`, whose quoted
  `bool` stays a `ForwardRef`, and raised `NameError` on `def valid() -> "Decimal"` with
  `Decimal` imported only under `TYPE_CHECKING`. `bool_parameters` now evaluates each parameter's
  annotation and each union member in the function's globals, where a name that does not
  resolve stands for an unknown type, and it never reads the return type. Planted in scratch
  copies, `Optional["bool"]` fails the test, a module that uses such a `Decimal` in a parameter
  and a return type passes, and the same module fails once a function in it takes `flag: bool`.
  Design section 11.4.
- **Step 1: the shape test reads private re-exports, constructors and inherited members**
  (November 22, 2026, S1-C, found in the build and in the Codex review). `public_functions` kept
  an object only when its `__module__` was the public module being read, and it skipped every
  name that starts with `_`. So a public name could reach a `bool` parameter the test never read.
  Before the change, `uv run pytest packages/checkedtables/tests/test_library_shape.py` printed
  `4 passed` with `def parse(flag: bool)` in a new `checkedtables/_impl.py` and
  `from checkedtables._impl import parse` in `checkedtables/__init__.py`. It printed `4 passed`
  again for a public class in `words.py` whose `__init__` takes `strict: bool`, and for one whose
  `__init__` takes five parameters. Now an object counts when a public name in a public module
  reaches it and its `__module__` is the scanned module or a module under it, and a public class
  that is not a dataclass has its own `__init__` checked without `self`. All three plants fail,
  and a dataclass with five pinned fields passes. The test still read `vars(cls)` only, so
  `class Reader(_Base): pass` passed with `def read(self, strict: bool)` on a private `_Base`,
  and the same held for an inherited `__init__`. A public class's methods and its `__init__` now
  include those it inherits from a base class in the scanned package, private or not, each read
  once as the class resolves it, and a base outside the package adds nothing. Planted in scratch
  copies, the inherited method, the inherited `__init__` and an inherited method with five
  parameters each fail, and a subclass of `json.JSONEncoder`, whose `__init__` takes eight
  parameters, passes. Design section 11.4.
- **Step 1: the purity scan reports `builtins`, `__import__` and mutable module state**
  (November 22, 2026, S1-D, found in the Codex review and the build). The design's scan lists
  eight names. With `impurities` cut back to those eight, `uv run pytest tests/test_purity.py`
  passed with `builtins.open("x")`, `__import__("boto3")` and `CACHE: dict[str, str] = {}`
  appended to `checkedtables/words.py`. `CLAUDE.md` hard rule 3 says the purity test enforces the
  ban on mutable module state, and `__import__` gets past the `importlib` ban of S1-B with no
  import. The scan now also reports any import of `builtins` or read on it, a call to
  `__import__`, and a module-level assignment of a list, dict or set display, a comprehension of
  one, or a call to `list`, `dict`, `set` or `bytearray`. `__all__` gets no exemption, so a
  package writes it as a tuple. The same three lines now fail the test. The Codex review of the
  stack found that the scan read only the direct children of the module body. With
  `if __debug__:` and `CACHE = {}` under it, a `try:` block that holds `CACHE = {}`, or
  `CACHE, SEEN = {}, set()` appended to `checkedtables/words.py`,
  `test_pure_packages_have_no_effects` passed. An `if` opens no scope, so each makes mutable
  module state. The scan now reads every assignment at module scope, inside any nesting of `if`,
  `try`, `with`, `for`, `while` and `match` blocks but not in a function or class body, and it
  counts a tuple that holds a mutable display or call. Each of the three forms now fails the
  test, and a list assigned inside a function passes. Design section 11.1.
- **Step 1: an audit hook refuses socket events, and each core test module starts in an empty
  folder** (November 22, 2026, S1-D, found in the Codex review of the stack). pytest-socket
  replaces only the names `socket.socket`, `socket.getaddrinfo` and `socket.gethostbyname`, and
  its teardown hook lifts the block before fixture finalizers run. In
  `packages/datadesk/tests/core`, a test that called `socket.SocketType()` passed, and so did one
  that called `_socket.socket()` and a module-scoped fixture that called `socket.socket()` after
  its `yield`. A module-scoped fixture there also found `pyproject.toml` in the working
  directory, because `_empty_working_directory` has function scope. The root `conftest.py` now
  installs an audit hook that raises `SocketBlockedError` for `socket.__new__`,
  `socket.getaddrinfo`, `socket.gethostbyname`, `socket.gethostbyaddr` and `socket.getnameinfo`
  unless the running test carries the `enable_socket` marker. Both package `conftest.py` files add
  a module-scoped fixture that moves each test module into an empty folder. The three plants now
  fail with `SocketBlockedError`, and the fixture finds no `pyproject.toml`. Design section 11.1.
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

## Notes for later sessions

Things learned while building: surprises in the PDFs, commands that matter, traps.

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
  out of `kit_dataclasses`.
- **`assemble` passes the words of the cut page to `reading_for`, a note for the step 5 plan**
  (November 23, 2026, step 2, S2-E). `reading_for` compares the page words its box holds with
  the cell's words as values. So `assemble` passes the words the cells were cut from, after any
  `split_numeric_runs`, and not the page's raw words. Probed at S2-E: for "TAX434,605,553" on an
  OCR page, a reading around the child "434,605,553" gives `stale_reading` with the raw word as
  `page_words`, and the reading itself with the two children.
- **The loader's digit check and a footnoted reading disagree, a note for the step 5 plan**
  (November 23, 2026, step 2, S2-E fix round 2, finding 3 of the second Codex review of S2-E).
  Design section 3.2 says that `load_records`, which step 5 builds in `datadesk`, refuses "a
  reading whose digits fail transliteration_ok" (`docs/design.md`, lines 2069 and 2070 at the
  S2-E head). The loader has only the record's text, so it cannot tell that the last `1` of the
  footnoted cell `$ 2.8 1` is a small raised mark. Run in a scratch copy of `64560f3`:
  `transliteration_ok("$ 2.8 1", "2.8")` is false, and `apply_reading` gives that cell, an
  `Amount` with the mark `1`, a reviewed `Amount` of 2.8 that keeps the mark. The reverse also
  holds: `transliteration_ok("$ 2.8 1", "2.81")` is true, and `apply_reading` gives
  `reading_refused`. So the loader as the design words it would refuse a record that the
  cell-level check accepts, and pass one that it refuses. The step 5 plan decides: either the
  loader leaves the digit check to `apply_reading`, or the record carries what the loader needs.
- **`uv.lock` and `exclude-newer`** (November 22, 2026, step 1). The owner's uv config and
  `UV_EXCLUDE_NEWER` set `exclude-newer = "1 week"`, and `uv lock` records that span in
  `uv.lock`. A machine without the setting, such as a CI runner, rejects the lock: `uv lock
  --check` exits 1 with "removal of global exclude newer". The root `pyproject.toml` sets the
  same span under `[tool.uv]`, so the lock checks the same everywhere. Change both together.
  `UV_NO_CONFIG=1` and `UV_CONFIG_FILE` also drop that `[tool.uv]` table. Under either,
  `uv lock --check` fails when `UV_EXCLUDE_NEWER` is not set in the environment, and exits 0
  when it is. To test the lock without the owner's config, read the CI run's `uv sync --locked`
  step.
- **46 empty modules** (November 22, 2026, step 1, S1-B). import-linter refuses a contract that
  names a module that does not exist (`Module 'checkedtables.checks' does not exist.`, exit 1),
  and a wildcard that matches nothing keeps its contract with no warning. So the modules that the
  eight contracts name exist as empty files: 14 in `checkedtables`, 6 in `phillyledger` and 26 in
  `datadesk.core.tables`. Later steps fill them. Deleting one breaks `uv run lint-imports`.
- **ruff skips Markdown** (November 22, 2026, step 1). ruff 0.17 includes `*.md` by default and
  formats the Python blocks in it. `uv run ruff format --check .` failed on `docs/design.md`,
  whose code blocks align their comments on purpose. The root `pyproject.toml` excludes `*.md`.
- **`ci.yml` is pinned** (November 22, 2026, step 1). `test_ci_runs_every_gate` in
  `tests/test_gates.py` fails unless `.github/workflows/ci.yml` equals, byte for byte, a header
  constant plus one step per member of `GATES`. A workflow change edits both files in the same
  pull request. A new gate joins `GATES` and gets its step at the end of `ci.yml`. A scan for
  forbidden strings, tried first, let eight broken workflows pass. The `Kit size report` step is
  not a gate, so it sits in the pinned header, after `Python version`.
- **The shape pins grow with the kit** (November 22, 2026, step 1, S1-C. Updated November 23,
  2026, S2-B). In `packages/checkedtables/tests/test_library_shape.py`, `FIELD_SNAPSHOT` started
  as `{}` and `test_bool_fields_are_page_facts_only` expected `set()`. S2-B pins the fields of
  its 18 dataclasses, each in the commit that creates the class, and the bool test now expects
  `{("Word", "bold")}`. The pull request that adds a kit dataclass adds its fields to
  `FIELD_SNAPSHOT`. The one that creates `Column` adds `("Column", "printed")`.
  `kit_dataclasses` counts every dataclass of `checkedtables` that a public name in a public
  module reaches, so `RawRow` counts when step 5 creates it. The `RawRow.bold` note above is
  still the owner's call.
- **Kit types imported only under `TYPE_CHECKING`** (November 22, 2026, step 1, S1-C). The shape
  test evaluates a parameter's annotation with each name that does not resolve at run time
  standing for an unknown type. So `amount: "Decimal"`, with `Decimal` imported only under
  `TYPE_CHECKING`, neither raises nor counts, `flag: "bool | Decimal"` still counts as a `bool`
  parameter, and the return type is never read. Dataclass fields still go through
  `typing.get_type_hints`. A kit dataclass with the field `amount: "Decimal"` and that import
  fails `test_bool_fields_are_page_facts_only` with `NameError`, so import a field's type at run
  time.
- **`test_closed_lists_are_pinned` is not written yet** (November 22, 2026, step 1, S1-C. Updated
  November 23, 2026, S2-B). None of the lists it pins exists at step 1. Each list's pin lands in
  the pull request that creates the list, in the same test file (`CLAUDE.md`, hard rule 6). S2-B
  creates the `StrEnum` classes `SourceKind`, `ValueKind`, `DashMeaning`, `Presence`,
  `PercentSign`, `Reading` and `Severity`, and the `Cell` union. Design section 11.4 pins none of
  them, so the test is still not written.
- **Every test runs with sockets blocked** (November 22, 2026, step 1, S1-D). `--disable-socket`
  and the audit hook in the root `conftest.py` apply to every test, so a later adapter contract
  test that needs the network opts in with the `enable_socket` marker of pytest-socket. The
  marker reopens calls to `socket.socket()`, and an unmarked test after a marked one is blocked
  again. The marker is the only way in. The audit hook reads the marker alone, so a test that
  asks for pytest-socket's `socket_enabled` fixture still fails with `SocketBlockedError`. A name
  that a module binds with `from socket import socket` stays blocked under the marker, because
  the root `conftest.py` installs pytest-socket's block before that import runs. Probed at S1-D,
  under the marker `socket.socket().close()` passes and the early-bound `socket().close()` fails
  with `SocketBlockedError`.
  - pytest-socket 0.8.1 replaces only the names `socket.socket`, `socket.getaddrinfo` and
    `socket.gethostbyname`, and lifts its block before fixture finalizers run. The audit hook
    covers the rest. In a core test, `socket.SocketType()`, `_socket.socket()`,
    `pytest_socket._true_socket()`, a reloaded `socket` module, `_socket.getaddrinfo`,
    `_socket.gethostbyname`, `socket.gethostbyname_ex`, `socket.getnameinfo`, the
    `socket.gethostbyaddr` audit event, and a socket opened after the `yield` of a function- or
    module-scoped fixture each fail with `SocketBlockedError`. `socket.gethostname()` and
    `platform.node()` still work. The probes used unconnected sockets, numeric loopback input
    with numeric flags, and `sys.audit` for `gethostbyaddr`.
  - Two routes still pass. CPython raises no audit event for `_socket.socketpair()`, which makes
    a pair of local sockets, and a subprocess that a test starts opens sockets freely.
  - pytest runs a session-scoped fixture's finalizer inside the last test's protocol, so when
    that test carries `enable_socket`, the finalizer can open a socket even though an unmarked
    test requested the fixture. Probed at S1-D on an unconnected socket, the finalizer opened it
    and the run ended `5 passed`, and with the marker removed it failed with
    `SocketBlockedError` at teardown.
  - A class that a module defines on `socket.socket` keeps the block for the whole session when
    the module is first imported after the root `conftest.py` blocks sockets. `ssl` is one.
    `ssl.SSLSocket` subclasses pytest-socket's guard, so under the marker
    `ssl.create_default_context().wrap_socket(...)` fails with `SocketBlockedError`. With
    `import ssl` at the top of the root `conftest.py`, the same probe passes and the isolation
    tests still pass. Probed at S1-D with the audit hook in place, on an unconnected socket. The
    first contract test that needs TLS makes that change.
  - Each blocked call also prints the `UserWarning` that `SocketBlockedError` issues when it is
    created, so `uv run pytest` reports six warnings, one per blocked call in the isolation
    tests.
- **A core test's package- or session-scoped fixture sees the checkout** (November 22, 2026,
  step 1, S1-D). `_empty_module_working_directory` gives each core test module an empty folder,
  but pytest sets up a package- or session-scoped fixture first, so one that a core test requests
  still runs in the checkout. Probed at S1-D, fixtures of session and package scope found
  `pyproject.toml` in the working directory, and one of module scope did not.
- **The pure packages can still reach effects the gates do not name** (November 22, 2026, step 1,
  S1-D, found in the Codex review of the stack and the build. Rewritten November 23, 2026, S2-A).
  At step 1, ten plants each passed every gate when planted alone in
  `datadesk/core/tables/birt.py`. The forbidden lists and the purity scan named specific modules
  and calls, and every review found more. The owner chose an allow-list on November 23, 2026, and
  S2-A pins it (see Deviations). Each plant was run again in a scratch copy of the S2-A head. The
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
- **Follow-ups after step 1** (November 22, 2026). The step 1 run found these and did not fix
  them.
  - Nothing tests a gate's own settings. In scratch copies of the S1-D head, each of
    `--collect-only` in pytest's `addopts`, a root `conftest.py` hook that skips every test,
    `"*.py"` in ruff's `extend-exclude` and `"**"` in ty's `exclude` made its gate pass on a plant
    it had failed, with `uv run pytest` exiting 0. The `verify-step` audit for weakened checks
    reads each diff for these settings.
  - Only the gates behind C2, C3 and C4 have a planted test. The ruff check, ruff format and ty
    gates failed on a plant only in temporary pull requests at S1-A: runs 45077882205 (`F401`),
    45077856003 (a file to reformat) and 45077874284 (`invalid-assignment`).
  - A checkout with `core.autocrlf=true` fails `test_ci_runs_every_gate`, because Git writes
    `ci.yml` with CRLF line endings and the test compares bytes (see "`ci.yml` is pinned").
    `git -c core.autocrlf=true cat-file --filters HEAD:.github/workflows/ci.yml | file -` prints
    `CRLF line terminators`. A `.gitattributes` rule that keeps the file LF would fix it at the
    cause.
  - CI does not pin uv. `setup-uv` found no version in `pyproject.toml` and installed the latest,
    uv 0.13.9, where the lock was written with 0.13.6.
  - Codex reviewed the stack once, at `76aa7250`, before the last fix round. Verifier lanes checked
    the socket audit hook, the shape test's new annotation and inheritance handling, and
    `test_source_folders_are_packages`, and Codex did not review them. The owner landed the stack on
    November 23, 2026 without a second pass.
  - `.claude/skills/codex-review/run.sh` takes the reference repository's path from the parent of
    the checkout. From a worktree under `.claude/worktrees/`, it names a
    `.claude/worktrees/gov-budget-data` that does not exist.
  - The import contracts, the purity scan and the shape test name specific modules, calls and forms.
    Appendix C of `docs/plans/step-01.md` lists the limits found, and the note above records the
    owner's choice of an allow-list.
- **How step 1 landed** (November 23, 2026). The owner told the agent to merge the four pull
  requests, and they landed in order as squash commits `fa0eb1d` (#1), `fe83e1e` (#6), `db9ccd6`
  (#8) and `c22c101` (#10). After each squash, `main` had the tree of the head that landed, which is
  the base the next pull request was built on. So a merge of `main` into the next branch with
  `-s ours` moved it onto `main` with no force-push and no change to its tree. Each landing checked
  that the branch was at its verified head, that its patch id was unchanged, and that CI passed on
  the head that landed. The push run of CI on `c22c101`, run 45096500670, passed on Python 3.12 and
  3.14. The owner also kept the build's other choices: the byte pin of `ci.yml`,
  `exclude-newer = "1 week"` and the ruff exclusion of `*.md`. Hard rule 9 in `CLAUDE.md` is
  unchanged. During step 1, fresh owner agents force-pushed, with a lease, branches that an earlier
  agent had created, which crosses the rule's letter. Any change to the rule is the owner's to make.
- **Hard rule 9 changed** (November 23, 2026). The rule said agents never merge. The owner told
  agents to merge the four step 1 pull requests, pull request 16 and pull request 12, then asked
  for the rule to match. An agent now merges a pull request only when the owner tells it to, in
  that session and for that pull request, at the verified head with CI passing. The clauses on
  pushing to `main` and on force-pushing are unchanged, so the force-pushes in the note above
  still cross the rule.
- **Hypothesis writes nothing in the checkout** (November 23, 2026, step 2, S2-B). The root
  `conftest.py` registers and loads one profile with `database=None`, `derandomize=True` and
  `deadline=None`, so every machine draws the same examples. A wider search is a command a person
  runs with another profile. Hypothesis 6.170.15 still writes `.hypothesis/constants` under the
  working directory it was imported in, and its pytest plugin starts the writes during
  collection, so `pytest_configure` points it at a temporary folder with
  `set_hypothesis_home_dir` and `pytest_unconfigure` removes the folder. When the folder could
  not be made, teardown has nothing to remove and leaves the first error to show.
  `test_hypothesis_writes_nothing_in_the_workspace` in `tests/test_gates.py` runs a property test
  in a workspace copy and fails when a `.hypothesis` folder appears there.
- **Docstrings put `refs` past its estimate** (November 23, 2026, step 2, S2-B). The kit size
  report counts every line that is not blank or a comment, docstrings included. At the S2-B head
  it prints 592 lines. At the S2-E head after its fix round 2 it prints 1,420, and `records`
  counts 239 lines against its estimate of 140, and 115 without docstrings. Against design
  section 12.1: `refs` 121 (estimate 60), `kinds` 29 (40),
  `words` 147 (90), `labels` 25 (30), `cells` 108 (90). `columns` holds 49 lines for two of its
  ten names (330). `table` holds 113 lines (190) for two of the eight names its row lists,
  `RowKey` and `Finding`, and for `Severity`, which the row does not list. Without docstrings
  `refs` is 62 lines, `words` 65, `cells` 50 and `table` 58. The numpy docstrings on each public
  class and method, magic methods included, are 308 of the 592 lines. By module their share runs
  from 28 percent in `kinds` to 64 percent in `labels`. `refs` also writes four comparison
  methods for `WordRef`. The five whole modules hold 430 lines against an estimate of 310. If
  the other modules run as far past theirs, the kit passes its 3,800 line budget, an inference
  that no run has checked. The report never fails the build, so the owner decides whether the
  budget counts docstrings.
- **Five more kit modules against their estimates** (November 23, 2026, step 2, S2-E fix
  round 3). The same count as the note above, at `f82950e`, with and without
  docstrings, against design section 12.1: `testing` 91 and 51 (estimate 90), `text` 118 and 52
  (150), `lines` 122 and 52 (120), `lex` 269 and 181 (230), `records` 239 and 115 (140). The
  five hold 839 lines against an estimate of 730, and 451 without docstrings. With docstrings,
  `records` runs 99 lines past its estimate and `lex` 39. `testing`, at 91 lines against 90, and
  `lines`, at 122 against 120, are over their estimates too, by one line and by two, and a
  count at `73d428e2` gives the same two numbers. Without docstrings, each of the five is at or
  under its estimate. `uv run python packages/checkedtables/tests/test_library_shape.py` prints
  `checkedtables: 1431 lines (budget 3,800), 0 public names (budget 140)`, the sum of these
  five and the seven modules of the note above.
- **What an OCR word carries, a note for the step 4 plan** (November 23, 2026, step 2, S2-B).
  `Page` refuses a word with an OCR confidence on a text layer page. It does not refuse the
  converse states: a word on an OCR page with no confidence, or with a style, which the design
  says no OCR word has. Step 4 builds the adapters and learns what pdfplumber and Textract return
  for every word, so its plan decides whether `Page` refuses those states too, and records the
  choice in design section 2.1.
- **The kit checks a hash for presence only, a note for the step 4 and step 5 plans** (November
  23, 2026, step 2, S2-B). `WordRef`, `Page` and `Document` refuse an empty hash and take any
  other text, such as `"unknown"`. The old repository checks that a hash is 64 lowercase
  hexadecimal characters (`gov_budget_etl/models.py`, line 216). The kit does not. The adapter
  of step 4 computes each hash from a file's bytes, and the record lint of step 5 reads the hashes
  that records cite, so those two own the form of a hash. Their plans say where the form is
  checked.
- **A word that still holds a font code, a note for the step 4 plan** (November 23, 2026, step 2,
  S2-D fix round 2, found in the second Codex review of S2-D). Design section 15, step 4, says
  that a word still holding `(cid:` after repair lexes as `Unreadable`. At the S2-D head,
  `lex_cell` returns `Unreadable not_a_number` for `10(cid:28)` in a money, count or percent
  column, since `c`, `i`, `d` and `:` are no number's glyphs. It returns `Text` for the same word
  in a `YEAR`, `CODE` or `TEXT` column, because those columns give `Text` before any glyph is
  read. The sentence is part of step 4's own list, so the step 4 plan decides the rule for those
  three columns. `transliteration_ok` now fails against every reading of a `seen` that holds
  `(cid:`, so a reviewed reading cannot supply a digit that a font code hides, and such a cell can
  only be accepted as null. The step 4 plan also decides how a reviewed reading can supply a
  glyph that a font code hides, if the font repair leaves one.
- **What the step 2 rules do on real pages, for the plans of steps 5, 8, 10, 11
  and 12** (November 23, 2026, step 2, S2-C, found in the Codex reviews). Codex read three PDFs of
  `../gov-budget-data/data/phila/` with `pdftotext -bbox` and ran `group_lines`, `has_values` and
  `parse_label` on their word boxes at `8846f05`. The S2-C fix round reran the command (the
  block "PDF reproduction for findings 1-4" of `.codex-review/step-02-pr-8846f05c.md`) and
  printed the same eight lines. Real pages enter this repository's tests only as word fixtures
  that `datadesk fixture` writes, from step 4 on (`CLAUDE.md`, Tests), so S2-C changed none of
  the three functions for them. The boxes are those of `pdftotext`, not those of the adapter
  that step 4 builds.
  - A raised footnote mark leaves its row, for the step 5 plan and the owner. On page 2 of the
    FY2026 Q4 QCMR positions report (`qcmr/positions/FY26_Q4.pdf`), the mark of "Human Services
    (1)" is raised. The word `(1)` has top 357.95 and bottom 363.44, "Human" has bottom 367.62,
    and the tolerance of `group_lines` is 2.906, 0.35 of the median word height of 8.303. The
    mark's bottom is 4.18 above the row's, so `group_lines` makes `(1)` a line of its own. The
    run printed `(1) True` and `Human Services 438 1,059 1,497 532 1,323 1,855 448 1,045 1,493
    362 True`. So `has_values` is true for the lone mark, and `parse_label` never sees it with
    its label (QPOS-Q11). `group_lines` is the design's rule as written. FY2026 Q4 is one of the
    20 editions step 5 parses, so the step 5 plan tests this page with the real adapter's words
    and decides the rule. The same rule would keep a raised footnote digit out of its cell, and
    the lexer's rule for VAL-Q28 expects to find that digit in the cell. The second Codex review
    says that it reproduced this raised `(1)` and the lower-case `n/a` row below with `pdfplumber`
    word boxes as well (`.codex-review/step-02-pr-6442b4eb.md`, "What I checked"), which is Codex's
    statement and not a run of ours, because `pdfplumber` is not installed in this repository until
    step 4. The S2-D fix round reran the Codex command at the S2-D head on the words of
    `test_a_raised_digit_after_a_small_dollar_sign_is_a_mark`. Through `group_lines` they make two
    lines, and in a money column the run printed `'1' Amount 1` and `'$ 2.8' Amount 2.8`, so the row
    loses its mark and gains a value of 1. Given the three words as one cell, `lex_cell` returns
    `Amount 2.8` with the mark `1` and three refs, which is right for the words it gets, so the line
    rule and the raised-mark rule cannot both hold when a mark rises more than the line tolerance.
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
  - Join shape 1 joins two printed amounts, for the owner and the plans of steps 5 and 11
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
    that limit needs the real fixtures of step 5.
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
    predicate in `lines.py` is loose by design, and step 5 decides whether `lanes_from_values`
    needs a stricter one. Step 10 parses this report, and the RTT dossier finds a zone's columns
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
    `bold=True` and a word with no confidence (the note "What an OCR word carries"). `WordRef`,
    `Page` and `Document` accept the hash `"unknown"` (the note "The kit checks a hash for
    presence only", which also names the record lint of step 5). A subclass of `WordRef` with the
    same four fields as a ref on the page compares unequal to that ref, so `Page` holds both
    words.
  - The record lint of step 5 meets the record ids. `Dash` accepts an empty `rule_id`, and
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
- **What a reviewed reading can still do, for the owner and the step 5 plan** (November 23,
  2026, step 2, S2-E fix round, found in the Codex review of `ce55ea9a`). Each case below was
  run in a scratch copy of `f479ede`, and the fix round changed none of them.
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
    reads only as a number that ends in 1. `Unreadable` has no marks field. The step 5 plan
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
    `seen` holds a letter that is not a pinned confusable. When the step 5 plan writes
    `load_records`, it should run a tighter rule against the old repository's reviewed readings
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
- **Follow-ups after step 2** (November 23, 2026). The step 2 run found these and did not fix
  them.
  - Nothing ties the module table of design section 11.1 to `PURE_IMPORTS`. A pin can hold a pair
    from a module that the table does not list, and every test still passes. The Codex review of
    S2-A showed it with `from decimal import Decimal` in `words.py` and `decimal.Decimal` pinned,
    while the table said `none`. Until a test reads the table, the audit of each pull request
    checks it by hand against the modules in `PURE_IMPORTS`.
  - `package_sources` in `tests/test_purity.py` finds each pure package with `find_spec`, as it
    has since step 1. With a foreign `PYTHONPATH`, or an editable install that points at another
    checkout, it reads that checkout's sources. Every test imports the kit by name, so under that
    path the whole suite reads the other checkout, and the purity test agrees with the rest. The
    Codex review of S2-A at `c103b016` showed it with `PYTHONPATH` set to a sibling worktree's
    kit, where `test_pure_imports_are_pinned` failed on that worktree's imports.
  - `test_scan_reports_each_banned_form` checks each banned form against the live `PURE_IMPORTS`.
    Once a pin holds a name that a banned form imports, the scan accepts the form and the test
    fails. The third Codex review of S2-A, at `cd433543`, showed it with
    `collections.defaultdict` pinned for `checkedtables` in memory. Its command printed `scan: []`
    and `AssertionError: from collections import defaultdict` on Python 3.12.15. Both pins are
    empty, so no pin names one today. A later pull request that pins a name that one of the banned
    forms imports, such as `collections.defaultdict`, must also edit that form.
  - `page_from_text` splits lines at `\n` only and words at an ASCII space only. So a block with
    `\r\n` line ends keeps `\r` in its words and in the `#ocr` line, which then reads as text
    layer, and a non-breaking space stays inside a word. The Codex review of S2-C found both at
    `8846f05c`, and a rerun of its command at `7c1eb0b` printed `text_layer ['#ocr\r', 'Taxes',
    '1,234\r']` for `#ocr\r\nTaxes 1,234\r\n` and `['Taxes\xa01,234'] False` for
    `Taxes\u00a01,234`. The second is what a page test of `normalize_space` needs.
    `test_page_lines_carry_the_source_and_the_text` builds `CASH\xa0FLOW` so that `Line.text`
    must collapse the space. With words split at any whitespace in a scratch copy, the 80 kit
    tests still passed, and that space never reached `Line.text`.
  - `test_hypothesis_profile_is_derandomized` in `tests/test_workspace.py` asserts the name of the
    active Hypothesis profile. Hypothesis renames the active profile when a run sets
    `--hypothesis-verbosity=verbose`, so that one diagnostic flag fails the test. The third Codex
    review of S2-B found it at `aec4c6c8`. In a scratch copy of that head, pytest with the flag
    failed the test on the name `phillyledger-with-verbose-verbosity`, and the same run without
    the flag passed.
  - `pytest_unconfigure` in the root `conftest.py` removes the Hypothesis home with
    `shutil.rmtree(home, ignore_errors=True)`, so a failed cleanup is silent. The third Codex
    review of S2-B found it at `aec4c6c8`. Its command, which patches `os.lstat` to raise
    `PermissionError`, printed `cleanup failed: True teardown returned normally` in a scratch copy
    of that head.
  - `normalize_label` turns a combining accent into a space. So the decomposed spelling of
    "Crédit" gives `cre dit`, with the squash `credit` of the unaccented word, where the composed
    spelling gives `crédit`. The third Codex review of S2-C found it at `0df73f36` (finding 4 of
    `.codex-review/step-02-pr-0df73f36.md`). A rerun of its command in a scratch worktree at that
    head printed `'Cre\u0301dit' 'cre dit' 'credit'` and `'Cr\xe9dit' 'cr\xe9dit' 'cr\xe9dit'`.
    No page is known to print one. No step owns it, and the first step to meet a decomposed label
    decides.
  - `split_line_prefix` compiles the table's prefix pattern. For a pattern that Python itself
    warns about, such as `[[]` (a `FutureWarning`, "Possible nested set"), Python's warnings
    machinery reads the source file of `text.py` to format the warning and writes a
    `__warningregistry__` dictionary into the module. The kit does no I/O of its own here, and no
    table would declare such a pattern, but a table module that did would see the warning in its
    tests. The fourth Codex review of S2-C found it at `7d1aa59d` (finding 1 of
    `.codex-review/step-02-pr-7d1aa59d.md`). A rerun of its command in a scratch worktree at that
    head printed the warning at `text.py:140`, then `registry before: False`,
    `prefix: [ remainder: Revenue` and `read text.py: True registry after: dict`. Turning
    warnings into errors for the tests of the pure packages would catch it. That is an idea, not
    a plan.
  - In Python `[^\W\d_]` matches a superscript digit. So `normalize_space` closes the hyphen of
    `"\u00b9 - \u00b2"`, and `parse_label` takes the `2` of `"Total \u00b9 2"` as a mark. The
    fourth Codex review of S2-C found it at `7d1aa59d` (finding 4). A rerun of its command in a
    scratch worktree at that head printed `'\u00b9-\u00b2'` and
    `Total \u00b9 2 'Total \u00b9' ('2',)`, with the superscripts written here as escapes. Both
    inputs are made up.
  - `transliteration_ok` and `split_numeric_runs` look for a font code as `(cid:` in lower case.
    At the S2-D fix round 3 head, `transliteration_ok("10(CID:28)", "10028")` is true, where the
    lower-case form is false, and `split_numeric_runs` cuts `(CID:21)5` into `(CID:21)` and `5`.
    `pdfminer` writes the code in lower case, as `f"(cid:{cid})"` at line 268 of
    `pdfminer/converter.py` in the reference repository's environment, read and not run. The
    last verifier of S2-D found it. The adapter of step 4 is the only source of such words, so
    its plan decides whether the kit also refuses another case.
  - A small raised digit after a `$` word, with no number word before it, reads as the amount.
    The raised-digit rule measures a digit against the word just before it, which must hold a
    digit, so `$` and a raised `1` give `Amount 1`, with the `$` at full size or small. The S2-D
    fix round 3 searched raised layouts at `fae7e17` and at its own head and found this one
    still reading a raised digit into the number. A raised `*1`, a superscript then a digit, a
    digit then a superscript or two marks, a digit then `)` or `%`, two digits, a raised
    superscript word, a raised digit before a full-size mark word, and a `$` word, a number and
    a raised footnote all keep the digit out of the number at that head. A full-size digit
    before a raised mark word joins the number through join shape 2, as it does with no mark.
    No page is known to print a `$` and a raised digit alone, and no step owns the form.
  - `apply_reading`'s message for a word that is not on the reading's file and page has no test
    that reads the message. The S2-E fix round 2 found it.
  - Hand-built words `10(` and `cid:28)` in a count column give an `Unreadable` cell whose text
    is `10( cid:28)`, and the reading `10028` gives a reviewed `Amount`, because the font-code
    check looks for `(cid:` in `seen`. The S2-E verifier found it at `2e0f4eca`, and a rerun at
    `f82950e` printed `cell 'Unreadable not_a_number', reading '10028' -> Amount 10028
    reviewed`. A text layer gives a font code in place of one character, so no extraction
    should split it across two words. The note above on the case of `(cid:` cites the
    `pdfminer` line that writes it. This is for the plan of the step that ports the word
    reader: the reader must keep a font code inside one word, or the check must look for
    `cid:`.
  - `pages()` in `packages/checkedtables/tests/test_lines.py` draws, for each word index, the
    word or its children and never both. So `test_every_word_lands_in_exactly_one_line` passes
    when `group_lines` drops a parent word whose child is on the page. The Codex review of S2-C
    at `d3dbb428` found it (finding 1). `Page` accepts a parent with its children (the
    Deviations entry "the constructor checks are the ones the design blocks show"). At
    `f82950e`, a page of the word `1,234` and its children `1,` and `234` builds, and
    `group_lines` keeps all three words. In a scratch copy with `group_lines` changed to drop
    such a parent, the same page gave only the two children, and the property and the other 11
    tests of `test_lines.py` passed.
  - A label whose words are `Sheriff` ending in a non-breaking space and then `2` gives the
    norm `sheriff 2` with no mark, where `Sheriff 2` gives `sheriff` with the mark `2`. The
    bare-digit form needs exactly one whitespace character before the digit. The input is
    constructed. The Codex review of S2-C at `d3dbb428` found it (finding 3), and a rerun of
    `parse_label` at `f82950e` printed `norm 'sheriff 2' marks ()` and
    `norm 'sheriff' marks ('2',)`.
  - No test states the value of an OCR amount in a fixed-decimal column. A lexer that rounds
    every OCR `Amount` in a one-decimal column to a whole number passes every test of
    `test_lex.py`, `test_val_probe.py`, `tests/test_evidence.py` and `test_records.py`. A run at
    `b52a993a` with that lexer, patched in memory, printed `89 passed`, and the patch changed 9
    values on the way. The same patch without its test of the source fails 5 tests, so the gap
    is the OCR source and not the one-decimal column. The property
    `test_amount_digits_are_the_digits_of_its_words` and `test_lexer_round_trip`, the two named
    proofs of clause C1b, both pass under it. The lexer at the head is right: it reads `65.8` on
    an OCR page in the one-decimal column as `Amount` 65.8. The Codex review of S2-D at
    `4fa19584` found a narrower form (finding 1), a patch that also asked for a confidence on the
    word, which `lex.py` never reads. The review of the run's decision trail found this wider
    one. Eight cash editions name a Textract word source in a reviewed record, FY2007 Q3 among
    them (the table in section 1 of `docs/evidence/dossiers/QCASH.md`), and the tests' own cash
    column is the one-decimal column of VAL-Q35, so this is a path the cash parser of step 8
    reads. Close the gap before then, with an OCR draw in a fixed-decimal column in both
    properties.
  - `transliteration_ok` counts a footnote digit, because it sees text only. The Codex review of
    S2-D at `4fa19584` found it (finding 2). At `73d428e2`, `transliteration_ok("2.8 1*", "2.8")`
    is false and `transliteration_ok("2.8 1*", "2.81")` is true. `apply_reading` removes the mark
    words that end an `Amount` before the check, so the cell of `2.8` and a small raised `1*`
    accepts the reading `2.8` and keeps the mark `1*`, and refuses `2.81` with `reading_refused`.
    The S2-E verifier ran the same at `73d428e2` (`/tmp/swarm-s2-e/worker-7/verify-fix3-c.log`),
    and so did a run of ours. Any other caller of `transliteration_ok`, such as the loader of
    step 5, must remove the marks itself (the note "The loader's digit check and a footnoted
    reading disagree").
  - The SUPCAP-Q34 test lexes `N/A` in a money column, where the page prints `N/A*` in a year
    column. The Codex review of S2-D at `4fa19584` found it (finding 3). Page 93 of the FY2023
    supplemental report (`supplemental-report/FY23.pdf`) prints `N/A*` under Budget Year and five
    dashes in the money columns. Run read-only on it, `pdftotext -f 93 -l 93 -layout` 26.07.0
    prints the line `N/A* - - - - -` under the heading line that starts `Budget Year Available`.
    At `73d428e2`, `N/A*` is `Unreadable` with the reason `not_a_number` in a money column and
    `Text` in a year column, and `N/A` is `NotApplicable` and `Text`. This is for the step 12
    plan.
  - The last child that `split_numeric_runs` returns can end past its parent's right edge by a
    float error. The Codex review of S2-D at `4fa19584` found it (finding 4). At `73d428e2`, for
    the word `TAX434,605,553` in the box (10.02, 10, 65.04, 20), the run printed the children
    `TAX` and `434,605,553`, the parent edge 65.04 and the child edge 65.04000000000002, and
    `contains` is false at a slack of 0 and true at 1.0. An idea, not a plan: the first and last
    child keep the parent's own outer edges.
  - In `lex_cell`, the test `len(texts) == 1` before the `N/A` check changes no result, since a
    cell of two or more words joins with a space and so never equals `N/A` or `NA`. The S2-D
    verifier found it at `4fa19584`. At `73d428e2`, the two-word cells `N/A` and an empty word,
    `N/` and `A`, `N` and `A`, and `NA` and an empty word join to texts that are not `N/A` or
    `NA`, and each lexes as `Unreadable` in a money column.
  - Every successful application in `test_records.py` uses the id `r1`, so its tests pass when
    `apply_reading` writes one constant id. The Codex review of S2-E at `73d428e2` found it
    (finding 2), with an in-memory mutant that left all 37 tests passing. At `73d428e2`, a record
    with the id `cash-fy07-q3` on the OCR cell `2918` in the one-decimal column gives that id as
    `Amount.review_id` for the reading `291.8` and as `Unreadable.accepted_by` for a null reading.
  - The signed-value property of `test_records.py` compares the value and the exponent, which are
    equal for `Decimal("-0.0")` and `Decimal("0.0")`. The Codex review of S2-E at `73d428e2` found
    it (finding 3), with an in-memory mutant that dropped the sign of a reviewed zero and left all
    37 tests passing. At `73d428e2`, `(0.0)` read as `(0.0)` in the one-decimal cash column gives
    `Decimal("-0.0")`, whose `as_tuple()` is `DecimalTuple(sign=1, digits=(0,), exponent=-1)`, and
    the run printed `True` for its equality with `Decimal("0.0")`. Comparing `as_tuple()` would
    catch a lost sign, as `test_lexer_round_trip` does. Codex states that page 1 of the FY2010 Q2
    cash report (`qcmr/cash/FY10_Q2.pdf`) prints `(0.0)` in `Total Current Revenue`. That is
    Codex's statement, not checked here.
