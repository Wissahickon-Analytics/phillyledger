---
name: codex-review
description: Get Codex to review a build step's plan, to verify and review a pull request in one pass, or to read a fix round, then confirm each Codex finding before acting on it. Use after a step plan is written, after a pull request passes the gates, and after its fix round.
argument-hint: "plan <step> | pr <step> [base-branch] | fix <step> <reviewed-head>"
---

Codex is the reviewer from another vendor, and its usage is not the scarce budget. It does the
verification that Claude agents once did. Its findings are leads, not verdicts: keep only the
ones a run or a quote confirms.

## Run

1. Commit the work under review. The script reviews the committed HEAD and refuses a dirty tree.
2. Run `.claude/skills/codex-review/run.sh $ARGUMENTS` in the background and wait for it to
   finish. Do not poll it. The last line it prints is the path of Codex's report under
   `.codex-review/`.
   - `plan N` reads the plan of step N in a read-only sandbox.
   - `pr N <base>` runs the check and the audits of the `verify-step` skill, then the review,
     on `git diff <base>...HEAD`. Codex works in a throwaway worktree with its own environment,
     in a sandbox with no network, so it runs tests and breaks code there to test a claim.
   - `fix N <reviewed-head>` reads only the fix round, `git diff <reviewed-head>..HEAD`. It
     needs the report of the `pr` or `fix` review of that head, and stops without it.
3. If the script stops because `codex` is missing or the tree is dirty, report that in one line
   and go on. Never install Codex or change its configuration.

## Confirm each finding

- For a finding with a command, rerun the command. Keep it when the output shows the failure.
- For a finding with quoted lines, open both files at those lines. Keep it when the quotes are
  exact and they conflict.
- Drop the rest, and merge findings that share a root cause.

## Sort what is kept

`docs/plans/README.md`, "What blocks a pull request", says which confirmed findings block.
Every other one is a follow-up. Codex labels each finding, and its label is a lead too.

## Act

- **Plan review.** Revise `docs/plans/step-NN.md` for each kept finding, or write why you
  disagree under a `## Codex review` heading at the end of the plan. Show the owner the kept
  findings with the revised plan before the build starts.
- **Pull request review.** Give the findings that block to one fresh `pstack:poteto-agent` on
  the feature model, with each finding, its evidence, and the original brief. That is the pull
  request's one fix round. The message of its last commit lists each finding of the review by
  its title as fixed, follow-up or dropped, with the reason for a drop, so the fix review can
  account for each. Then run `just gates` and `fix N <reviewed-head>` on the new head.
- **Fix review.** A finding that blocks in the fix diff goes to the owner. So does any second
  round. Do not start one without his go.
- List the follow-ups under `## Follow-ups` in the pull request's text.
- Add a short summary to the pull request's `## Verification` section: each Codex report's path
  and commit, the findings fixed, and the findings dropped with the reason for each.
