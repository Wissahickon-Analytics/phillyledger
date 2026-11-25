# Follow-ups

Confirmed findings that did not block their pull request, by step
(`docs/plans/README.md`, "What blocks a pull request"). The owner picks the ones a cleanup pull
request fixes. No session reads this file unless its task names it. A note or an entry named
by its title is in `docs/plan-notes.md`, `docs/progress.md` or `docs/deviations/`.

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
    Appendix C of `docs/plans/step-01.md` lists the limits found, and the note "The pure
    packages can still reach effects the gates do not name" in `docs/plan-notes.md` records the
    owner's choice of an allow-list.
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
    entry "the constructor checks are the ones the design blocks show" of
    `docs/deviations/step-02.md`). At
    `f82950e`, a page of the word `1,234` and its children `1,` and `234` builds, and
    `group_lines` keeps all three words. In a scratch copy with `group_lines` changed to drop
    such a parent, the same page gave only the two children, and the property and the other 11
    tests of `test_lines.py` passed. Pull request #27 (`step-02/f-test-gaps`) closes it.
    `pages()` may now draw a word with its children, and
    `test_every_word_lands_in_exactly_one_line` gains the example `PARENT_WITH_CHILDREN`, the
    word `TAX434,605,553` with `TAX` and `434,605,553`. With `group_lines` changed in a scratch
    copy to drop each word with no child whose index a child on the page shares, the property
    fails with its examples and without them, and so do the ten breaks of the S2-C verifier.
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
    properties. Pull request #27 (`step-02/f-test-gaps`) closes it. Both properties now also lex
    each cell in the column that declares its printed decimals, on both sources.
    `test_amount_digits_are_the_digits_of_its_words` also draws printed numbers and gives each
    OCR word a confidence of None or 0 to 100. The plain test
    `test_an_ocr_amount_keeps_the_decimals_it_prints` reads `65.8` in the one-decimal column and
    `828,904.89` in a two-decimal column on an OCR page. Three lexers patched in memory each fail
    all three tests: one that rounds every OCR `Amount` in a one-decimal column, one that does so
    only when the first word has a confidence, and one that rounds every OCR `Amount` in a
    two-decimal column. Each passes the 89 tests of the old run at `2638173a`. The Codex review
    of this pull request at `5a443450` found three more gaps here, and the fix round closes them.
    `test_lexer_round_trip` gains the OCR example `828,904.89`, because its only two-decimal
    example, `-0.00`, reads the same after rounding. The lexer that rounds the cents and keeps
    the exponent, so that `828,904.89` reads as `828905.00`, now fails the round trip as well.
    `fixed_column` keeps the drawn column's kind and percent-sign rule, and
    `test_a_bare_percent_keeps_the_decimals_its_column_declares` reads a bare `74.98` in a
    two-decimal percent column (SUPOP-Q12). A lexer that rounds that bare percent to `75.00`
    fails it and the digits property. The digits property draws `bold` as False or None for OCR
    words, and `test_a_style_free_ocr_word_below_full_confidence_keeps_its_decimals` reads `5.6`
    at confidence `99.21337127685547` with no bold and no size. By Codex's account, FY2007 Q4
    cash carries that word. A lexer that rounds such a word in the one-decimal column to `6.0`
    fails that test, and the digits property through its new example `5.6`. At `5a443450` every
    test passed under the percent and the style-free lexers. The Codex review at `e2d91c9d`
    found two more, and the second fix round closes them.
    `test_a_bare_percent_above_one_hundred_is_read` reads a bare `116.17` in a two-decimal
    percent column (SUPOP-Q12), as page 86 of the FY2023 supplemental report prints it. A lexer
    that returns `Unreadable` above 100 in such a column fails it.
    `test_an_ocr_word_under_the_confidence_floor_keeps_its_decimals` reads `65.8` in the
    one-decimal column from an OCR word with no size and the confidence `60.890262603759766`,
    under the floor of 95 that assembly applies. A lexer that rounds such a word to `66.0`
    fails it. At `e2d91c9d` every test passed under both lexers.
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
    Pull request #27 (`step-02/f-test-gaps`) closes it with
    `test_a_reviewed_cell_names_the_record_that_was_applied`, which applies records of the ids
    `cash-fy07-q3` and `cash-fy08-q1` to that cell. With `apply_reading` patched in memory to
    write `r1` in place of the reading's id, that test fails. Both records go to a cell that is
    `Unreadable`, which the Codex review at `5a443450` found. So
    `test_a_reviewed_amount_names_the_record_that_was_applied` applies the record `cash-fy07-q4`
    to the OCR `Amount` `65.8`, with the reading `65.8` and with none. With `apply_reading`
    patched in memory to write `r1` only when its input cell is an `Amount`, that test fails. At
    `5a443450` every test passed under that patch. The Codex review at `e2d91c9d` found that the
    test read `65.8` as a person's reading of FY2007 Q4 cash, where page 1 prints `85.8` and
    `65.8` is the OCR error of QCASH-Q22. The second fix round gives it the made-up OCR
    `Amount` `291.8` and the record `second-record`, cites no report and keeps every assertion,
    and the same patch still fails it. That review also found that no test asked `reading_for`
    to pick a record that is not the first.
    `test_a_cell_takes_the_record_boxed_on_it_and_not_the_first_record` boxes `29.18` on the
    left and `291.8` on the right of two OCR cells that print `2918`, and each cell gets its own
    record's value and id. With `reading_for` patched in memory to return `readings[0]`, that
    test fails. At `e2d91c9d` every test passed under that patch.
  - The signed-value property of `test_records.py` compares the value and the exponent, which are
    equal for `Decimal("-0.0")` and `Decimal("0.0")`. The Codex review of S2-E at `73d428e2` found
    it (finding 3), with an in-memory mutant that dropped the sign of a reviewed zero and left all
    37 tests passing. At `73d428e2`, `(0.0)` read as `(0.0)` in the one-decimal cash column gives
    `Decimal("-0.0")`, whose `as_tuple()` is `DecimalTuple(sign=1, digits=(0,), exponent=-1)`, and
    the run printed `True` for its equality with `Decimal("0.0")`. Comparing `as_tuple()` would
    catch a lost sign, as `test_lexer_round_trip` does. Codex states that page 1 of the FY2010 Q2
    cash report (`qcmr/cash/FY10_Q2.pdf`) prints `(0.0)` in `Total Current Revenue`. That is
    Codex's statement, not checked here. Pull request #27 (`step-02/f-test-gaps`) closes it.
    `test_a_reviewed_amount_keeps_the_digits_seen` now compares `as_tuple()` and gains the
    example `0.0` read as `(0.0)`, since the words it draws hold no parenthesis, and
    `test_a_reviewed_zero_keeps_its_sign` reads `(0.0)` as `(0.0)`. With `apply_reading` patched
    in memory so that a reviewed zero loses its sign, both tests fail.
- **Follow-ups after step 3** (November 25, 2026). Step 3's five pull requests, 32, 33, 35, 36
  and 37, found these and did not fix them. Each was checked against `d3b0666`, the head of
  stack 34, and the owner kept them when he sorted the list.
  - `test_index_refuses_one_sha_twice` uses two editions, so a guard that refuses a repeated sha
    only across editions still passes it (pull request 32).
  - The watch tests never index a URL as a version's second URL or on a superseded version, so
    two mutants of `_request` in `watch.py` survive (pull request 33).
  - No test holds the "and nothing more" of the title rule. With `search` in place of
    `fullmatch`, 48 title, listing and watch tests pass (pull request 33).
  - The HTTP test of `plan_fetch` cannot tell a bad status from a missing sha. With
    `status != 200` removed from the guard, both of its cases pass (pull request 35).
  - The tests of `confirm_period` allow a confirmation by the end date alone, though the rule
    compares the whole period, start included (pull request 35).
  - Rule 3 of `plan_fetch` has no test at a held URL. With the `superseded_sha_relisted` check and
    the known-URL check swapped, 156 tests pass (pull request 35).
  - The fixed branch `fetch/index` and its title have no test. With either changed, 156 tests
    pass. No step 3 code uses them (plan shape 10, pull request 35).
  - No test fails when the S3 client reads `~/.aws/config` and `~/.aws/credentials`. The
    ambient-profile test plants its files only through the two variables (pull request 36).
  - No test fails when botocore's own retries come back. With the `retries` line dropped, a put
    answered 500 sent three requests (pull request 36).
  - The client's `use_arn_region` and `s3_disable_multiregion_access_points` values change no put
    in any probe, and no test fails without them (pull request 36).
  - No test compares an inventory row's `sha256` with its `browser_sha256`. All 20 agree at the
    head by the read-back run (pull request 37).
  - No test reads the index's `holding`, `printed_period`, `via`, `urls`, `title` or `listed_at`,
    or the inventory's `bytes`, `pages`, `page1_period`, `url` or `browser_sha256`. With each
    changed in the real files, the four inventory tests pass (pull request 37).
  - The purity test misses `Counter()` at module scope, because its list of mutable constructors
    holds `list`, `dict`, `set` and `bytearray` alone (pull request 32).
  - A category with the entry's title whose `documents` is not a list is skipped with no finding
    when a readable category with that title is beside it (pull request 33).
  - A retitled revision such as "Quarterly City Managers Report Revised - June 30, 2025" reads as
    `unrelated` with no finding. The old repo's `test_qcmr.py:165` read it as the winning
    revision, and step 13's gap rule cannot see it, because the quarter is already indexed (pull
    request 33). Of the kept items, this is the one that could change what gets published, since
    a revised report would be missed with no finding. Step 13's plan should read it.
  - An empty digest gives the store key `pdf//.pdf` (pull request 35).
  - `qcmr_period` reads digits that are not ASCII and the year 0001, where the title rule wants
    `[1-9]\d{3}` (pull request 35).
  - A 412 with no body is read as `EffectError`, so `put_immutable` does not read the object back
    (pull request 36).
  - A service message with a newline prints two stderr lines (pull request 36).
  - `https://?q=1` passes the saved-folder URL rule, which the design states as a scheme and no
    whitespace (pull request 36).
  - An endpoint with no scheme ends `main` in a `ValueError` traceback from inside `s3_store`. It
    prints no key (pull request 36).
