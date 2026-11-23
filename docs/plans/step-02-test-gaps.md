# Build step 2, three proof gaps

This plan runs on the light track (`docs/plans/README.md`). It closes three gaps in the proofs of
build step 2 before later steps build on the kit. In each gap the code at the base is right, and
the tests would not catch a regression. The gaps are recorded under "Follow-ups after step 2" in
`docs/progress.md`.

## The pull request

One pull request, `test(checkedtables): close three proof gaps of step 2`, on the branch
`step-02/f-test-gaps`. Its base is `step-02/e-records` at `2638173a`. It changes tests and docs
only, so `git diff 2638173a HEAD --stat -- packages/checkedtables/src` is empty at its head.

## The gaps

Each test is proved by a mutation. The change to the code is made in a scratch copy or as an
in-memory patch, never committed. The test fails under the change and passes at the head.

| Gap | Test that closes it | Change to the code that must make the test fail |
| --- | --- | --- |
| G1, clause C1b. No test states the value of an OCR amount in a fixed-decimal column. | `test_amount_digits_are_the_digits_of_its_words` also draws numbers printed with 0 to 12 decimals, lexes each cell in the drawn column and in the column that declares its printed decimals, and gives each OCR word a confidence of None or 0 to 100. `test_lexer_round_trip` also lexes each value in the column that declares its decimals, on both sources, and compares by `as_tuple()`. The plain test `test_an_ocr_amount_keeps_the_decimals_it_prints` reads `65.8` on an OCR page in the one-decimal column and `828,904.89` in a two-decimal column. | `lex_cell` rounds every OCR `Amount` in a one-decimal column to a whole number. The same only when the first word has a confidence. The same for every OCR `Amount` in a two-decimal column. Each fails both properties and the plain test. |
| G2, clause C1a. `pages()` never draws a word together with its children. | `pages()` in `test_lines.py` may draw a run that holds the parent and its children. `test_every_word_lands_in_exactly_one_line` gains the example `PARENT_WITH_CHILDREN`. | `group_lines` drops every word whose `ref.child` is None when another word of the page has the same index and a child. It fails the named test with its `@example` decorators and without them. The ten breaks of `/tmp/swarm-s2-c/worker-9/verify-fix4-mutations.sh` still fail it. |
| G3a, records. Every successful application uses the id `r1`. | `test_a_reviewed_cell_names_the_record_that_was_applied` applies records of the ids `cash-fy07-q3` and `cash-fy08-q1`, with a reading and with none. | `apply_reading` writes `r1` in place of the reading's id. |
| G3b, records. The signed-value property cannot see the sign of a zero. | `test_a_reviewed_amount_keeps_the_digits_seen` compares `as_tuple()` and gains the example `0.0` read as `(0.0)`. `test_a_reviewed_zero_keeps_its_sign` reads `(0.0)` as `(0.0)` in the one-decimal column. | A reviewed zero loses its sign. |

## Files

- `packages/checkedtables/tests/test_lex.py`, `test_lines.py` and `test_records.py`.
- `docs/plans/step-02-test-gaps.md`, this plan, as the first commit.
- `docs/progress.md`: each of the four follow-up bullets says that this pull request closes it,
  with the test and the mutation that now fails. The step 2 row stays as it is.

## Verification

- The six gates on the committed head, and `uv run pytest -k "exactly_one_line or round_trip or
  digits_of_its_words or val_probe or digit_swap"` with 6 passed.
- Each mutation above, run and seen to fail, with its output in the trail
  `.audit/owner-s2-f.tsv` of the root checkout.
- The `CI` workflow's `pull_request` run on the head passes on Python 3.12 and 3.14.
- One verifier runs `verify-step` in full at the finished head, and Codex reviews the pull
  request once.
