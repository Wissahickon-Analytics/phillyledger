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

All seven are from November 25, 2026.

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
4. After Codex's review, this Plan run asked whether to add "the readers' refusal codes" to
   the list in hard rule 6. It had told him that proposal 4 pins the two enums and that the
   change edits a hard rule. He answered "Yes, add them".
5. This Plan run then asked "Keep the four kit constructors refusing a sha that is plain
   text?" It had told him that `WordRef`, `Page`, `Document` and `ReviewedReading` would refuse
   a sha that is not a `Sha256`, and that a kit user who passes plain text gets a `ValueError`.
   He answered "Yes, keep it".
6. This Plan run then asked "Keep unstaged in SkipReason, though no reader returns it yet?" It
   had told him that design section 3.2 lists `unstaged`. He answered "Yes, keep it".
7. This Plan run then asked "Build sweep B on the open sweep A branch, or wait until 39 and 40
   land?" He answered "Build on sweep A". The answer is not the go for the Build run.

Everything else in this plan was worked out after the first three answers. Each item under
"Proposals" is a proposal until he lands this plan, except where an answer above settles it.

## Proposals

1. One pull request holds both changes. They share `core/fetch.py`, `core/listings/__init__.py`
   and the design, and sweep A was one pull request.
2. `WordRef`, `Page`, `Document` and `ReviewedReading` refuse a sha that is not a `Sha256`.
   The first three refuse an empty one now. A caller with no type checker, such as a user of
   the kit from PyPI, then gets a `ValueError` at the constructor. `ty` does not see plain text
   that `dataclasses.replace` passes, and `test_records.py` has such a call. Answer 5 keeps
   this.
3. The refusals are two enums, one for each family of readers. `PERIOD_READERS` and
   `TITLE_RULES` each need one return type for every reader they hold. One shared enum would
   let `qcmr_title` return `period_ambiguous` with no report from `ty`.
4. Both enums are pinned in `test_closed_lists_are_pinned` and in design section 11.4. Answer
   4 lets the list in hard rule 6 of `CLAUDE.md` name them.
5. `SkipReason` has the four values that design section 3.2 gives `ListedLink.skip_reason`.
   The fourth, `unstaged`, has no reader that returns it yet. Answer 6 keeps it.
6. `ListedLink.skip_reason` takes the type `SkipReason | None`. It holds what a title rule
   returned and nothing else.
7. `parse_index` builds `supersedes` with `Sha256` too, since it is the sha of an earlier
   version.
8. The `datadesk.core` import pin gains `typing.assert_never`, and the kit's gains
   `typing.Self`.
9. Tests that hold the fetch pull request's body and the lines `fetch` prints to exact text.
   The present tests look for substrings.

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
    UNSTAGED = "unstaged"
def qcmr_title(title: str) -> EditionKey | SkipReason: ...

# datadesk/core/fetch.py
class PeriodRefusal(StrEnum):
    UNREADABLE = "period_unreadable"
    AMBIGUOUS = "period_ambiguous"
    NOT_A_QUARTER_END = "period_not_a_quarter_end"
def qcmr_period(page1_text: str) -> Period | PeriodRefusal: ...
```

`Sha256` is the one builder. It builds the value from the 64 characters it matched, never from
`str(text)`, so a `str` subclass with its own `__str__` cannot give a `Sha256` of another
length. It raises `ValueError`, and it returns no finding, because a sha is never the
publisher's data. The code computes it from bytes, or reads it from one of the repo's own
files, where the caller of the parser already turns a `ValueError` into a finding (`_read_index`
gives `index_unreadable`). `.claude/rules/core-purity.md` says to raise only for a broken
invariant, and this is one.

A `Sha256` is the sha256 of a file's bytes: a publisher file, a listing's HTML, a release
manifest. A cache key is also a sha256, of a tuple of inputs. It names no file, so `cache_key`,
`word_keys`, `compare_keys` and the code tree sha keep their types until the step that builds
each cache.

These positions take `Sha256` where they take `str` now, and `Sha256 | None` where marked.

- Kit: `WordRef.doc_sha256` and the first member of the tuple `WordRef._order` returns,
  `Page.doc_sha256`, `Document.sha256`, `ReviewedReading.doc_sha256`, and the `sha` parameter of
  `page_from_text`.
- `datadesk.core`: `DocumentVersion.sha256` and `.supersedes` (or `None`), the `sha` parameter
  of `ArchiveIndex.by_sha`, the locals `editions` and `chain` of `index_problem`,
  `Fetched.sha256` (or `None`), `StoreObject.sha256`, the parameter of `_pdf_key`, whose result
  stays a `str`, `EditionNote.doc_sha256` and `Listing.html_sha256`.
- `datadesk.shell`: `FetchRun.listing_sha256`, the `sha` parameter of `put_immutable`, and the
  local `held` of `run_fetch`.

Three places build a `Sha256`. `_version` in `core/index.py` builds `sha256` where the guard of
pull request 38 stands now, before it looks at `urls`, so a line with both wrong still reports
the sha. It builds `supersedes` unless the JSON value is `null`. `parse_listing` in the core
builds it from the digest of the HTML. `run_fetch` in the shell builds it from the digest of
each body.

`confirm_period` and `parse_listing` each match the reader's result with one arm for each
member and a last arm that calls `assert_never`. After that match `parse_listing` still appends
the link and returns the `Listing`. `confirm_period` puts `refusal.value` in `Finding.code`, so
the code stays a plain `str`. `_clears` takes a reader typed `Callable[[str], Period |
PeriodRefusal]` and keeps its `==`, since a refusal never equals a `Period`. `watch.py` compares
`skip_reason` with `SkipReason.NOT_A_QUARTER_END`.

## What the runs showed

The Plan run tried three forms of `Sha256` at `36807de` with a throwaway script that edits
`packages/*/src` and no test. The scripts are not committed, and the two scratch branches are
local and not pushed. Every pytest count in this plan is from a shell with none of the four
`DATADESK_CONTRACT_S3_*` variables set, which is why 7 tests skip.

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

The chosen form was then run with both enums on `643d663`, sweep A's head at that hour. The
baseline there is 491 passed and 7 skipped, and the kit size report prints 735 lines. The saved
prototype is the local commit `0f4c018`.

- With `typing.assert_never` and `typing.Self` added to the import pin and no other test file
  edited, 491 passed. Without `typing.assert_never`, 3 tests failed, all on the import pin.
- `ty` reported the same 118 errors and none in `src`. `lint-imports` kept its 9 contracts.
  The kit size report printed 746 lines. `render_index` gave back the committed index.
- ruff's `PYI034` asks that `__new__` return `Self`. The purity tests failed on
  `from typing import Self` until the kit's pin held it.
- `eval(repr(word)) == word` held for a `Word`, and the sha came back as a `Sha256`.
- With the `PeriodRefusal` arm removed from `confirm_period`, `ty` printed
  `error[type-assertion-failure] Type PeriodRefusal is not equivalent to Never`.
- With three kit constructors changed to refuse plain text and no test edited, pytest could not
  collect `test_cells.py` and `test_lines.py`. So the constructors tighten after the tests
  build a `Sha256`.
- The prototype's builder called `str.__new__(cls, text)`. For a member of a `(str, Enum)`
  class that holds 64 hex characters it returned `Sha256('Digest.SAMPLE')`, 13 characters
  long. The Codex review found this, and it is why the builder builds from the matched text.

## The check

One pull request, SB, owns every clause. A test file is named once, and a later clause gives
the test's name alone.

| # | Clause | Proof |
| --- | --- | --- |
| 1 | `Sha256` holds 64 lowercase hex characters and equals its text. It raises `ValueError` for an empty string, an uppercase digit, 63 or 65 characters, a trailing newline, and a value that is not a `str`. Given a `str` subclass whose `__str__` gives other text, it holds the 64 characters it checked. | `test_sha256_holds_64_lowercase_hex_characters_and_equals_its_text`, `test_sha256_refuses_any_other_value` and `test_sha256_of_a_str_subclass_holds_the_text_it_checked` in the kit's `test_refs.py` |
| 2 | The `repr` of a `Sha256`, and of a `WordRef` that holds one, is an expression that rebuilds an equal value whose sha is a `Sha256`. Step 4's fixture writer needs this. | `test_the_repr_of_a_word_ref_rebuilds_its_sha256` |
| 3 | `WordRef`, `Page`, `Document` and `ReviewedReading` raise `ValueError` for a sha that is not a `Sha256`, 64 hex characters of plain text and the empty string included. | `test_word_ref_refuses_a_sha_that_is_not_a_sha256`, and the same test for each of the other three in `test_words.py` and `test_records.py`. The present tests of an empty sha keep that input, passed through a value typed `object`, and their `match` text follows the new message. |
| 4 | Each field and parameter in the list under "The shapes" that is not a local or a private name has the annotation given there, and plain text passed to one fails `uv run ty check`. | `test_every_sha_position_is_annotated_sha256`, a new root test that reads each annotation with `get_type_hints`, with `ListedLink.skip_reason` among its rows. `test_planted_plain_text_sha_fails_ty` in `tests/test_gates.py`, built on `run_gate`, which appends the bad call. The locals and private names are read in the diff. |
| 5 | `render_index(parse_index(text)) == text` for the committed `index.jsonl`, and the pull request does not change that file. | `test_render_index_gives_back_the_committed_index_byte_for_byte` in `tests/test_archive_inventory.py`. `git diff <base>...HEAD -- packages/datadesk/src/datadesk/data/index.jsonl` prints nothing. |
| 6 | The base's tests pass, unchanged, against the new code. With `packages/*/src` as it stands before the four constructors tighten, and the test files of the base with two names added to the import pin in `tests/test_purity.py`, `uv run pytest` gives the base's count. | The run, recorded in the pull request with its commit. Codex repeats it in its throwaway worktree with `git checkout <base> -- packages/checkedtables/tests packages/datadesk/tests tests conftest.py` and the two names. |
| 7 | `parse_index` gives each version a `sha256` that is a `Sha256`, and a `supersedes` that is a `Sha256` or, for JSON `null`, `None`. For text that is not 64 lowercase hex characters, a number or a list in either field, it raises `ValueError` with the builder's message. A line with a bad `sha256` and a bad `urls` reports the sha. | `test_parse_index_builds_a_sha256_for_each_digest_and_none_for_null`, on a chain of two versions, with `type(...) is Sha256`. `test_parse_index_refuses_a_supersedes_that_is_not_64_lowercase_hex_characters`, which matches the message, so the chain check of the base does not pass it. `test_parse_index_reports_a_bad_sha_before_a_bad_urls`. `test_parse_index_refuses_a_sha_that_is_not_64_lowercase_hex_characters`, unchanged. All in `test_index.py`. |
| 8 | `qcmr_period` returns a `Period` or a member of `PeriodRefusal`, and `qcmr_title` an `EditionKey` or a member of `SkipReason`. A skipped link that `parse_listing` returns carries the member. Each member's value is the string the reader returns now. | `test_qcmr_period_refuses_with_a_member_of_period_refusal` in `test_fetch.py`, `test_qcmr_title_skips_with_a_member_of_skip_reason` in `test_titles.py` and `test_a_skipped_link_carries_a_member_of_skip_reason` in `test_listings.py`, each with `is`. The readers' present tests, unchanged. |
| 9 | The three values of `PeriodRefusal` and the four of `SkipReason` are pinned, in order. | `test_closed_lists_are_pinned` in `test_library_shape.py`, with two more asserts |
| 10 | In `confirm_period` and in `parse_listing`, the match on the reader's result has an arm for each member and ends in `assert_never`. | Two mutants made by hand, one in each function, each with the refusal arm removed. `uv run ty check` prints `type-assertion-failure` at that function's `assert_never`. The pull request records both runs, and Codex repeats them. `run_gate` only appends text, so no gate test can remove an arm. |
| 11 | The code of the finding that `confirm_period` returns for a refusal is a plain `str`. | `test_confirm_period_puts_the_refusal_in_the_finding_code_as_plain_text`, with `type(finding.code) is str` |
| 12 | The body of the fetch pull request, and the lines that `fetch` prints, are the same text as before, for a run that adds a report, a run that rejects one and a run that changes nothing. Each sha and each store key in them is plain text. | `test_the_body_of_the_fetch_pull_request_is_exact` in `test_fetch.py` and `test_fetch_prints_exact_lines` in `test_fetch_command.py`. Each compares whole text, with the sha and the store key typed out in the test. Both are written first and pass before any file under `packages/*/src` changes. |
| 13 | The design and the rules say what the code does. | The lists under "Design and doc changes", read against the diff |

`FIELD_SNAPSHOT` does not change. `Sha256` is not a dataclass, and no field changes its name.
`test_kit_dataclass_fields_are_pinned` passed unchanged in every run above.

## The pull request

- **Branch.** `standards/sweep-b`, cut from `standards/sweep-a`, the branch of pull request 40,
  at the head that has pull request 40's verdict, by answer 7. That head was `363b9b5` when
  this plan was written. Sweep A wrote docstrings in every file that sweep B changes, so B cannot be built
  beside it.
- **Base and title.** Base `standards/sweep-a`. Title
  `refactor(standards): give a sha256 its own type and name the readers' refusals`.
- **Landing order.** The step 3 stack (32, 33, 35, 36, 37, 38), then 39, then 40, then SB. The
  pull request that holds this plan is based on `docs/code-standards` and can land any time
  after 39. If it has not landed under SB's branch, SB's first commit is this file, unchanged.
  SB is not part of step 3's GitHub stack, as 39 and 40 are not.
- **Order of work.** Tests first (`CLAUDE.md`, Tests).
  1. The tests of the table. Those of clauses 5 and 12 pass at once, since they hold what the
     code does now. The rest fail, and the pull request records that run.
  2. `Sha256`, the two enums and the two pinned names, without the constructor guards. The run
     of clause 6 is made here.
  3. The tests build a `Sha256` where they pass a sha, until `ty` passes. The build also reads
     each `replace(` call and each JSON input in the tests, which `ty` does not check.
  4. The four constructors tighten.
  5. The design and the docs.
- Only the head has to pass the gates. Every run is made with the four
  `DATADESK_CONTRACT_S3_*` variables unset, so no test opens a socket or reaches a bucket.
- It needs no call to R2, no request to the City and no Textract call.

## Files

- `packages/checkedtables/src/checkedtables/`: `refs.py`, `words.py`, `records.py`,
  `testing.py`.
- `packages/datadesk/src/datadesk/core/`: `domain.py`, `index.py`, `fetch.py`, `records.py`,
  `watch.py`, `listings/__init__.py`, `listings/titles.py`.
- `packages/datadesk/src/datadesk/shell/`: `cli.py`, `run_fetch.py`.
- Tests: the 17 files that pass a sha as plain text, `test_titles.py`, `test_library_shape.py`,
  `tests/test_purity.py`, `tests/test_gates.py`, `tests/test_archive_inventory.py`, and one new
  root test file for clause 4.
- `docs/design.md`, `docs/deviations/step-03.md`, `docs/principles.md`, `docs/progress.md`,
  `docs/plan-notes.md`, `CLAUDE.md` and `.claude/rules/core-purity.md`.

## Design and doc changes

The build makes these in the same pull request (hard rule 7). The counts are from
`docs/design.md` at `36807de`.

- **Design, a sha by name.** 27 lines name a sha or `supersedes` and type it `str`. Each
  becomes `Sha256`. Built: `WordRef`, `Page`, `Document` and `ReviewedReading` (2.1),
  `DocumentVersion.sha256` and `.supersedes`, `ArchiveIndex.by_sha` and `EditionNote` (2.2),
  `page_from_text` (3.1), `Listing`, `Fetched` and `StoreObject` (3.2), `FetchRun` (4.2),
  `put_immutable` (4.5). Not built yet: `Table` and `FailureKey` (2.1), `WordSourcePlan`,
  `TablePages` and `ReleaseRow` (2.2), `records_for`, `illegible_pages`, `WordJob`, `ParseJob`
  and `textract_to_document` (3.2), `PdfReader.words` (4), `ExpectedTables` and
  `ArticleFigure.manifest_sha256` (18.3).
- **Design, a sha by meaning.** Five more places hold file shas under another name or pass a
  raw digest. `Alias.editions` (2.2) and the `scope` of `match_acknowledgments` (3.1) are sets
  of document shas. The `run_fetch` sketch (4.2) keys `held` by sha and passes a `hexdigest()`
  to `Fetched`. The OCR sketch (4.3) passes one to `put_immutable`. The build searches the
  design for "sha" once more, since this list came from two passes.
- **Design, what stays.** The cache keys, by the boundary under "The shapes". The
  `accepted_diff` of `release_command` (4.5) is a word from the command line, and the plan of
  the release step says what it parses into.
- **Design, the refusals.** Five lines in 3.2: `ListedLink.skip_reason`, `TITLE_RULES`,
  `qcmr_title`, `PERIOD_READERS` and `qcmr_period`, with the two enums beside them.
- **Design, the rest.** Section 2.1 gains `Sha256`, with what it refuses and why it raises. The
  blocks of `WordRef`, `Page`, `Document` and `ReviewedReading` show the new check, as the
  opening of 2.1 asks of a pull request that adds one. The `refs.py` row of 12.1 names
  `Sha256`. The test listing of 11.4 gains the two pins.
- **Docstrings.** Each docstring of a changed name says `Sha256` or names the enum. Sweep A
  wrote `str` in those of `refs.py`, `words.py`, `records.py`, `testing.py` and `fetch.py`.
- **`docs/deviations/step-03.md`.** A "Standards sweep B" section after sweep A's. It covers
  the kit types that step 2 built too.
- **`docs/principles.md`, section 8.3.** Two changes, both with the owner's answer above. Where
  a value is one piece of text with a rule, 8.3 allows a `str` subclass whose constructor
  checks the rule, beside the frozen dataclass with one builder. `fetch_command`'s
  `isinstance(repo, tuple)` leaves the examples of the loose form, and the sentence on
  `qcmr_period` moves to the past tense.
- **The three places that say values are frozen dataclasses.** `CLAUDE.md` (Code), section 5
  of `docs/principles.md` and `.claude/rules/core-purity.md` each name the allowed exception.
- **`CLAUDE.md`, hard rule 6.** Its list gains "the readers' refusal codes", by answer 4.
- **`docs/progress.md` and `CLAUDE.md`.** The note "The type rules of the code standards are not
  met yet" and the dated bullet in the Code section shrink to "What sweep B leaves" below. The
  note's claim that `gather_repo` owes a named result goes, by answer 3. The note that says
  `test_closed_lists_are_pinned` pins `NoteKind` alone names the two enums.
- **`docs/plan-notes.md`.** Two notes for step 4's plan. A word fixture prints each sha as
  `Sha256('...')`, once for each word, unless the writer binds it to a name. `Unreadable.reason`
  is still an open `str`. One note for the step that builds the TOML loaders: a loader builds a
  sha with `Sha256` and turns its `ValueError` into a finding.

## Risks the build should probe

- **A message that prints a sha with `repr` changes.** `repr` now shows `Sha256('...')`, so a
  `ValueError` of `WordRef` or `Page` that prints a `WordRef` changes, and so does the one
  `doc_of` raises for pages of two files. `Document` prints the sha itself and does not
  change. No message is a published value.
- **A message of `parse_index` changes.** For a `supersedes` that is not a sha, the base says
  "supersedes bad, not of its edition" for text and raises `TypeError` for a list. Both become
  the builder's `ValueError`. `_read_index` catches all three, and the finding is still
  `index_unreadable`.
- **Equal to its text.** `Sha256(x) == x` is `True`, so `ty` does not report a comparison of a
  sha with text that no builder checked. A parser builds the `Sha256` where the text enters.
- **`dataclasses.replace` in `datadesk`.** `DocumentVersion`, `Fetched` and the other
  `datadesk` types have no guard, so plain text that a test passes through `replace` stays
  plain. The build reads those calls.
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
- A URL, a store key, a cache key, a `listed_at` stamp and an edition id, by answer 1.
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
Plain text passed as a sha is a `ty` error, and a `ValueError` at the four constructors.

## Verification

- `just gates` at the head, and the CI run of the pull request.
- Codex verifies and reviews the pull request once. `.claude/skills/codex-review/run.sh` takes
  a step number, and its prompts and the `verify-step` skill read `docs/plans/step-NN.md`,
  `docs/deviations/step-NN.md` and a check in design section 15. Sweep B has none of the three
  under those names. The Build session runs the same `codex exec` command as `run.sh pr` does,
  in a throwaway worktree, with a prompt that gives Codex this file as the plan, the table
  above as the check, `docs/deviations/step-03.md` as the deviations, and the sha of the base.
  The audits of `verify-step` stay.
- The prompt names `gov-budget-data` for the audit that nothing there changed. No path is
  written by hand. The folder sits beside the main checkout, and from a worktree
  `git rev-parse --path-format=absolute --git-common-dir` gives the main checkout's `.git`.
  `run.sh` takes the parent of the current checkout, which from a worktree is
  `.claude/worktrees`, where no `gov-budget-data` exists.
- The fix review gets the same prompt changes and the report of the first review. The Plan run
  did the same with the `plan` prompt.
- One fix round, then Codex reads the fix diff. One Fable read of the whole diff.

## Codex review

Codex read this plan once, at `dfdd9193`, and raised 14 findings. A run or a quote confirmed
all 14, and the plan above answers each. It differs from Codex's advice in two places.

- Codex asked that `_clears` "account for both outcomes" of the reader. It keeps its `==`. The
  function asks whether a note's quotation reads as the printed period. A refusal is never
  equal to a `Period`, so it clears nothing, which is the right answer for a quotation that no
  reader can read.
- Codex offered two ways to handle `unstaged`: keep it in the enum, or name the step that adds
  it. The plan keeps it, since the design already gives the list of four.
