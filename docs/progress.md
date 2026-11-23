# Build progress

The build order and each step's check are in `docs/design.md` section 15. Update this file in the
same branch as the work: status, the date the check passed, and anything a later session needs.

| Step | What | Status | Branch | Check passed |
|---|---|---|---|---|
| 1 | Workspace, tooling, purity and shape tests | check passed | `step-01/a-workspace`, `step-01/b-import-contracts`, `step-01/c-kit-shape`, `step-01/d-test-isolation` | November 22, 2026, runs 45093444380, 45094817250, 45094829990 and 45092206629 |
| 2 | Kit, words to cells | in progress | `step-02/a-import-pin`, `step-02/b-value-types`, `step-02/c-words-to-lines` | |
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
- **Step 2: a kit type refuses what its own design block rules out** (November 23, 2026, S2-B,
  found in the second Codex review and by a verifier). Each Codex round asked for a few more
  constructor checks, and the list had no natural end. Design section 2.1 now opens with one
  closed rule. A kit type refuses at construction, with `ValueError`, a value that breaks a fact
  its own block states in a field comment or in a "What these make impossible" list, and a check
  that no block states is not built. The round added six checks. Each is stated in its block of
  section 2.1, and each has a test of the refused value and of its nearest legal value. No field
  changed, so `FIELD_SNAPSHOT` is unchanged.
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
  "Sheriff 2" test fails and the "Human Services (1)" test passes. The comments also say three
  smaller things. `normalize_label` turns punctuation into a space where the design said "drop",
  as `entities.py:95` did, so "Delivery/couriers" gives "delivery couriers" (BSALES-Q47).
  `normalize_space` trims the ends. `page_from_text` keeps a `**` that opens no bold span, so
  the label "Total RTT records **1" (RTT-Q38) can be built with it. A `**` that starts a word
  opens a span when the word's next character is not `*`, and a `**` that ends a word closes
  one when the character before it is not `*`. Each closer pairs with the nearest unpaired
  opener to its left on the same line, and every other `**` stays in the text. The first build
  paired the first two `**` on a line, so "Total RTT records **1  **1,234**" gave the words
  `1`, bold, and `1,234**` (found in the Codex review). It now gives `**1` and a bold `1,234`.
  The comment of `doc_of` also says that it sorts the pages by number and raises `ValueError`
  for no pages, for pages of two files and for a repeated page number. `text`, `lines`
  and `testing` import from `re`, `statistics` and `typing`, which join the list in section
  11.1. Design sections 3.1 and 11.1.

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
  it prints 592 lines. Against design section 12.1: `refs` 121 (estimate 60), `kinds` 29 (40),
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
- **What the step 2 line and label rules do on four real pages, for the plans of steps 5, 8 and
  11** (November 23, 2026, step 2, S2-C, found in the Codex review). Codex read three PDFs of
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
    the lexer's rule for VAL-Q28 expects to find that digit in the cell.
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
    decision.
  - Line formulas other than `(19+20)` stay in the label, for the step 11 plan. On the same
    page, the run printed `Subtotal (12 thru 17) ()` and `Operating Surplus (Deficit) for Fiscal
    Year (8-21) ()`. So rows 19 and 22 keep their line formulas in `Label.text`, because
    `parse_label` reads only the `(19+20)` form (BIB-Q38). The RTT reports print a class code in
    the same shape, "General Commercial (88-2)" (RTT dossier, "Legacy property labels"), so the
    kit cannot take `(8-21)` as a mark unless a table tells it to.
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
