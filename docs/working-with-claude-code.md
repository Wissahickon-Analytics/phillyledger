# Working on this repo with Claude Code

Fable 5.2 plans each step and reads each finished diff once. Opus 5.5 runs each build and writes
the code. Codex reviews each plan, and verifies and reviews each pull request. The workflow and
principles come from pstack. Claude usage is the scarce budget, Fable's most of all, so no long
session runs on Fable (`docs/plans/README.md`, "Why verification is this size").

## One-time setup

1. Clone this repo next to `gov-budget-data`, so `../gov-budget-data` resolves from the repo
   root. Hooks need `python3` and `uv` on the path.
2. Start `claude` in the repo and accept the workspace trust prompt. The project settings set
   the session model to Opus at `xhigh` and pin the `fable` alias to `claude-fable-5-2`. Check
   with `/status`. A Plan run switches the session to Fable with `/model fable`. If `/status`
   then shows another Fable version, run `export ANTHROPIC_DEFAULT_FABLE_MODEL=claude-fable-5-2`
   before starting `claude`.
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
   It writes `~/.claude/rules/pstack-models.md`, which loads in every session. The Build run
   uses `feature` for its owners and `judgment and prose` for the one Fable read. It runs no
   arena and no swarm (`CLAUDE.md`). Skip the offers to generate verification skills:
   `verify-step` is this repo's.
5. Set up Codex. Install and log in to the Codex CLI, then create
   `~/.codex/phillyledger-review.config.toml` with the model and effort reviews should use:
   ```toml
   model = "<the Astra 6.2 id that /model shows in Codex>"
   model_reasoning_effort = "xhigh"
   ```
   The `codex-review` skill runs `codex exec --profile phillyledger-review`. A plan review runs
   in a read-only sandbox. A pull request or fix review runs in a throwaway worktree that the
   script syncs with `uv sync --locked`, in a sandbox that has no network and refused a write
   to the main checkout when tested. Without the profile file it uses Codex's default model and
   says so.
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
8. Install `just` (`brew install just`). The Build session runs `just gates`, the six gates
   that CI runs. The `Justfile` also has `just check` for lint, format, types and import
   contracts, `just test` for pytest, and `just fix` for ruff's fixes. CI calls the commands
   itself and does not need `just`.

## Each build step

Plan, in a session on Fable (`/model fable`):

```text
/pstack:poteto-mode Plan build step N from docs/design.md section 15. Write
docs/plans/step-NN.md in the short format of docs/plans/README.md, commit it, get a Codex review
with the codex-review skill, revise the plan for each finding you confirm, and stop.
```

The run ends with Codex's review of the plan and the revisions it led to. Read the plan. Then
build each pull request in its own new session on Opus, the project default, in the plan's
order:

```text
/pstack:poteto-mode Build pull request <name> of docs/plans/step-NN.md with the Feature
playbook, as CLAUDE.md says. One Opus owner builds it. Run the gates, then one Codex pass with
the codex-review skill, and confirm each finding before acting on it. Give the findings that
block to one fix round and have Codex read the fix diff. Have a Fable delegate read the whole
diff once. Stop when the pull request is verified, and list its follow-ups. Do not merge.
```

A new session for each pull request keeps its context small. One session that carried the five
pull requests of step 2 re-read about half a million tokens on each of its 557 calls.

A step that qualifies for the light track (`docs/plans/README.md`) skips the Plan run:

```text
/pstack:poteto-mode Build step N from docs/design.md section 15 on the light track with the
Feature playbook, as CLAUDE.md says. Write the short plan as the first commit. Then build,
verify and review the pull request as on the full track, but with no Codex read of the fix
diff. Do not merge.
```

To rerun a Codex review by hand, commit and run `/codex-review plan N`,
`/codex-review pr N <base-branch>` or `/codex-review fix N <reviewed-head>`. Reports land in
`.codex-review/`, which git ignores.

A second fix round, or a finding that blocks after the first one, waits for your go. Only a
failed gate, an unproven clause, a broken hard rule or a wrong number can ask for one. For a
design question the plan leaves open, or a pull request that feels wrong:

```text
/pstack:interrogate
```

Land the pull requests yourself, or tell the session to merge them once they are verified (hard
rule 9 in `CLAUDE.md`). A stack lands from its top pull request, by squash. The repository's
squash default is the pull request title with a blank body, which keeps every line of the branch
commits out of `main`. Then update the step's row in `docs/progress.md` if the run did not.

## Known gaps in Claude Code

- pstack's review panels want one seat from another vendor. In Claude Code that seat runs on
  the session model, so `/pstack:interrogate` panels are Claude only. Codex's review of every
  plan and pull request fills that gap, and after steps 6, 13 and 14 Codex reviews the whole
  design against the code.
- `/deslop` comes from Cursor's `cursor-team-kit`, which is not in the Claude Code marketplace.
  This repo ships an adapted copy in `.claude/skills/deslop/`.
