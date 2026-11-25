# Standards sweep B

On November 25, 2026 the owner asked for the type rules of the book Robust Python, and pull
request 39 wrote them into `CLAUDE.md` (Code) and section 8 of `docs/principles.md`. Sweep A
brought the built code to the typer and docstring rules without changing a signature. Sweep B
changes signatures. It gives a sha256 a type of its own, `Sha256`, in the kit and in `datadesk`,
and it makes the two readers that return a bare `str` for a refusal return a closed enum. It
changes no published value. `index.jsonl` stays byte for byte the same, and so does every store
key, every finding code and every line of the body of the fetch pull request.

Sweep B comes before step 4's plan because step 4 writes the first word fixtures, and each word
in a fixture names its file by sha256.

## Track

Full track. The types of `WordRef.doc_sha256`, `Page.doc_sha256`, `Document.sha256` and
`ReviewedReading.doc_sha256` are part of the kit's public shape. This file is the Plan run.
Sweep B has no check in design section 15, so "The check" below is its check. One Build run
follows, on Opus, after the owner's go.

## The owner's answers

All three are from November 25, 2026.

1. The planning session asked "Plan sweep B as its own short step before step 4's plan?" He
   answered "Yes, plan it". He was shown this scope. One `Sha256` type, defined in the kit and
   used in `datadesk`, with `index.jsonl` unchanged byte for byte. `qcmr_period` and
   `qcmr_title` return a closed enum of codes where they return a bare `str`.
   `SourceCatalog | tuple[Finding, ...]` stays. Other value types, such as a URL or a store
   key, wait until a step's plan meets them.
2. This Plan run asked which form `Sha256` takes. It showed him three forms, each with its
   pytest count, its `ty` count, whether the index bytes change, and its `repr`, as in the
   first table under "What the runs showed". He chose the option "Checked str subclass
   (Recommended)". Its text said the form "needs 8.3 reworded to allow this form for a value
   that is one piece of text".
3. This Plan run asked "Should the sweep B build reword 8.3 so it no longer says that?", where
   "that" is the sentence that calls `isinstance(repo, tuple)` in `fetch_command` "the loose
   form". He chose the option "Yes, withdraw it (Recommended)".

Everything else in this plan was worked out after those answers. Each item under "Proposals" is
a proposal until he lands this plan.

## Proposals

1. One pull request holds both changes. They share `core/fetch.py`, `core/listings/__init__.py`
   and the design, and sweep A was one pull request.
2. `WordRef`, `Page` and `Document` refuse a sha that is not a `Sha256`, where they refuse an
   empty one now. A caller with no type checker, such as a user of the kit from PyPI, then gets
   a `ValueError` at the constructor. `ReviewedReading` has no guard on its sha now and gets
   none.
3. The refusals are two enums, one for each family of readers. `PERIOD_READERS` and
   `TITLE_RULES` each need one return type for every reader they hold. One shared enum would
   let `qcmr_title` return `period_ambiguous` with no report from `ty`.
4. Both enums are pinned in `test_closed_lists_are_pinned` and in design section 11.4, so hard
   rule 6 covers them. Section 8.3 of `docs/principles.md` already says a closed set is "pinned
   by a test". The text of hard rule 6 stays as it is.
5. `ListedLink.skip_reason` takes the type `SkipReason | None`. It holds what `qcmr_title`
   returned and nothing else.
6. `parse_index` builds `supersedes` with `Sha256` too, since it is the sha of an earlier
   version.
7. The `datadesk.core` import pin gains `typing.assert_never`, and the kit's gains
   `typing.Self`.

## The shapes

```python
# checkedtables/refs.py
class Sha256(str):
    """The sha256 of a file's bytes, as 64 lowercase hex characters."""
    __slots__ = ()
    def __new__(cls, text: str) -> Self: ...   # ValueError for anything else, a non-str included
    def __repr__(self) -> str: ...             # Sha256('7c4a...'), which rebuilds the value

# datadesk/core/listings/titles.py
class SkipReason(StrEnum):
    INFOGRAPHIC = "infographic"
    UNRELATED = "unrelated"
    NOT_A_QUARTER_END = "not_a_quarter_end"
def qcmr_title(title: str) -> EditionKey | SkipReason: ...

# datadesk/core/fetch.py
class PeriodRefusal(StrEnum):
    UNREADABLE = "period_unreadable"
    AMBIGUOUS = "period_ambiguous"
    NOT_A_QUARTER_END = "period_not_a_quarter_end"
def qcmr_period(page1_text: str) -> Period | PeriodRefusal: ...
```

`Sha256` is the one builder. It raises `ValueError`, and it returns no finding, because a sha
is never the publisher's data. The code computes it from bytes, or reads it from one of the
repo's own files, where the caller of the parser already turns a `ValueError` into a finding
(`_read_index` gives `index_unreadable`). `.claude/rules/core-purity.md` says to raise only for
a broken invariant, and this is one. The guard that pull request 38 put in `parse_index` moves
into the builder and leaves `_version`.

These take `Sha256` where they take `str` now.

- Kit: `WordRef.doc_sha256`, `Page.doc_sha256`, `Document.sha256`,
  `ReviewedReading.doc_sha256`, and the `sha` parameter of `page_from_text`.
- `datadesk.core`: `DocumentVersion.sha256` and `.supersedes`, `ArchiveIndex.by_sha`,
  `Fetched.sha256`, `StoreObject.sha256`, `_pdf_key`, `EditionNote.doc_sha256` and
  `Listing.html_sha256`.
- `datadesk.shell`: `FetchRun.listing_sha256`, `put_immutable`, and the two places that wrap a
  `hexdigest()`.

`confirm_period` and `parse_listing` handle each member of the reader's result and end in
`assert_never`. `confirm_period` puts `refusal.value` in `Finding.code`, so the code stays a
plain `str`. `watch.py` compares `skip_reason` with `SkipReason.NOT_A_QUARTER_END`.

## What the runs showed

The Plan run tried three forms of `Sha256` at `36807de` with a throwaway script that edits
`packages/*/src` and no test. The scripts are not committed, and the two scratch branches are
local and not pushed.

| | Frozen dataclass | Checked `str` subclass | `NewType` and a builder |
| --- | --- | --- | --- |
| `uv run pytest` | 56 failed, 434 passed | 490 passed | 3 failed, 487 passed |
| `uv run ty check` | 121 errors, 2 in `src` | 118 errors, all in tests | 118 errors, all in tests |
| `render_index` of the committed index | other bytes | the same bytes | the same bytes |
| `Sha256(x) == x` | `False`, and `ty` says nothing | `True` | `True` |
| `repr` | `Sha256(hex='7c4a...')` | `Sha256('7c4a...')` | `'7c4a...'` |

- The baseline at `36807de` is 490 passed and 7 skipped. `uv run lint-imports` kept its 8
  contracts under all three forms.
- The dataclass changes the index because `asdict` in `render_index` turns it into
  `{"hex": ...}`. The committed file has the sha256 `a06dd9ee...87a4`, and the dataclass form
  rendered `8a36d4bf...0dd3`.
- The three `NewType` failures are the import pin, which refuses `typing.NewType`.
  `Sha256("anything")` also skips the check, and a sha prints as a bare string, so a word
  fixture would not rebuild the type.
- The 118 `ty` errors are all `invalid-argument-type`, in 17 test files, where a test passes
  plain text as a sha.

The chosen form was then run on sweep A's head, `643d663`, with both enums. The baseline there
is 491 passed and 7 skipped, and the kit size report prints 735 lines.

- With `typing.assert_never` and `typing.Self` added to the import pin and no other test file
  edited, 491 passed. Without `typing.assert_never`, 3 tests failed, all on the import pin.
- `ty` reported the same 118 errors and none in `src`. `lint-imports` kept its 9 contracts.
  The kit size report printed 745 lines. `render_index` gave back the committed index.
- ruff's `PYI034` asks that `__new__` return `Self`. The purity tests failed on
  `from typing import Self` until the kit's pin held it.
- `eval(repr(word)) == word` held for a `Word`, and the sha came back as a `Sha256`.
- With the `PeriodRefusal` arm removed from `confirm_period`, `ty` printed
  `error[type-assertion-failure] Type PeriodRefusal is not equivalent to Never`.
- With the three kit constructors changed to refuse plain text and no test edited, pytest could
  not collect `test_cells.py` and `test_lines.py`. So the constructors tighten after the tests
  build a `Sha256`.

## The check

One pull request, SB, owns every clause.

| # | Clause | Proof |
| --- | --- | --- |
| 1 | `Sha256` holds 64 lowercase hex characters and equals its text. It raises `ValueError` for an empty string, an uppercase digit, 63 or 65 characters, a trailing newline, and a value that is not a `str`. | `test_sha256_holds_64_lowercase_hex_characters_and_equals_its_text` and `test_sha256_refuses_any_other_value` in the kit's `test_refs.py` |
| 2 | The `repr` of a `Sha256`, and of a `WordRef` that holds one, is an expression that rebuilds an equal value whose sha is a `Sha256`. Step 4's fixture writer needs this. | `test_the_repr_of_a_word_ref_rebuilds_its_sha256` in `test_refs.py` |
| 3 | `WordRef`, `Page` and `Document` raise `ValueError` for a sha that is not a `Sha256`, 64 hex characters of plain text included. The tests that pass an empty sha stay as they are. | `test_word_ref_refuses_a_sha_that_is_plain_text` in `test_refs.py`, `test_page_and_document_refuse_a_sha_that_is_plain_text` in `test_words.py` |
| 4 | Every name listed under "The shapes" has the type `Sha256`, and plain text passed to one fails `uv run ty check`. | `test_planted_plain_text_sha_fails_ty` in `tests/test_gates.py`, built on `run_gate`, and the `ty` gate |
| 5 | `render_index(parse_index(text)) == text` for the committed `index.jsonl`, and the pull request does not change that file. | `test_render_index_gives_back_the_committed_index_byte_for_byte` in `tests/test_archive_inventory.py`. `git diff <base>...HEAD -- packages/datadesk/src/datadesk/data/index.jsonl` prints nothing. |
| 6 | Sweep B changes nothing that a test of steps 1 to 3 asserts. The first code commit holds every change to `packages/*/src` but the three constructor guards. It edits no test file but the two names in `tests/test_purity.py`, and `uv run pytest` passes at that commit with the base's count. | The run at that commit, recorded in the pull request. Codex checks out the commit and runs it again. |
| 7 | `parse_index` raises `ValueError` for a `sha256` or a `supersedes` that is not 64 lowercase hex characters. | `test_parse_index_refuses_a_sha_that_is_not_64_lowercase_hex_characters`, unchanged, and `test_parse_index_refuses_a_supersedes_that_is_not_64_lowercase_hex_characters` in `test_index.py` |
| 8 | `qcmr_period` returns a `Period` or a member of `PeriodRefusal`, and `qcmr_title` an `EditionKey` or a member of `SkipReason`. Each member's value is the string the reader returns now. | `test_qcmr_period_refuses_with_a_member_of_period_refusal` in `test_fetch.py`, `test_qcmr_title_skips_with_a_member_of_skip_reason` in `test_titles.py`, and the readers' present tests, unchanged |
| 9 | The values of `PeriodRefusal` and of `SkipReason` are pinned, in order. | `test_closed_lists_are_pinned` in `test_library_shape.py`, with two more asserts |
| 10 | `confirm_period` and `parse_listing` end in `assert_never`, and a member that one of them misses fails `uv run ty check`. | `test_planted_missed_refusal_fails_ty` in `tests/test_gates.py` |
| 11 | The code of the finding that `confirm_period` returns for a refusal is a plain `str`. | `test_confirm_period_puts_the_refusal_in_the_finding_code_as_plain_text` in `test_fetch.py` |
| 12 | The design and the rules say what the code does. | The lists under "Design and doc changes", read against the diff |

`FIELD_SNAPSHOT` does not change. `Sha256` is not a dataclass, and no field changes its name.
`test_kit_dataclass_fields_are_pinned` passed unchanged in every run above.

## The pull request

- **Branch.** `standards/sweep-b`, cut from `standards/sweep-a`, the branch of pull request 40,
  at the head that has pull request 40's verdict. Sweep A wrote docstrings in every file that
  sweep B changes, so B cannot be built beside it.
- **Base and title.** Base `standards/sweep-a`. Title
  `refactor(standards): give a sha256 its own type and name the readers' refusals`.
- **Landing order.** The step 3 stack (32, 33, 35, 36, 37, 38), then 39, then 40, then SB. The
  pull request that holds this plan is based on `docs/code-standards` and can land any time
  after 39. If it has not landed under SB's branch, SB's first commit is this file, unchanged.
  SB is not part of step 3's GitHub stack, as 39 and 40 are not.
- **Commits, in the order that clause 6 needs.** First `Sha256`, the two enums and the two
  pinned names, with every test passing and no other test file edited. Then the tests build a
  `Sha256` where they pass a sha, until `ty` passes. Then the three constructors tighten, and
  the new tests of the table above arrive. Then the design and the docs. Only the head has to
  pass the gates.
- It needs no call to R2, no request to the City and no Textract call.

## Files

- `packages/checkedtables/src/checkedtables/`: `refs.py`, `words.py`, `records.py`,
  `testing.py`.
- `packages/datadesk/src/datadesk/core/`: `domain.py`, `index.py`, `fetch.py`, `records.py`,
  `watch.py`, `listings/__init__.py`, `listings/titles.py`.
- `packages/datadesk/src/datadesk/shell/`: `cli.py`, `run_fetch.py`.
- Tests: the 17 files that pass a sha as plain text, `test_library_shape.py`,
  `tests/test_purity.py`, `tests/test_gates.py`, `tests/test_archive_inventory.py`.
- `docs/design.md`, `docs/deviations/step-03.md`, `docs/principles.md`, `docs/progress.md`,
  `docs/plan-notes.md`, `CLAUDE.md`.

## Design and doc changes

The build makes these in the same pull request (hard rule 7). The line counts are from
`docs/design.md` at `36807de`.

- **Design, a sha.** 27 lines type a sha256 as `str`, and each becomes `Sha256`. Built:
  `WordRef`, `Page`, `Document` and `ReviewedReading` (2.1), `DocumentVersion.sha256` and
  `.supersedes`, `ArchiveIndex.by_sha` and `EditionNote` (2.2), `page_from_text` (3.1),
  `Listing`, `Fetched` and `StoreObject` (3.2), `FetchRun` (4.2), `put_immutable` (4.5). Not
  built yet: `Table` and `FailureKey` (2.1), `WordSourcePlan`, `TablePages` and `ReleaseRow`
  (2.2), `records_for`, `illegible_pages`, `WordJob`, `ParseJob` and `textract_to_document`
  (3.2), `PdfReader.words` (4), `ExpectedTables` and `ArticleFigure.manifest_sha256` (18.3).
- **Design, the refusals.** Five lines in 3.2: `ListedLink.skip_reason`, `TITLE_RULES`,
  `qcmr_title`, `PERIOD_READERS` and `qcmr_period`, with the two enums beside them.
- **Design, the rest.** The `refs.py` row of 12.1 names `Sha256`. The test listing of 11.4
  gains the two pins. Section 2.1 says what `Sha256` refuses and why it raises.
- **`docs/deviations/step-03.md`.** A "Standards sweep B" section after sweep A's. It covers
  the kit types that step 2 built too.
- **`docs/principles.md`, section 8.3.** Two changes, both with the owner's answer above. A
  rule on one piece of text is held by a `str` subclass whose constructor checks it, and a rule
  across fields by a frozen dataclass with one builder. `fetch_command`'s
  `isinstance(repo, tuple)` leaves the examples of the loose form, and the sentence on
  `qcmr_period` moves to the past tense.
- **`docs/progress.md` and `CLAUDE.md`.** The note "The type rules of the code standards are not
  met yet" and the dated bullet in the Code section shrink to "What sweep B leaves" below. The
  note's claim that `gather_repo` owes a named result goes, by answer 3.
- **`docs/plan-notes.md`.** Two notes for step 4's plan. A word fixture prints each sha as
  `Sha256('...')`, once for each word, unless the writer binds it to a name. `Unreadable.reason`
  is still an open `str`. One note for the step that builds the TOML loaders: a loader builds a
  sha with `Sha256` and turns its `ValueError` into a finding.

## Risks the build should probe

- **A message that prints a sha with `repr` changes.** `repr` now shows `Sha256('...')`, so the
  `ValueError` text of `WordRef`, `Page`, `Document` and `doc_of` changes. Every test passed
  with that change, and no message is a published value.
- **Equal to its text.** `Sha256(x) == x` is `True`, so `ty` does not report a comparison of a
  sha with text that no builder checked. A parser builds the `Sha256` where the text enters.
- **Hypothesis strategies.** `test_index.py` and the kit's `test_refs.py` draw shas as text, and
  each needs `.map(Sha256)`.
- **A slice is a `str`.** `sha[:2]` in `_pdf_key` and `doc_sha256[:8]` in the kit's `records.py`
  stay as they are.
- **The unchecked route.** `str.__new__(Sha256, "x")` builds one with no check. Nothing calls
  it, and a review refuses it.
- **A base that moves.** SB is one branch outside a GitHub stack. If the head of pull request 40
  moves after SB is open, SB's first owner created the branch and may rebase it and push with a
  lease (hard rule 9). A fix-round owner may not, so it asks the owner first.

## What sweep B leaves

- `SourceCatalog | tuple[Finding, ...]` and `gather_repo`'s result, by answer 1.
- `_read_cell` in the kit's `lex.py`, which returns `Decimal | str`. Its `str` is the value of
  the public field `Unreadable.reason`, which design section 2.1 lists as `"grouping",
  "low_confidence", "two_tokens", ...`, an open list. Step 4 adds the rule for a word that
  still holds `(cid:` (VAL-Q05), so step 4's plan meets it.
- `Rejection.reason`, which holds `http_<status>` and finding codes beside the period codes.
- A URL, a store key, a `listed_at` stamp and an edition id, by answer 1.
- The other callers in `datadesk` that tell a union apart with an early `isinstance` return, or
  with a `match` that has no `assert_never`. `core/fetch.py` has three, and `core/catalog.py`,
  `core/listings/__init__.py`, `shell/gather.py`, `shell/cli.py` and `shell/adapters/s3.py`
  have the rest. `rg 'isinstance\(|^\s*match ' packages/datadesk/src` lists them.
- `phillyledger`. The contract "the reader stands alone" keeps it from importing the kit, so
  step 13's plan decides how it types a sha.
- `checkedtables/__init__.py` exports nothing yet, so `Sha256` is imported from
  `checkedtables.refs`.

## What a user of the kit gets

The kit is not on PyPI until after step 14, so no released version changes. A user builds a
sha with `Sha256(hashlib.sha256(data).hexdigest())` and passes it to `WordRef`, `Page`,
`Document`, `ReviewedReading` and `page_from_text`. What they read back, such as
`document.sha256`, is still a `str` wherever one is wanted: a dictionary key, a path or JSON.
Plain text passed as a sha is a `ty` error, and a `ValueError` at the three constructors.

## Verification

- `just gates` at the head, and the CI run of the pull request.
- Codex verifies and reviews the pull request once. `.claude/skills/codex-review/run.sh` takes
  a step number and reads `docs/plans/step-NN.md`, so it cannot take this plan. The Build
  session runs the same `codex exec` command as `run.sh pr` does, in a throwaway worktree, with
  the `pr` prompt changed in two places: the plan is this file, and the check is the table
  above. The gates run the tests of steps 2 and 3, whose code changes. The Plan run did the
  same with the `plan` prompt, and the fix review needs the same change to the `fix` prompt.
- One fix round, then Codex reads the fix diff. One Fable read of the whole diff.
