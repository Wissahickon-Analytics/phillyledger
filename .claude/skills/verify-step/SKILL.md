---
name: verify-step
description: Verify a phillyledger pull request or build step against the design. Proves each clause of the step's check with a named test, and audits the diff for weakened checks, purity breaks and altered numbers. Codex runs it for every pull request, through the codex-review skill.
argument-hint: "[step-number | plan-name] [base-branch]"
---

Verify build step $0 on the current branch against `docs/design.md`. The base is `$1`, or `main`
when no base is given. Report findings. Do not fix anything.

`$0` is a step number, or the name of a plan that is not a numbered step. That name is the
plan's file name under `docs/plans/` without `.md`, such as `standards-sweep-b`. Design section
15 has no entry for a named plan, so its own check table is the check, and "the step" below
means the work that it describes.

## Gather

- `git diff <base>...HEAD` and `git log <base>..HEAD`.
- The check, which is step $0 in design section 15 or the check table of `docs/plans/$0.md`.
  Then the module tables in section 12, and every section that the step or the plan names.
- The plan, `docs/plans/step-NN.md` or `docs/plans/$0.md`, for the pull request this branch is
  meant to deliver. The commit messages and the deviations file for what the builder claims.
  A step's deviations file is `docs/deviations/step-NN.md`. A named plan names its own.

## Gates

The Build session runs `just gates` at the head, and CI runs the same six gates. Do not rerun
them all. Run one only when a finding needs it. The `Justfile` gives each gate's command, and
the tools are in `.venv/bin`.

## The check

Go through the check clause by clause. For each clause this pull request owns in the plan, name
the test that proves it and run that test alone. A clause with no test, or a test that would
still pass if the clause were false, is a finding. Prove that second case by breaking the code
the clause describes in a scratch copy and showing the test still passes.

## Audits

1. **Weakened checks.** Deleted or loosened assertions, `skip`, `xfail`, widened tolerances,
   broad `except`, `# type: ignore`, `noqa`, fixtures regenerated without a reason in the
   commit.
2. **Design drift.** Names, signatures, types and module boundaries that differ from the design
   without an entry in the deviations file.
3. **Purity.** Anything in `checkedtables` or `datadesk.core` that touches files, sockets,
   processes, the clock, the environment, randomness or logging, or keeps mutable module state.
4. **Honest numbers.** Code that changes a printed value, fills a missing one, guesses, or binds
   a column by position where a caption exists.
5. **Kit shape.** `bool` parameters or flag fields in `checkedtables`; a closed list extended
   without the pin test and the design changing together.
6. **Quirks.** Each quirk the diff marks in `docs/evidence/coverage.tsv` has a test that
   exercises it.
7. **Reference repo.** No file that `git -C ../gov-budget-data status --porcelain` lists was
   written after this branch's first commit. Use the path the caller gives when the checkout
   is not beside that repository. The owner's own pending changes there are older, and do not
   count.

## Report

Each clause of the check: proven by which test, or not proven and why. Then findings ranked most serious first, each with file and line, what is wrong,
and the command and output, or the two quoted lines, that show it. Mark each finding `blocks` or `follow-up` by the rule
in `docs/plans/README.md`. A finding with neither a run nor quoted lines
behind it is left out. Say plainly when there are none.
