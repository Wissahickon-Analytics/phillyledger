# Codex review of a named plan

The `codex-review` skill takes a build step's number. Two plans have no number:
`docs/plans/standards-sweep-a.md` and `docs/plans/standards-sweep-b.md`. The sweep B Plan run
wrote its Codex prompt by hand, and its Build run would have to do the same for the `pr` and
`fix` prompts. This pull request lets `run.sh` take the name of a plan file in place of a step
number. It also fixes the path that `run.sh` gives Codex for the old repository. From a worktree
under `.claude/worktrees/`, the path pointed at `.claude/worktrees/gov-budget-data`, which does
not exist. All 23 prompts of the step 3 and sweep A reviews, which ran from worktrees, gave that
path. Each of their 7 `pr` reports says that the path was missing, and in each Codex used
`/Users/nhand/DataProjects/gov-budget-data` on its own.

## Track

Light track. The diff changes the review scripts, the two skills and `docs/plans/README.md`. It
can change no published value, no label or period, no part of the kit's public shape and no step
of the release protocol. The design names neither skill, so no deviation is recorded.

## The pull request

One pull request on the branch `tools/codex-review-named-plans`, with base `main`. It was cut
from `standards/sweep-a` at `665d3da`. Pull request 40 then landed on `main` as `cab37c5`, whose
tree is the same, so the branch moved onto `main` by a rebase that left its `git patch-id`
unchanged. It is not part of a GitHub stack. Sweep B's build branch gets the fix when it is cut
from `main` after this pull request lands.

## The check

| # | Clause | Proof |
| --- | --- | --- |
| 1 | `run.sh plan`, `pr` and `fix` take a step number or the name of a file under `docs/plans/` without `.md`. A name with a character other than a lowercase letter, a digit or a hyphen, a name that starts with a hyphen or with `step-`, and a name with no plan file in `HEAD`, such as `readme`, each stop with the usage line. | Runs with a stub `codex` on `PATH`. |
| 2 | A number builds the prompt the old script builds, line for line. From a worktree the only change is the old repository's path, on each line that names it. | `diff` of the prompt files that the old and the new script write for `plan 3` from the main checkout, and for `plan 3`, `pr 3` and `fix 3` from this worktree. |
| 3 | A name builds a prompt that names `docs/plans/<name>.md`. It says that design section 15 has no entry for the plan and that the plan's own check table is the check. The `pr` prompt lists each `docs/deviations/step-NN.md` that the plan names, or says it names none. | `plan`, `pr` and `fix` runs for `standards-sweep-b` and `standards-sweep-a`, with the stub. |
| 4 | A named plan's prompt is `.codex-review/<name>-<kind>-<sha>.prompt.md` and its report is `.codex-review/<name>-<kind>-<sha>.md`. `fix` reads the report of the `pr` or `fix` review of the head it answers, and stops with exit 6 without one. | The same runs. |
| 5 | The old repository is `gov-budget-data` beside the folder that holds the repository's `.git`, which is the main checkout, from the main checkout and from any worktree. When no folder is there, the script stops with exit 7 and writes nothing. | Runs from the main checkout, from this worktree, and from a scratch clone. |
| 6 | Codex runs through the named route end to end. | `codex-review pr codex-review-named-plans standards/sweep-a` reviews this pull request. |
| 7 | `codex-review/SKILL.md` with its `argument-hint`, `verify-step/SKILL.md` and `docs/plans/README.md` say what the script now does. The sentences of `CLAUDE.md` that name the commands speak of numbered steps and stay true. | Clause 6's review reads each changed sentence against the script. |
| 8 | The gates pass. | `just gates` at the head. |

## Choices

- **The deviations file.** The script finds every `docs/deviations/step-NN.md` path that the
  plan names, with `grep`. Each sweep plan names exactly one, the deviations file of step 3. A
  third argument was rejected, since `pr` and `fix` already take one. So was a fixed line in
  each plan, since sweep B's plan sits on another branch. A file that a plan names in passing
  costs Codex one more read.
- **The two forms of a prompt.** Each prompt keeps one text. Lines between `{{#step}}` and
  `{{/step}}` stay for a number, and lines between `{{#named}}` and `{{/named}}` stay for a
  name. The script deletes the other block and the marker lines, so a number gives the old
  prompt line for line.
- **The old repository's path.** `git rev-parse --path-format=absolute --git-common-dir` gives
  the main checkout's `.git` from any worktree, and `gov-budget-data` sits beside the main
  checkout. The script stops when no folder is there, since a wrong path went unseen through 23
  reviews. A repository made with `git init --separate-git-dir` keeps `.git` elsewhere, and its
  linked worktrees hold no record of the main checkout, so there the script looks beside the
  `.git` folder's parent. This repository does not use that layout.

## Files

- `.claude/skills/codex-review/run.sh`, `SKILL.md`, `prompts/plan.md`, `prompts/pr.md` and
  `prompts/fix.md`.
- `.claude/skills/verify-step/SKILL.md`.
- `docs/plans/README.md` and this file.

## Risks the build should probe

- macOS `sed` reads `{{` in an address as plain text. A probe on November 25, 2026 deleted a
  `{{#named}}` block and kept a `{{#step}}` block's text.
- A step number with a leading zero, such as `08`, fails `printf '%02d'` as an octal number. The
  old script has the same fault, and this pull request leaves it.

## Owner questions

None.
