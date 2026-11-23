# Working on this repo with Claude Code

The main session runs Fable 5.2 and reviews. Opus 5.5 delegates write the code. Codex reviews
each plan and each pull request from outside. The workflow and principles come from pstack.

## One-time setup

1. Clone this repo next to `gov-budget-data`, so `../gov-budget-data` resolves from the repo
   root. Hooks need `python3` and `uv` on the path.
2. Start `claude` in the repo and accept the workspace trust prompt. The project settings set
   the session model to Fable at `xhigh` and pin the `fable` alias to `claude-fable-5-2`. Check
   with `/status`. If it shows another Fable version, run
   `export ANTHROPIC_DEFAULT_FABLE_MODEL=claude-fable-5-2` before starting `claude`.
3. Install pstack:
   ```text
   /plugin marketplace add cursor/plugins
   /plugin install pstack@cursor-plugins
   ```
4. Run `/pstack:setup-pstack`, choose the `large` budget, and set the roles to:
   ```text
   feature, refactoring: opus xhigh
   bug-fix: opus xhigh
   perf-issue: opus xhigh
   hillclimb: opus xhigh
   judgment and prose: fable xhigh
   arena runners: fable high, opus high
   swarm workers: opus high
   interrogate reviewers: fable high, opus high
   ```
   It writes `~/.claude/rules/pstack-models.md`, which loads in every session. Skip its offers
   to generate verification skills: `verify-step` is this repo's.
5. Set up Codex for reviews. Install and log in to the Codex CLI, then create
   `~/.codex/phillyledger-review.config.toml` with the model and effort reviews should use:
   ```toml
   model = "<the Astra 6.2 id that /model shows in Codex>"
   model_reasoning_effort = "xhigh"
   ```
   The `codex-review` skill runs `codex exec --profile phillyledger-review` in a read-only
   sandbox. Without that file it uses Codex's default model and says so.
6. Install GitHub's stack extension, which owners use to build a step's pull requests as one
   stack (`docs/plans/README.md`):
   ```text
   gh extension install github/gh-stack
   ```
7. Set this clone's commit email to an address that is on your GitHub account, so that commits
   made here show under your account and not as an unlinked name:
   ```text
   git config --local user.email <an email on your GitHub account>
   ```
   Agents never change the git author name or email (hard rule 10 in `CLAUDE.md`).
8. Optional: install `just` (`brew install just`). The `Justfile` wraps the gate commands:
   `just check` for lint, format, types and import contracts, `just test` for pytest,
   `just fix` for ruff's fixes, and `just gates` for everything CI runs. CI calls the
   commands itself and does not need `just`.

## Each build step

Plan:

```text
/pstack:poteto-mode Plan build step N from docs/design.md section 15 with the Multi-phase plan
playbook. Write docs/plans/step-NN.md, commit it, get a Codex review with the codex-review skill,
revise the plan for each finding you confirm, and stop.
```

The run ends with Codex's review of the plan and the revisions it led to. Read the plan. Then
build:

```text
/pstack:poteto-mode Run docs/plans/step-NN.md with the Autopilot-stack playbook. Opus owners
build each pull request. Verify each with the verify-step skill, then get a Codex review with
the codex-review skill and confirm each finding before acting on it. Review every diff yourself
and stop when the pull requests are verified. Do not merge.
```

Those two runs are the full track. A step that qualifies for the light track
(`docs/plans/README.md`) takes one run:

```text
/pstack:poteto-mode Build step N from docs/design.md section 15 on the light track with the
Feature playbook. Write the short plan as the first commit, have one Opus owner build it, verify
it once with the verify-step skill, then get a Codex review with the codex-review skill and
confirm each finding before acting on it. Review the diff yourself and stop when the pull
request is verified. Do not merge.
```

To rerun a Codex review by hand, commit and run `/codex-review plan N` or
`/codex-review pr N <base-branch>`. Reports land in `.codex-review/`, which git ignores.

For a design question the plan leaves open, or a pull request that feels wrong:

```text
/pstack:interrogate
```

Land the pull requests yourself, or tell the session to merge them once they are verified (hard
rule 9 in `CLAUDE.md`). A stack lands from its top pull request, by squash. The repository's
squash default is the pull request title with a blank body, which keeps every line of the branch
commits out of `main`. Then update the step's row in `docs/progress.md` if the run did not.

## Known gaps in Claude Code

- pstack's review panels want one seat from another vendor. In Claude Code that seat runs on
  the session model, so `/pstack:interrogate` panels are Claude only. The Codex reviews of every
  plan and pull request fill that gap, and after steps 6, 13 and 14 Codex reviews the whole
  design against the code.
- `/deslop` comes from Cursor's `cursor-team-kit`, which is not in the Claude Code marketplace.
  This repo ships an adapted copy in `.claude/skills/deslop/`.
