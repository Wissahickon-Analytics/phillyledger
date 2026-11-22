---
name: verify-step
description: Verify a phillyledger pull request or build step against the design. Runs the gates, proves each clause of the step's check with a named test, and audits the diff for weakened checks, purity breaks and altered numbers. Use whenever work on a build step claims to be done, and for every swarm verifier.
argument-hint: "[step-number] [base-branch]"
---

Verify build step $0 on the current branch against `docs/design.md`. The base is `$1`, or `main`
when no base is given. Report findings. Do not fix anything.

## Gather

- `git diff <base>...HEAD` and `git log <base>..HEAD`.
- Step $0 in design section 15, the module tables in section 12, and every section the step
  names.
- `docs/plans/step-NN.md` for the pull request this branch is meant to deliver, and
  `docs/progress.md` for what the builder claims.

## Gates

Run each and record the command and its result: `uv run pytest`, `uv run ruff check .`,
`uv run ruff format --check .`, `uv run ty check`, `uv run lint-imports`. A gate that does not
exist yet (before step 1 builds it) is reported as missing, not as passing.

## The check

Go through the step's check in section 15 clause by clause. For each clause this pull request
owns in the plan, name the test that proves it and run that test alone. A clause with no test, or
a test that would still pass if the clause were false, is a finding. Prove that second case by
breaking the code the clause describes in a scratch copy and showing the test still passes.

## Audits

1. **Weakened checks.** Deleted or loosened assertions, `skip`, `xfail`, widened tolerances,
   broad `except`, `# type: ignore`, `noqa`, fixtures regenerated without a reason in the
   commit.
2. **Design drift.** Names, signatures, types and module boundaries that differ from the design
   without an entry under Deviations in `docs/progress.md`.
3. **Purity.** Anything in `checkedtables` or `datadesk.core` that touches files, sockets,
   processes, the clock, the environment, randomness or logging, or keeps mutable module state.
4. **Honest numbers.** Code that changes a printed value, fills a missing one, guesses, or binds
   a column by position where a caption exists.
5. **Kit shape.** `bool` parameters or flag fields in `checkedtables`; a closed list extended
   without the pin test and the design changing together.
6. **Quirks.** Each quirk the diff marks in `docs/evidence/coverage.tsv` has a test that
   exercises it.
7. **Reference repo.** `git -C ../gov-budget-data status --porcelain` is empty.

## Report

The gates with their results. Then each clause of the check: proven by which test, or not
proven and why. Then findings ranked most serious first, each with file and line, what is wrong,
and the command and output that show it. A finding without a run behind it is left out. Say
plainly when there are none.
