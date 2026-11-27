# Build step 4, the cleanup the owner picked

This plan runs on the light track (`docs/plans/README.md`). Step 4's five pull requests, 46, 47,
49, 50 and 51, left 55 follow-ups. On November 27, 2026, the owner was sent one list with a
proposed sort and answered "Take the sort": 7 already closed, 20 for this pull request, 4 as notes
for later plans and 24 kept in `docs/followups.md`. Ten of the 20 are sentences in the docs, one
is a refusal that the codec's docstring already promises, five are tests, each against the mutant
its follow-up names, one is a return type, and three are sentences of `CLAUDE.md`. None can
change a published value, a label, a period, the kit's public shape or the release protocol, and
no word fixture changes.

An id such as `49-6` means follow-up 6 of pull request 49, as its text lists it under
`## Follow-ups`.

## The pull request

One pull request, `fix(datadesk): close the step 4 follow-ups the owner picked`, on the branch
`step-04/f-cleanup`. Its base is `main` at `cfd67ee`. The step 4 stack has landed, so the branch
stands alone. It needs no call to R2 and no request to the City. Runs that read the held PDFs
name the folder through `DATADESK_HELD_PDFS`.

## Already closed

No action. Each is listed with the reason.

| Item | Why it is closed |
| --- | --- |
| 46-3 | Pull request 51 set the step 4 row of `docs/progress.md` to "Words: PDF adapter, word cache, codec". |
| 47-8 | Moot. The encoding of `70b2aa3` never reached `main`, and no command built a `DirCache` before pull request 50, so no entry in that encoding exists. |
| 47-10 | Pull request 50 draws page widths and heights as an `int` or a `float`, and a decoder that reads `792` as `792.0` fails the property. |
| 47-11 | The `Deps` docstring now reads "The adapters a command runs with." |
| 47-12 | Pull request 49's reader gives an `int` rotation and makes any other an `EffectError`. |
| 51-7 | The same sentence as 50-5, closed with it. |
| 51-15 | The note "`shell/cli.py` runs past its estimate" in `docs/progress.md` records it. |

## The items

A false sentence is cut, or shortened to what a signature, a test or a run shows. The fix adds no
claim and no list of cases. Each run is recorded in the pull request.

| Item | What closes it | The run that proves it |
| --- | --- | --- |
| 47-4 | The S4-B entry of `docs/deviations/step-04.md` stops saying `decode_document` refuses "bytes it did not write", and any other place that says so. | A leading space and an extra key decode. |
| 47-9 | Design section 1.4 lists the reader's cache adapter again, `phillyledger._shell.cache_dir`, as sections 4.6 and 12.2 do. | The three sections quoted. |
| 49-3 | Design section 4 stops saying a broken media box or crop box at or before the last page asked for always stops the read. | `/CropBox [0 0]` on page 1 of a built PDF, then `words` of page 2: the read goes on. `/CropBox 42` there stops it. |
| 49-4 | Design section 4 stops saying a missing page's `EffectError` is chained. | The `__cause__` of the error that `words`, `render` and `page1_text` raise for a page the file lacks and for a PDF with no page. |
| 49-5 | The S4-C entry stops saying each line object gives a rule. | A line 7 points long gives none. |
| 49-10 | The `WordSource` docstring in `checkedtables/words.py` stops giving `pdfplumber==0.11.4;dedupe_chars` as a tool string. The docstring alone changes. | `PdfPlumberReader().tool()` printed. |
| 50-5 | Design section 12.3's row for `shell/cli.py` stops saying each command reads the clock once, and so does the Clock row of section 1.4, which says the same. | `rg` for the clock calls in `shell/cli.py`: `fetch` reads it and `fixture` and `crops` do not. |
| 50-11 | Design section 12.3's row for `core/codec.py` names `render_fixture`. | The module's public names. |
| 51-10 | The S4-E entry says the plan's shape 13 named the command, the crop file and the rule, where it says the design did. | `git show 851d3e3:docs/design.md` holds no `datadesk crops`. |
| 51-16 | The line of design section 4.2 that runs past 100 characters is rewrapped. | The line lengths of section 4.2's prose. |
| 47-3 | `decode_document` raises `ValueError` for a number that reads as an infinity, such as `1e400`, as its docstring and design section 3.2 say. A test in `packages/datadesk/tests/core/test_codec.py`. | The test fails before the guard and passes after. |
| 49-6 | A test in `packages/datadesk/tests/shell/test_pdf_reader_contract.py`, on a PDF it builds, fails when `extract_words` runs with other options and the tool string is unchanged. | It fails for each mutant the follow-up names: pdfplumber's defaults, `use_text_flow` dropped, and `x_tolerance` 30. |
| 50-6 | A test in `tests/test_word_fixtures.py` that `render_fixture(module.PAGE)` equals the text of each checked-in fixture. It runs in CI and reads no PDF. | It fails when `render_fixture` adds a comment to the `rotation` line. |
| 50-9 | A test in `packages/datadesk/tests/shell/test_fixture_command.py` with both R2 keys planted in what `fixture` prints: the lines it writes and its one-line message for an `EffectError` (hard rule 8). | It fails when each of those prints drops `hide_keys`. |
| 50-3 | `test_no_word_of_the_twenty_grid_pages_holds_a_font_code` asks that each fixture's sha be an indexed sha of its edition, as the plan's C3 paragraph says, and no longer the edition's current version. Clause C3's words and its font-code assertion do not change. | In a copy whose index adds a newer version of one edition, the old test fails and the new one passes. A fixture whose `SHA` is another edition's sha fails the new test. |
| 46-1 | A test in `packages/checkedtables/tests/test_lex.py` that a text-column cell with `(CID:21)` lexes as `Text`, since a font code is lower case (plan fact 9). | It fails when `lex_cell` lowers each word before the `(cid:` test. |
| 50-12 | `_fixture_sha` in `shell/cli.py` returns `Sha256 \| None`. | `uv run ty check` and the fixture command's tests. |
| 46-2 | Hard rule 6 of `CLAUDE.md` names the reasons a cell is `Unreadable` among the pinned lists. | `test_closed_lists_are_pinned` pins `UnreadableReason`. |
| 50-10 | The Tests sentence of `CLAUDE.md` on real pages says that CI's tests read real pages only as word fixtures, and one test that skips in CI regenerates them from the held PDFs. | `uv run pytest tests/test_word_fixtures.py -rs`. |
| 51-13 | The Code sentence of `CLAUDE.md` says a command builds the ports it reads, and `fetch` builds `Deps`. | Design section 4 and `shell/cli.py`. |

The three `CLAUDE.md` sentences are in the owner's pick, and nothing else in that file changes.
`decode_document` needs no new import for 47-3. If a change would add a name to the import pin in
`tests/test_purity.py`, the build stops and asks the owner.

## Notes for later plans

`docs/plan-notes.md` gains two notes and extends one, each dated November 27, 2026 and naming its
pull requests.

- 49-1 and 51-1, one note for the plan of the first step that renders or runs OCR on a page
  outside the 20 grid pages: word boxes and `render` use other frames when a page's media box is
  off the origin or its crop box is smaller.
- 49-9, for the step 5 plan: `extract_words` labels the bytes it reads with `job.doc_sha256` and
  never hashes them.
- 51-14 extends the step 5 note "Rules and margin page numbers on the P-1 grid pages": on the six
  pages with a margin page number, `group_lines` joins its digits to table lines.

## Follow-ups after step 4

`docs/followups.md` gains the entry "Follow-ups after step 4" in the form of the step 3 entry,
each item with its id: 47-1, 47-2, 47-5, 47-6, 47-7, 47-13, 47-14, 49-2, 49-7, 49-8, 50-1, 50-2,
50-4, 50-7, 50-8, 51-2, 51-3, 51-4, 51-5, 51-6, 51-8, 51-9, 51-11 and 51-12. For 51-8 it records
that the owner chose to keep it a follow-up on November 26 and again on November 27, 2026. An item
of the 20 that cannot close inside the limit above moves here, and the pull request says why.

## Files

- `docs/plans/step-04-cleanup.md`, this plan, as the first commit.
- `CLAUDE.md`, `docs/design.md`, `docs/deviations/step-04.md`, `docs/followups.md`,
  `docs/plan-notes.md`.
- `packages/checkedtables/src/checkedtables/words.py`, a docstring.
- `packages/datadesk/src/datadesk/core/codec.py` and `packages/datadesk/src/datadesk/shell/cli.py`.
- `packages/checkedtables/tests/test_lex.py`, `packages/datadesk/tests/core/test_codec.py`,
  `packages/datadesk/tests/shell/test_pdf_reader_contract.py`,
  `packages/datadesk/tests/shell/test_fixture_command.py` and `tests/test_word_fixtures.py`.

## Verification

- `just gates` at the head, the CI run of the pull request, and `git status` clean after both.
- Each new test fails against its mutant and passes at the head. The 20 fixtures keep their
  sha256 values.
- C1 and C3 on the held folder at the head, under Python 3.12 and 3.14.
- Codex verifies and reviews the pull request once (`codex-review pr step-04-cleanup main`).
