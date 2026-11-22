---
name: codex-review
description: Get an outside review from Codex of a build step's plan or of a step's pull request, then verify each Codex finding before acting on it. Use after a step plan is written and after each pull request passes verify-step.
argument-hint: "plan <step> | pr <step> [base-branch]"
---

Codex is the reviewer from another vendor. Its findings are leads, not verdicts: keep only the
ones a run or a quote confirms.

## Run

1. Commit the work under review. The script reviews the committed HEAD and refuses a dirty tree.
2. Run `.claude/skills/codex-review/run.sh $ARGUMENTS` in the background. A review at high
   reasoning effort can take a long time; wait for it to finish rather than polling in a loop.
   The last line it prints is the path of Codex's report under `.codex-review/`.
3. If the script stops because `codex` is missing or the tree is dirty, report that in one line
   and go on. Never install Codex or change its configuration.

## Verify each finding

- For a finding with a command, rerun the command. Keep it when the output shows the failure and
  the failure breaks the design, the step's check, or a rule in `CLAUDE.md`.
- For a finding with quoted lines, open both files at those lines. Keep it when the quotes are
  exact and they conflict.
- Drop the rest, and merge findings that share a root cause.

## Act

- **Plan review.** Revise `docs/plans/step-NN.md` for each kept finding, or write why you
  disagree under a `## Codex review` heading at the end of the plan. Show the owner the kept
  findings with the revised plan before the build starts.
- **Pull request review.** Give each kept `blocks` or `should fix` finding to a fresh
  `pstack:poteto-agent` on the feature model, with the finding, its evidence, and the original
  brief. Rerun `verify-step` and this review on the new head. Record kept `minor` findings as
  follow-ups.
- Add a short summary to the pull request's `## Verification` section: the Codex report's path
  and commit, findings kept and fixed, findings dropped with the reason for each.
