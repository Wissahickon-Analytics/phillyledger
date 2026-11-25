# Build step 3, the cleanup the owner picked

This plan runs on the light track (`docs/plans/README.md`). Step 3's five pull requests left 42
follow-ups. On November 25, 2026, the owner picked 15 of them for one cleanup pull request ("Your
15 picks"). Eleven are false sentences in the docs, two are rules that no test holds, and two are
index lines that `parse_index` should refuse. The other 21 he kept go into `docs/followups.md`.
None of the 15 can change a published value, a label, a period, the kit's public shape or the
release protocol.

## The pull request

One pull request, `fix(datadesk): close the step 3 follow-ups the owner picked`, on the branch
`step-03/f-cleanup`. Its base is `step-03/e-archive` at `d3b0666`, and it is the sixth branch of
GitHub stack 34. It needs no call to R2 and no request to the City. It changes neither
`index.jsonl` nor the inventory, and it changes no test of a step 3 clause except by adding tests.

## The items

The numbers are those of the follow-up list the owner sorted. A false sentence is rewritten to
say what a run shows, and the run is recorded in the pull request.

| Item | What closes it | The run that proves it |
| --- | --- | --- |
| 1 | The S3-A entry of `docs/deviations/step-03.md` names the mutant that fails the `a_chain_that_runs_into_a_cycle` case: removing `sha is not None or`. Removing the stop on a repeated version loops forever. | Each mutant run under a timeout. |
| 2 | The S3-C fix round entry says what the month word of `PERIOD_ENDING` is, and drops "as in the title rule", since the title rule also wants letters. | `PERIOD_ENDING` reads "Mar½ch" as a month word, and the title rule reads that title as `unrelated`. |
| 3 | The entry on the quarter start says which tests fail when the start moves back a year. | The mutant run: 19 tests fail, and the cases that expect a finding pass. |
| 4 | The entry on `listed_at` says a later upload stamp is always a new URL, and that the feed lists the same URLs again. | The count of the July fixture's QCMR URLs that the November feed lists again: 34 of 34. |
| 5 | The S3-D entry names what reading the last page fails, if anything. | The mutant run. |
| 6 | The S3-D entry names `_printed_date` as the function that catches the `ValueError` of `date`. | A quote of the `except` in `core/fetch.py`. |
| 7 | The S3-D entry credits the fourth round with naming `_printed_date`. | The round records of pull request 36. |
| 8 | The S3-D entry says what `rg -n "except"` prints in the kit: one docstring line of `checkedtables/text.py` and no catch. | The command's output. |
| 9 | Design section 9 says a `KeyboardInterrupt` that escapes the core is the operator's stop, not a bug, and agrees with section 4.2, which already says `main` prints its traceback and returns 1. A deviation entry records it. No code changes. | Both sections quoted. |
| 10 | QPOS-Q38 says the cover of the FY2027 Q1 report has no text a program can read, and that later pages do. It changes in the dossier row, `quirks.tsv`, the S3-E deviation entry, the step 7 note in `docs/plan-notes.md`, and any other place that says the whole report. | `pdftotext` on pages 1, 6 and 50 and `pdffonts` on the file `qcmr-2026-09-30.pdf` of the held folder. Page 6 prints "For the Period Ending September 30, 2026". No OCR, no index run and no Textract call. |
| 11 | The S3-E entry says three rows of the section 13 table change and `fetch.qcmr_period` is a new row. | The section 13 table against the evidence files. |
| 12 | Already held. `test_new_bytes_listed_before_the_current_version_are_rejected` and `test_older_bytes_after_a_repost_of_the_current_sha_are_listed_before_current` in `packages/datadesk/tests/core/test_fetch.py` both fail when the `listed_before_current` rule is removed. The follow-up searched only the root `tests/` folder. No test is added. | The mutant run at `d3b0666`: 2 failed, 53 passed. |
| 13 | A test in `packages/datadesk/tests/shell/test_fetch_command.py` runs `main` to exit 0 with both R2 keys planted in text that `main` prints to stdout. Stdout holds `$DATADESK_R2_ACCESS_KEY_ID` and `$DATADESK_R2_SECRET_ACCESS_KEY` and neither key. | The test fails when the stdout `print` in `cli.main` drops `hide_keys`, and passes at the head. |
| 26 | `parse_index` raises on a line whose `urls` is not a JSON list. `gather_repo` already turns the raise into `index_unreadable`. | A test in `packages/datadesk/tests/core/test_index.py`, run before the guard (the bare string parses as 95 URLs) and after. |
| 27 | `parse_index` raises on a line whose `sha256` is not 64 lowercase hex characters. The design states no form for the sha, so the rule joins the `core/index.py` block of the design and a deviation entry. | A test with the FY2022 Q1 line beside a copy under FY2022 Q2 whose sha is the same in upper case, run before the guard (two versions) and after. |

Item 27 refuses the line and does not fold its case. `hexdigest()` writes lowercase, so another
form can come only from a hand edit, and a number is published only from what the input says
(`CLAUDE.md`, hard rule 4). Folding would rewrite input without a finding.

## Follow-ups after step 3

`docs/followups.md` gains the section "Follow-ups after step 3" in the form of the step 1 and
step 2 sections. It holds the 21 items the owner kept, 14 to 25 and 28 to 36. Item 30 notes that
a missed revised report is the one kept item that could change what gets published. The five
drops (37 to 41) and the closed item 42 stay out.

## Files

- `docs/plans/step-03-cleanup.md`, this plan, as the first commit.
- `docs/deviations/step-03.md`, `docs/design.md`, `docs/followups.md`, `docs/plan-notes.md`.
- `docs/evidence/dossiers/QPOS.md` and `docs/evidence/quirks.tsv`, for QPOS-Q38.
- `packages/datadesk/src/datadesk/core/index.py`.
- `packages/datadesk/tests/core/test_index.py` and
  `packages/datadesk/tests/shell/test_fetch_command.py`.

## Verification

- `just gates` at the head, and the CI run of the pull request.
- Each new test fails with its rule removed and passes at the head. The 20 committed index lines
  still parse, and `tests/test_archive_inventory.py` passes.
- Codex verifies and reviews the pull request once (`codex-review pr <N> step-03/e-archive`).
