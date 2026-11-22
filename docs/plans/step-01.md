# Build step 1 plan

Build step 1 of `docs/design.md` section 15 creates the uv workspace, its three packages and the
gates that every later step runs. It ships no parser and no data. The work is for the owner, who
lands each pull request, and for the agents that build steps 2 to 14 on these gates. The plan
enforces one rule. Each clause of the step's check belongs to exactly one pull request, and a
named test proves the clause. The pull requests stack in the order S1-A, S1-B, S1-C, S1-D.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `<pstack>/skills/poteto-mode/playbooks/autopilot-stack.md`. `<pstack>` is the
installed pstack plugin folder, the one that holds `skills/` and `docs/`. No agent merges. The
operator lands every pull request, so all four stop at verified.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

This repository's rules add to the playbook, and the repository's rule wins where the two differ
(`CLAUDE.md`, "How work runs here"). The differences are these.

- Verification is the `verify-step` skill. Every swarm lane reads it.
- What a lane drives is a command line and a CI run. A lane saves a transcript as a `.log` file
  in place of a screenshot.
- Each lane runs in its own git worktree on this machine. Claude Code has no cloud agents.
- After the swarm, Codex reviews each pull request with the `codex-review` skill, and the root
  confirms or drops each finding. This repository has no Bugbot.
- "Trunk" is `main` for S1-A. For a stacked child, the base that a lane compares against is the
  head of the parent pull request.

Each clause of the step 1 check has one owner.

| Clause | Text in design section 15 | Owner | Named proof |
|---|---|---|---|
| C1 | CI is green | S1-A | the `CI` run at the head, and `test_ci_runs_every_gate` |
| C2 | a planted `import boto3` in `datadesk.core` fails CI | S1-B | `test_planted_boto3_import_fails_lint_imports` |
| C3 | a planted `bool` parameter in `checkedtables` fails CI | S1-C | `test_planted_bool_parameter_fails_shape_test` |
| C4 | a planted socket call in a core test fails CI | S1-D | `test_planted_socket_call_fails_pytest` |

A planted test proves that one gate fails on the plant. `test_ci_runs_every_gate` proves that CI
runs that gate on every pull request and cannot ignore its failure. One live lane per clause then
shows a real `pull_request` run fail on the plant.

Three pull requests change `docs/design.md`. Each change is also an entry under Deviations in
`docs/progress.md`, in the same pull request. The owner kept all four on November 22, 2026.

- S1-B replaces the "Not verified" note on standard-library modules in sections 12.5 and 17.4.
- S1-B adds the 20 table modules to the contract "family helpers do not import table modules" in
  section 12.5. As the design gives it, the contract forbids only `catalog`.
- S1-C makes the `bool` assertion in section 11.4 also fail on `bool | None` and
  `Optional[bool]`.
- S1-D adds `builtins` and mutable module state to the purity row of section 11.1.

## Program checklist

### Arm the program

The evidence for each box in this section is a row in the decision trail.

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on the operator's explicit go.
- [ ] Confirm the operator's preconditions before any owner starts. Agents never push to `main` (`CLAUDE.md`, hard rule 9).
  - [ ] `git rev-parse --abbrev-ref HEAD` prints `main`, and `git status --porcelain` prints nothing.
  - [ ] `git ls-remote origin main` prints the SHA that `git rev-parse main` prints.
  - [ ] `gh repo view --json nameWithOwner,defaultBranchRef` names the repository and `main`.
  - [ ] `git show origin/main:docs/plans/step-01.md` prints this plan, with the revisions of Appendix E.
  - [ ] `gh auth status` lists the `repo` and `workflow` scopes. The command masks the token. S1-A pushes a workflow file, which needs the `workflow` scope.
  - [ ] The operator confirms that the repository's GitHub Actions allowance covers the run. The plan opens seven temporary PRs, which start 14 jobs, and every push to one of the four PR branches starts two more.
- [ ] Start the decision trail at `.audit/step-01.tsv` per `<pstack>/skills/show-me-your-work/SKILL.md`.
- [ ] Save the reference snapshot as `<root>/.audit/reference-baseline.txt`, where `<root>` is the absolute path of the root's checkout. The snapshot is the output of the commands below this list. Give every lane both absolute paths.
- [ ] Read these from trunk at program start. Re-read them at every tick.
  - [ ] `git show origin/main:CLAUDE.md`
  - [ ] `git show origin/main:docs/plans/step-01.md`
  - [ ] `git show origin/main:.claude/skills/verify-step/SKILL.md`
  - [ ] `git show origin/main:.claude/skills/codex-review/SKILL.md`
  - [ ] `git show origin/main:.claude/skills/deslop/SKILL.md`
- [ ] Read these from the installed pstack plugin. They are not in this repository.
  - [ ] `<pstack>/docs/harness/claude-code.md`
  - [ ] `<pstack>/skills/poteto-mode/playbooks/autopilot-stack.md` and `autopilot-full.md`
  - [ ] `<pstack>/skills/poteto-mode/playbooks/opening-a-pr.md` and `shipping.md`
  - [ ] `<pstack>/skills/swarm/SKILL.md` and `<pstack>/skills/no-comments/SKILL.md`
- [ ] On the operator's go, arm the audit tick as `/loop 1h` with the tick prompt below. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read `<pstack>/skills/poteto-mode/playbooks/autopilot-stack.md`, and re-read `docs/plans/step-01.md` and `CLAUDE.md` from trunk. Audit the operation against them and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then post a short status message to the operator in chat only when the audit found a tracked change that no earlier status message reported, such as a PR opened, a code-ready head, a round launched or closed, a verdict, a stuck agent and the action taken, a blocker added or cleared, or a decision only the operator can make. Name every such change and nothing else. Do not repeat a table or an unchanged blocker. If the audit found none, end the turn with no reply text. Either way, log this tick's row in your decision trail. The row names the items reported, or none."
- [ ] On the operator's hold or stand-down, send every owner a zero-writes order at once.

The reference snapshot reads `../gov-budget-data` and never writes to it. A plain `git status`
can rewrite the index of the checkout it reads, so every command carries `--no-optional-locks`.
`<reference>` is the absolute path of `../gov-budget-data`.

```sh
git --no-optional-locks -C <reference> rev-parse HEAD
git --no-optional-locks -C <reference> status --porcelain
git --no-optional-locks -C <reference> diff | shasum -a 256
git --no-optional-locks -C <reference> diff --cached | shasum -a 256
git --no-optional-locks -C <reference> ls-files --others --exclude-standard -z |
    xargs -0 -I{} shasum -a 256 "<reference>/{}"
```

Step 1 needs no R2 and no Textract credentials.

### Spawn owners

- [ ] Spawn one owner per PR with the lifecycle that `autopilot-full.md` step 2 names, without the merge. Each owner is a fresh `pstack:poteto-agent` on the `feature, refactoring` line of `~/.claude/rules/pstack-models.md`, in its own git worktree.
- [ ] Write each owner a brief that stands alone.
  - [ ] It restates the user's goal in one sentence.
  - [ ] It names the PR's section of this plan by heading, and gives the absolute path of `<pstack>/skills/poteto-mode/SKILL.md`.
  - [ ] It lists the rules that bind the owner. Write the tests first and commit them failing. Never weaken a check. Never write under `../gov-budget-data`. Never push to `main`. Never merge.
- [ ] Follow this dependency graph. Each child is based on its parent's branch, because each child edits files that its parent created.
  - [ ] S1-A is first. It branches from `main` as `step-01/a-workspace`.
  - [ ] S1-B after S1-A, as `step-01/b-import-contracts`.
  - [ ] S1-C after S1-B, as `step-01/c-kit-shape`.
  - [ ] S1-D after S1-C, as `step-01/d-test-isolation`.
- [ ] Start a child only after its parent reports a code-ready head.
- [ ] Hold the file boundaries.
  - [ ] S1-A touches only `pyproject.toml`, `uv.lock`, `.python-version`, `prek.toml`, `.gitignore`, `.github/workflows/ci.yml`, `packages/*/pyproject.toml`, the five `__init__.py` files, `tests/test_gates.py` and `tests/test_workspace.py`.
  - [ ] S1-B touches only `pyproject.toml`, `uv.lock`, `.gitignore`, `.github/workflows/ci.yml`, `tests/test_gates.py`, the 46 new empty modules under `packages/*/src/`, and sections 12.5 and 17.4 of `docs/design.md`.
  - [ ] S1-C touches only `pyproject.toml`, `.github/workflows/ci.yml`, `tests/test_gates.py`, `packages/checkedtables/tests/test_library_shape.py`, and section 11.4 of `docs/design.md`.
  - [ ] S1-D touches only `pyproject.toml`, `uv.lock`, the root `conftest.py`, `tests/test_gates.py`, `tests/test_purity.py`, the `conftest.py` and `test_isolation.py` files in `packages/checkedtables/tests/` and `packages/datadesk/tests/core/`, and section 11.1 of `docs/design.md`.
  - [ ] Every PR may also edit `docs/progress.md`. A PR edits `docs/plans/step-01.md` when the build shows this plan wrong.
  - [ ] No PR touches `docs/prototype/`, `.claude/`, `CLAUDE.md` or anything under `../gov-budget-data`.
- [ ] Hold the review gate. No PR in this plan changes an interaction, so none is review-gated. Every PR still stops at verified and waits for the operator to land it.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Run `command -v origin`. When it fails, use `gh` for every PR operation and record the fallback. Never require `gt`.
- [ ] Open the PR ready, never draft, with `gh pr create --base <base-branch>`. S1-A targets `main`. A stack child targets its parent branch. Write the title as `type(scope): subject`.
- [ ] Write the PR body per `opening-a-pr.md`. Open `## Why` with the user's goal. Put the Codex summary under `## Verification`. From S1-C on, also put the line that the `Kit size report` step prints there.
- [ ] Run the repo's lint and typecheck once before the PR-facing push, with every gate that exists at that head. Push with hooks on.
- [ ] Run `/deslop` from `.claude/skills/deslop/` before each commit and `/no-comments` before review.
- [ ] Rebase before the code-ready report. S1-A rebases onto current `main`. A child rebases onto the tip of its parent branch. Keep that merge base in fix rounds. Rebase again only on a `git merge-tree` conflict with the base, on a CI failure that comes from the base, or when the parent gets a new head.
- [ ] Report the code-ready head SHA to the root, then every later head.

This repository has no Bugbot. The Codex review in the next section takes its place.

### Verdict and merge, for every PR

- [ ] A full swarm runs once, at the code-ready head. Another full swarm runs only for new behavior, a redesign, or a large new diff. A rebase, a merge-conflict resolution, or a minor fix gets a single verifier at the new head, and a wording-only change gets none. Run each full swarm per `<pstack>/skills/swarm/SKILL.md`, with `general-purpose` workers in their own worktrees on the `swarm workers` line of `~/.claude/rules/pstack-models.md`.
  - [ ] One gates lane runs the Gates section of `verify-step`.
  - [ ] The ten live lanes come from the PR's live block.
  - [ ] The perf lane comes from the PR's perf block.
  - [ ] Audit lane 1 runs the check section of `verify-step` for the clause this PR owns. It breaks the guarded code in a scratch copy and shows the named test fail.
  - [ ] Audit lane 2 runs audits 1 to 7 of `verify-step` on the diff and distrusts the PR body. For audit 7 it runs the reference snapshot commands and compares the output with `<root>/.audit/reference-baseline.txt`. It reports a difference to the operator and changes nothing in the reference.
  - [ ] Every lane reports `PASS`, `ISSUES` or `BLOCKED`, with the head SHA and its transcript paths.
- [ ] The root audits the receipts in the merge-ready report before the verdict.
- [ ] Judge every finding by the blocking rule in `autopilot-full.md` step 4. The verdict is clean when none blocks. A failure on base behavior in a lane marked `Regression lane against trunk.` is recorded against the base and does not block the PR. A new head gets a fresh verdict, except for results that stay valid under the patch-id rule in `shipping.md`.
- [ ] After a clean swarm verdict, run the Codex review. Run `.claude/skills/codex-review/run.sh pr 1 <base-branch>` in the background on the committed head. Confirm or drop each finding by a rerun of its command or a read of its quoted lines. Give each kept `blocks` or `should fix` finding to a fresh owner with the finding, its evidence and the original brief. Then run one `verify-step` verifier and the Codex review on the new head.
- [ ] The root reads the whole diff and writes its own summary. It does not pass through an owner's report.
- [ ] Stop at verified. Report each PR with its verdict and its head SHA. After the handoff, nobody pushes without the operator's go. The operator lands the stack bottom-up. When a parent lands, its child moves onto `main` per `shipping.md` step 4, and the child's verdict stands when `git patch-id` is unchanged.

### Boot recipe, for every live lane

Each live lane runs in its own git worktree on this machine at the PR head. Claude Code has no
`control-cli` skill, so a lane drives the command line with shell commands and saves the
transcript.

- [ ] `git fetch origin <head-branch> && git checkout <head SHA>`.
- [ ] Run `uv sync --locked` and wait for exit code 0.
- [ ] Deliver input only as the shell commands that the lane names. The read-only diagnostics are `git status`, `uv tree`, `uv run python -V` and `gh run view`.
- [ ] For a plant, edit the file that the lane names, in the lane's own worktree. Never commit a plant to the PR branch.
- [ ] Never run `prek install` in a worktree. Linked worktrees share one hooks folder, so the hook would reach every other lane and the operator's checkout.
- [ ] For a lane that opens a temporary PR, cut `verify/<pr-id>-lane-<n>` from the head SHA, commit the plant there, and push the branch. Run `gh pr create --base <head-branch>` with the title `verify <pr-id> lane <n>` and a body that says the PR is a throwaway and must not be merged.
- [ ] Wait for the temporary PR with `gh pr checks <number> --watch`. Save the run ID, the SHA, the event name, the conclusion and the output of `gh run view <run-id> --log-failed`. Then run `gh pr close <number> --delete-branch`.
- [ ] Save every transcript to `/tmp/swarm-<pr-id>/worker-<n>/<slug>.log` and return the paths with the report.

## Stand up the workspace, the base gates and CI (S1-A)

**Depends on.** None. S1-A branches from `main`. It owns clause C1.

**Files.**

- [ ] Create `pyproject.toml`, `uv.lock`, `.python-version` and `prek.toml` at the repository root.
- [ ] Create `packages/checkedtables/pyproject.toml` and `packages/checkedtables/src/checkedtables/__init__.py`.
- [ ] Create `packages/phillyledger/pyproject.toml` and `packages/phillyledger/src/phillyledger/__init__.py`.
- [ ] Create `packages/datadesk/pyproject.toml` and, under `packages/datadesk/src/datadesk/`, the files `__init__.py`, `core/__init__.py` and `shell/__init__.py`.
- [ ] Create `tests/test_gates.py` and `tests/test_workspace.py`.
- [ ] Create `.github/workflows/ci.yml`.
- [ ] Edit `.gitignore` and `docs/progress.md`.

**Build.**

- [ ] Write the root `pyproject.toml` as a virtual workspace. `[tool.uv.workspace]` has `members = ["packages/*"]`, and `[tool.uv.sources]` marks the three members `{ workspace = true }`. The file has no `[project]` table.
- [ ] Add the `dev` dependency group. It lists `checkedtables`, `phillyledger`, `datadesk`, `prek==0.5.10`, `pytest>=9`, `ruff>=0.17` and `ty==0.0.104`.
- [ ] Write each member's `pyproject.toml` with its name, `version = "0.0.0"`, `requires-python = ">=3.12"`, no dependencies, and the build backend `uv_build` with `requires = ["uv_build>=0.13.6,<0.14.0"]`.
- [ ] Create the five `__init__.py` files empty.
- [ ] Run `uv python pin 3.12`, then `uv lock`. Commit `.python-version` and `uv.lock`.
- [ ] Configure ruff in the root `pyproject.toml`. Use `line-length = 100`, `target-version = "py312"`, the three `packages/*/src` folders as `src`, and `extend-exclude = ["docs/prototype", ".claude"]`.
- [ ] Set the ruff rules. `select` is the old repo's list with `ANN` and `PYI` added (`../gov-budget-data/pyproject.toml`, `[tool.ruff.lint]`). `ignore` is `ANN401`, `D100` and `D104`. The pydocstyle convention is `numpy`.
- [ ] Scope the `D` rules with two `per-file-ignores` entries, `"!packages/{checkedtables,phillyledger}/src/**" = ["D"]` and `"**/tests/**" = ["ANN", "D"]`.
- [ ] Configure pytest with `testpaths = ["tests"]` and `addopts = "--import-mode=importlib"`.
- [ ] Configure ty with `python-version = "3.12"`, the three `src` folders as `root`, and `exclude = ["docs/prototype", ".claude"]` under `[tool.ty.src]`.
- [ ] Write `prek.toml` with the three local hooks of `../gov-budget-data/prek.toml`. They run `uv run ruff check --fix --force-exclude`, `uv run ruff format --force-exclude`, and `uv run ty check` with `pass_filenames = false`.
- [ ] Write `GATES` in `tests/test_gates.py`. It is a tuple of the five commands that CI runs, `uv run ruff check .`, `uv run ruff format --check .`, `uv run ty check`, `uv run prek run --all-files` and `uv run pytest`.
- [ ] Write `test_ci_runs_every_gate` in `tests/test_gates.py`. It reads `.github/workflows/ci.yml` and fails, with the reason in the message, unless four things hold. The text holds the line `run: <gate>` for every member of `GATES`. The text holds `pull_request`. The text holds neither `continue-on-error` nor `github.event_name`. Every `if` in the text is `${{ !cancelled() }}`.
- [ ] Write `test_workspace_packages_import` in `tests/test_workspace.py`. It imports `checkedtables`, `phillyledger`, `datadesk.core` and `datadesk.shell`.
- [ ] Write `.github/workflows/ci.yml` with one job named `gates`. It runs on `pull_request` and on a push to `main`. The matrix is Python 3.12 and 3.14. Pin `actions/checkout` and `astral-sh/setup-uv` to the commit SHAs in `../gov-budget-data/.github/workflows/ci.yml`, and pass `python-version: ${{ matrix.python-version }}` to `setup-uv`.
- [ ] Give the `gates` job the step `uv sync --locked`, then a step named `Python version`. That step prints the major and minor version of `uv run python` and fails unless the version equals the matrix value.
- [ ] Add one step per member of `GATES`. Give each gate step `if: ${{ !cancelled() }}`, so one failed gate does not hide the others.
- [ ] Add `.audit/` to `.gitignore`.
- [ ] Set the step 1 row of `docs/progress.md` to `in progress` with the branch name.

**You see.**

- [ ] `uv sync --locked` exits 0, and `uv run python -c "import checkedtables, phillyledger, datadesk.core, datadesk.shell"` prints nothing.
- [ ] `uv run ruff check .` and `uv run ty check` each print `All checks passed!`.
- [ ] `uv run prek run --all-files` prints `Passed` for `ruff check`, `ruff format` and `ty check`.
- [ ] `uv run pytest` ends with `2 passed`.
- [ ] The `CI` run for the PR head shows two green `gates` jobs. One prints `3.12` in its `Python version` step and the other prints `3.14`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_gates.py` gains `test_ci_runs_every_gate`. Run `uv run pytest tests/test_gates.py`.
  - [ ] Delete the `uv run ty check` step in a scratch copy of `ci.yml`. The test fails and names that gate.
  - [ ] Add `continue-on-error: true` to one gate step in a scratch copy of `ci.yml`. The test fails.
- [ ] `tests/test_workspace.py` gains `test_workspace_packages_import`. Run `uv run pytest tests/test_workspace.py`.
- [ ] The branch log shows both tests committed before the packages and `ci.yml`, and failing at that commit.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus high` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `uv sync --locked` and the five gates at `main` and at the head. `main` has no workspace, so record that `uv sync` fails there, and gate the head. Save `gates-clean.log`. Pass when the `main` failure is recorded and every gate exits 0 at the head with `2 passed`.
- [ ] Lane 2. Read the real `pull_request` run for the head SHA with `gh run list --commit <head SHA>` and `gh run view`. Save `ci-green.log`. Pass when the run concludes `success`, every gate step is green in both `gates` jobs, and the two `Python version` steps print `3.12` and `3.14`.
- [ ] Lane 3. Open a temporary PR from `verify/s1-a-lane-3` with `import json` appended to `packages/datadesk/src/datadesk/shell/__init__.py`. Save `ci-ruff-check.log`. Pass when the `pull_request` run fails, the `uv run ruff check .` step reports `F401`, and the `uv run pytest` step still ran.
- [ ] Lane 4. Open a temporary PR from `verify/s1-a-lane-4` with the line `x  =  1` appended to the same file. Save `ci-ruff-format.log`. Pass when the `pull_request` run fails and the `uv run ruff format --check .` step reports that the file would be reformatted.
- [ ] Lane 5. Open a temporary PR from `verify/s1-a-lane-5` with the line `X: int = "a"` appended to the same file. Save `ci-ty.log`. Pass when the `pull_request` run fails and the `uv run ty check` step reports `invalid-assignment`.
- [ ] Lane 6. Open a temporary PR from `verify/s1-a-lane-6` with a new `tests/test_planted_failure.py` whose one test asserts `1 == 2`. Save `ci-pytest.log`. Pass when the `pull_request` run fails and the `uv run pytest` step reports `1 failed`.
- [ ] Lane 7. Clone the repository into a new folder with `git clone`, check out the head SHA there, and run `uv sync --locked` and `uv run prek install`. Append `x  =  1` to a tracked Python file, stage it, and run `git commit`. Save `prek-hook.log`. Pass when `git commit` exits non-zero, the `ruff format` hook reports a changed file, `git log -1` still shows the head SHA, and the hooks folder of the root's checkout is unchanged.
- [ ] Lane 8. Run `uv build --all-packages --out-dir dist` and list each wheel with `unzip -l`. Save `build.log`. Pass when three wheels and three source archives exist, each wheel holds its package's `__init__.py`, and no wheel holds a `tests/` path.
- [ ] Lane 9. Add `"httpx"` to `dependencies` in `packages/datadesk/pyproject.toml` without a relock, and run `uv sync --locked`. Save `stale-lock.log`. Pass when the command exits non-zero and reports that the lockfile needs an update.
- [ ] Lane 10. Add an undocumented `def planted() -> None: ...` to `checkedtables/__init__.py` and run `uv run ruff check .`. Move the function to `datadesk/core/__init__.py` and run the command again. Save `docstring-scope.log`. Pass when the first run reports `D103` and the second reports no `D` rule.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Warm wall time in seconds of the five gates, run in sequence in a synced worktree. `main` has no workspace and cannot produce the metric, so the work this diff adds is the whole gate run.
- [ ] Probe. Record `uptime`, run the sequence once as a warm-up, then time it five times with `time -p`. Every command must exit 0, and pytest must print `2 passed`.
- [ ] Baseline. Record the `main` result first, which is the `uv sync` failure.
- [ ] Rule. The head fails when its median is 5.0 s or more.

**Review gate.** None. S1-A is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Every Codex finding is confirmed or dropped, and the summary is in the PR's `## Verification` section.
- [ ] Rebased onto current `main` after the verdict, patch-id unchanged.
- [ ] The root reports S1-A as verified, with its head SHA. The operator lands it.

## Enforce the import contracts (S1-B)

**Depends on.** S1-A. The base is `step-01/a-workspace`. S1-B owns clause C2.

**Files.**

- [ ] Edit `pyproject.toml`, `uv.lock`, `.gitignore`, `.github/workflows/ci.yml` and `tests/test_gates.py`.
- [ ] Create `checks/__init__.py` and 13 empty modules in `packages/checkedtables/src/checkedtables/`. The modules are `assemble.py`, `columns.py`, `grammar.py`, `lex.py`, `lines.py`, `pages.py`, `pipeline.py`, `records.py`, `rows.py`, `suggest.py`, `testing.py`, `text.py` and `words.py`.
- [ ] Create `_shell/__init__.py` and five empty modules in `packages/phillyledger/src/phillyledger/`. The modules are `api.py`, `lineage.py`, `manifest.py`, `pin.py` and `plan.py`.
- [ ] Create `tables/__init__.py` and 25 empty modules in `packages/datadesk/src/datadesk/core/tables/`. They are the 20 table modules of the independence contract, the four `*_common.py` modules, and `catalog.py`.
- [ ] Edit `docs/design.md` sections 12.5 and 17.4, and `docs/progress.md`.

**Build.**

- [ ] Add `import-linter>=2.16` to the `dev` group and run `uv lock`.
- [ ] In design section 12.5, add the 20 table modules of the independence contract to `forbidden_modules` of the contract "family helpers do not import table modules". As the design gives it, the contract forbids only `datadesk.core.tables.catalog`, so a helper can import a table module directly (Appendix A). Record the change under Deviations in `docs/progress.md`.
- [ ] Copy the TOML block of design section 12.5, as it reads after that change, into `pyproject.toml` word for word. The evidence is an empty `diff` between the two blocks at the PR head.
- [ ] Create the 46 empty files that the contracts name. import-linter refuses a contract that names a module that does not exist (Appendix A). The evidence is that `git ls-files 'packages/*/src/*.py' | wc -l` prints 51 and every one of those files has size 0.
- [ ] Add `TID251` to the ruff `select` list, and add the `banned-api` table with `datetime.datetime.now`, `datetime.date.today` and `tomllib.load`.
- [ ] Scope the ban with one `per-file-ignores` entry, `"!packages/{checkedtables/src/checkedtables,datadesk/src/datadesk/core}/**" = ["TID251"]`.
- [ ] Add `uv run lint-imports` to `GATES` in `tests/test_gates.py`, and add the step `run: uv run lint-imports` to `ci.yml` with the same `if` as the other gates.
- [ ] Write `run_gate(workspace, plants, gate, extra)` in `tests/test_gates.py`. It copies `packages/` and `pyproject.toml` into `workspace`, appends each plant to its file, and runs the gate with the copy as the working directory. `extra` holds the arguments that follow the gate's own.
- [ ] Make `run_gate` take a member of `GATES`, drop the `uv run` prefix, and run that executable from the folder of `sys.executable`. It sets `PYTHONPATH` to the three `src` folders of the copy, so the gate reads the copy and not the installed packages.
- [ ] Write `clean_then_planted(tmp_path, clean, planted, gate, extra)` in `tests/test_gates.py`. It runs the gate on a clean copy, asserts exit code 0, then returns the result of the planted copy.
- [ ] Write `test_planted_boto3_import_fails_lint_imports`. It plants `import boto3` at the end of `packages/datadesk/src/datadesk/core/__init__.py`, runs the `uv run lint-imports` gate with `--no-cache`, and asserts a non-zero exit code and the text `datadesk core is pure BROKEN`.
- [ ] Add `.import_linter_cache/` to `.gitignore`.
- [ ] Replace the "Not verified" note on standard-library modules in design sections 12.5 and 17.4 with the observed result. import-linter 2.16 treats `os`, `pathlib`, `logging` and `time` as external packages and fails the contract.
- [ ] Add a note to `docs/progress.md`. The 46 empty modules exist because import-linter refuses a contract that names a missing module, and later steps fill them.

**You see.**

- [ ] `uv run lint-imports` ends with `Contracts: 8 kept, 0 broken.`
- [ ] With `import boto3` appended to `packages/datadesk/src/datadesk/core/__init__.py`, the same command exits 1 and prints `datadesk core is pure BROKEN` and `Contracts: 7 kept, 1 broken.`
- [ ] `uv run pytest` ends with `3 passed`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_gates.py` gains `test_planted_boto3_import_fails_lint_imports`. Run `uv run pytest tests/test_gates.py::test_planted_boto3_import_fails_lint_imports`.
  - [ ] In a scratch copy, delete the contract named `datadesk core is pure`. The test fails.
  - [ ] In a scratch copy, drop `PYTHONPATH` from `run_gate`. The test fails, because the gate then reads the installed packages.
- [ ] `test_ci_runs_every_gate` now covers `uv run lint-imports`. In a scratch copy, delete that step from `ci.yml`. The test fails.
- [ ] The branch log shows the planted test committed before the contracts, and failing at that commit.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus high` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run the gates at the base, which is the S1-A head, and at the head. Record that `uv run lint-imports` does not exist at the base. Save `gates-clean.log`. Pass when the five S1-A gates exit 0 on both sides and `uv run lint-imports` prints `Contracts: 8 kept, 0 broken.` at the head.
- [ ] Lane 2. Open a temporary PR from `verify/s1-b-lane-2` with `import boto3` appended to `packages/datadesk/src/datadesk/core/__init__.py`. Save `ci-boto3.log`. Pass when the `pull_request` run fails and the `uv run lint-imports` step fails with `datadesk core is pure BROKEN`.
- [ ] Lane 3. Append `import os`, `from pathlib import Path`, `import logging` and `import time` to the same file, one at a time, and run `uv run lint-imports` after each. Save `stdlib-plants.log`. Pass when each run exits 1 with `datadesk core is pure BROKEN`.
- [ ] Lane 4. Append `import datadesk` to `checkedtables/words.py`, then separately `import pytest` to `checkedtables/testing.py`, and run `uv run lint-imports` after each. Save `kit-contract.log`. Pass when each run exits 1 with `checkedtables holds no I/O and no Philadelphia BROKEN`.
- [ ] Lane 5. Append `from checkedtables import words` to `checkedtables/checks/__init__.py` and run `uv run lint-imports`. Save `arithmetic-contract.log`. Pass when the run exits 1 with `arithmetic never sees words BROKEN`.
- [ ] Lane 6. Append `import datadesk` to `phillyledger/api.py`, then separately `from phillyledger import api` to `phillyledger/manifest.py`, and run `uv run lint-imports` after each. Save `reader-contracts.log`. Pass when the first run breaks `the reader stands alone` and the second breaks `the reader's core is pure`.
- [ ] Lane 7. Append `import datadesk.shell` to `datadesk/core/__init__.py`, then separately `import boto3` to `datadesk/shell/__init__.py`, and run `uv run lint-imports` after each. Save `layers.log`. Pass when the first run breaks `shell over core` and the second prints `Contracts: 8 kept, 0 broken.`
- [ ] Lane 8. Append `from datadesk.core.tables import birt` to `datadesk/core/tables/sales.py`. Then, one at a time, append the same import and `from datadesk.core.tables import catalog` to `datadesk/core/tables/qcmr_common.py`. Run `uv run lint-imports` after each. Save `table-contracts.log`. Pass when the first run breaks `table modules do not import each other` and the other two break `family helpers do not import table modules`.
- [ ] Lane 9. Delete `packages/checkedtables/src/checkedtables/lex.py` and run `uv run lint-imports`. Save `missing-module.log`. Pass when the run exits 1 with `Module 'checkedtables.lex' does not exist.`
- [ ] Lane 10. Write the probe below this list to `datadesk/core/tables/birt.py` and run `uv run ruff check .`. Move the same source to a new `datadesk/shell/probe.py` and run the command again. Save `banned-api.log`. Pass when the first run reports `TID251` three times, for `datetime.now`, `date.today` and `tomllib.load`, and the second run reports no `TID251`.

```python
import tomllib
from datetime import date, datetime

datetime.now()
date.today()
with open("x", "rb") as handle:
    tomllib.load(handle)
tomllib.loads("")
```

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Warm wall time in seconds of the gate sequence, five gates at the base and six at the head. Both sides produce it.
- [ ] Probe. Record `uptime`, warm each side once, then time the sequence five times per side with `time -p`, alternating base and head, each in its own synced worktree. Every command must exit 0, and pytest must print its pass count.
- [ ] Baseline. Record the base median first.
- [ ] Rule. The head fails when its median exceeds the base median by more than 3.0 s, or when its median is 20.0 s or more.

**Review gate.** None. S1-B is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Every Codex finding is confirmed or dropped, and the summary is in the PR's `## Verification` section.
- [ ] Rebased onto the tip of `step-01/a-workspace` after the verdict, patch-id unchanged.
- [ ] The root reports S1-B as verified, with its head SHA. The operator lands it after S1-A.

## Pin the kit's shape (S1-C)

**Depends on.** S1-B. The base is `step-01/b-import-contracts`. S1-C owns clause C3.

**Files.**

- [ ] Create `packages/checkedtables/tests/test_library_shape.py`.
- [ ] Edit `pyproject.toml`, `.github/workflows/ci.yml` and `tests/test_gates.py`.
- [ ] Edit `docs/design.md` section 11.4, and `docs/progress.md`.

**Build.**

- [ ] Write `public_functions(module)` in `packages/checkedtables/tests/test_library_shape.py`. It takes a package or a plain module. For a package it also imports every submodule that `pkgutil.walk_packages` finds, and it skips a dotted name when any part starts with `_`.
- [ ] Make `public_functions` yield every public function that a module defines, and every public method of every public class that a module defines, class methods and static methods included. A name is public when it does not start with `_`. A module defines an object when the object's `__module__` is the module's name.
- [ ] Type the return value of `public_functions` as `Iterator[types.FunctionType]`. With `Callable[..., object]`, `uv run ty check` rejects `fn.__qualname__` (Appendix A).
- [ ] Write `bool_parameters(fn)` in the same file. It returns the names of the parameters whose annotation is `bool` or is a union with `bool` as a member, so `bool | None` and `Optional[bool]` count. It reads string annotations through `inspect.signature(fn, eval_str=True)`. A `bool` inside another type, such as `tuple[bool, ...]`, does not count.
- [ ] Write `test_no_bool_parameters_and_at_most_four` as design section 11.4 gives it, with `bool_parameters(fn)` as the `bool` assertion. For a method, do not count the bound first parameter.
- [ ] Run the same test over the four family helpers, `qcmr_common`, `collections_common`, `bib_common` and `supp_common` in `datadesk.core.tables`. Design section 11.4 says these modules run the first test too. Name them in a tuple `FAMILY_HELPERS`.
- [ ] Change the `bool` assertion in the code block of design section 11.4 to match `bool_parameters`, and record the change under Deviations in `docs/progress.md`. The design's predicate passes `flag: bool | None`, which `CLAUDE.md` hard rule 5 bans.
- [ ] Write `test_bool_parameters_reads_each_spelling`. It checks `flag: bool`, `flag: bool | None`, `flag: Optional[bool]`, a keyword-only `flag: bool = False`, and the first two again as string annotations. It also checks that `flags: tuple[bool, ...]` and `count: int | None` give no name.
- [ ] Write `kit_dataclasses()`, `field_names(cls)` and `FIELD_SNAPSHOT = {}`, then `test_kit_dataclass_fields_are_pinned` as the design gives it.
- [ ] Write `bool_fields(classes)` and `test_bool_fields_are_page_facts_only`. At this step the expected value is `set()`. The design's two members arrive in the pull requests that create `Word` and `Column`.
- [ ] Write `source_lines(package)`, `public_names(package)` and `report_budget()`. `source_lines` counts the lines of the package's `.py` files that are neither blank nor comments. `public_names` returns the names in the package's namespace that do not start with `_` and are not modules.
- [ ] Call `report_budget()` under `if __name__ == "__main__"`. At this step it prints `checkedtables: 0 lines (budget 3,800), 0 public names (budget 140)`.
- [ ] Leave `test_closed_lists_are_pinned` out, because none of its lists exists yet. Record in `docs/progress.md` that each list's pin lands in the pull request that creates the list (`CLAUDE.md`, hard rule 6).
- [ ] Add `packages/checkedtables/tests` to `testpaths` in `pyproject.toml`.
- [ ] Add `test_planted_bool_parameter_fails_shape_test` to `tests/test_gates.py`. It plants `def planted(flag: bool) -> None: ...` at the end of `packages/checkedtables/src/checkedtables/__init__.py`. It runs the `uv run pytest` gate with the extra arguments `-p no:cacheprovider` and the path of the shape test file, and asserts exit code 1 and the text `AssertionError: planted`.
- [ ] Add `test_planted_family_helper_parameter_fails_shape_test` to `tests/test_gates.py`. It plants the same function at the end of `packages/datadesk/src/datadesk/core/tables/qcmr_common.py` and makes the same assertions.
- [ ] Add a CI step named `Kit size report` that runs `uv run python packages/checkedtables/tests/test_library_shape.py`. Keep it out of `GATES`, because the report never fails the build (design section 18.2).

**You see.**

- [ ] `uv run pytest packages/checkedtables/tests` ends with `4 passed`.
- [ ] `uv run python packages/checkedtables/tests/test_library_shape.py` prints `checkedtables: 0 lines (budget 3,800), 0 public names (budget 140)`.
- [ ] `uv run pytest` ends with `9 passed`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `packages/checkedtables/tests/test_library_shape.py` gains `test_no_bool_parameters_and_at_most_four`, `test_bool_parameters_reads_each_spelling`, `test_kit_dataclass_fields_are_pinned` and `test_bool_fields_are_page_facts_only`. Run `uv run pytest packages/checkedtables/tests/test_library_shape.py`.
- [ ] `tests/test_gates.py` gains `test_planted_bool_parameter_fails_shape_test` and `test_planted_family_helper_parameter_fails_shape_test`. Run `uv run pytest tests/test_gates.py -k shape_test`.
  - [ ] In a scratch copy, delete the `bool` assertion from `test_no_bool_parameters_and_at_most_four`. Both planted tests fail.
  - [ ] In a scratch copy, remove `FAMILY_HELPERS` from the test. The family helper planted test fails.
- [ ] The branch log shows the planted tests committed before the shape test, and failing at that commit.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus high` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run the six gates at the base, which is the S1-B head, and at the head. Record that the base has no shape test. Save `gates-clean.log`. Pass when every gate exits 0 on both sides and the head prints `9 passed`.
- [ ] Lane 2. Open a temporary PR from `verify/s1-c-lane-2` with `def planted(flag: bool) -> None: ...` appended to `packages/checkedtables/src/checkedtables/__init__.py`. Save `ci-bool.log`. Pass when the `pull_request` run fails and the `uv run pytest` step fails with `AssertionError: planted`.
- [ ] Lane 3. Put `from __future__ import annotations` and `def planted(flag: bool) -> None: ...` in `checkedtables/words.py` and run the shape test. Save `submodule-string-annotation.log`. Pass when the test fails and names `planted`.
- [ ] Lane 4. Plant `def planted(flag: bool | None) -> None: ...` in `checkedtables/lex.py` and run the shape test. Replace the annotation with `Optional[bool]`, then put `from __future__ import annotations` above each form, and run the test after every change. Save `optional-bool.log`. Pass when all four runs fail and name `planted`.
- [ ] Lane 5. Plant a public function with five `int` parameters in `checkedtables/text.py` and run the shape test. Remove one parameter and run it again. Save `parameter-count.log`. Pass when the first run fails and names the function, and the second run passes.
- [ ] Lane 6. Plant, one at a time, `def _helper(flag: bool) -> None: ...`, `def planted(flags: tuple[bool, ...]) -> None: ...` and `def planted(count: int | None) -> None: ...` in `checkedtables/rows.py`, and run the shape test after each. Save `passing-controls.log`. Pass when all three runs pass.
- [ ] Lane 7. Plant a public class `Planted` with a class method `of(cls, flag: bool)` in `checkedtables/pages.py` and run the shape test. Replace the method with `def of(self, a: int, b: int, c: int, d: int)` and run it again. Save `methods.log`. Pass when the first run fails and names `Planted.of`, and the second run passes.
- [ ] Lane 8. Plant a public function with five `int` parameters in `datadesk/core/tables/qcmr_common.py` and run the shape test. Then plant `def planted(flag: bool) -> None: ...` in `datadesk/core/tables/supp_common.py` and run it again. Save `family-helpers.log`. Pass when both runs fail and name the planted function.
- [ ] Lane 9. Plant a frozen dataclass `Planted` with the field `x: int` in `checkedtables/words.py` and run the shape test. Change the field to `flag: bool` and run it again. Save `dataclass-pins.log`. Pass when the first run fails `test_kit_dataclass_fields_are_pinned` and the second fails `test_bool_fields_are_page_facts_only` with `("Planted", "flag")`.
- [ ] Lane 10. Read the `Kit size report` step in the real CI run for the head SHA. Then plant 141 public functions in `checkedtables/__init__.py` and run the report command locally. Save `kit-size-report.log`. Pass when the CI step prints the `0 lines` and `0 public names` line, and the local run prints `141 public names` and exits 0.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Warm wall time in seconds of the six gates, run in sequence. Both sides produce it.
- [ ] Probe. Record `uptime`, warm each side once, then time the sequence five times per side with `time -p`, alternating base and head, each in its own synced worktree. Every command must exit 0, and pytest must print its pass count.
- [ ] Baseline. Record the base median first.
- [ ] Rule. The head fails when its median exceeds the base median by more than 5.0 s, or when its median is 20.0 s or more.

**Review gate.** None. S1-C is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Every Codex finding is confirmed or dropped, and the summary is in the PR's `## Verification` section.
- [ ] Rebased onto the tip of `step-01/b-import-contracts` after the verdict, patch-id unchanged.
- [ ] The root reports S1-C as verified, with its head SHA. The operator lands it after S1-B.

## Isolate the core tests and scan for effects (S1-D)

**Depends on.** S1-C. The base is `step-01/c-kit-shape`. S1-D owns clause C4.

**Files.**

- [ ] Edit `pyproject.toml`, `uv.lock` and `tests/test_gates.py`.
- [ ] Create `conftest.py` at the repository root.
- [ ] Create `packages/checkedtables/tests/conftest.py` and `packages/checkedtables/tests/test_isolation.py`.
- [ ] Create `packages/datadesk/tests/core/conftest.py` and `packages/datadesk/tests/core/test_isolation.py`.
- [ ] Create `tests/test_purity.py`.
- [ ] Edit `docs/design.md` section 11.1, and `docs/progress.md`.

**Build.**

- [ ] Add `pytest-socket>=0.8` to the `dev` group and run `uv lock`.
- [ ] Set `addopts = "--import-mode=importlib --disable-socket"` and add `packages/datadesk/tests` to `testpaths` in `pyproject.toml`.
- [ ] Write `pytest_configure` in the root `conftest.py`. It calls `pytest_socket.disable_socket()`, so the guard is in place before pytest imports any test module. With `--disable-socket` alone, a test module that runs `from socket import socket` keeps the real constructor and its test passes (Appendix A).
- [ ] Make `run_gate` in `tests/test_gates.py` copy the root `conftest.py` into the workspace too.
- [ ] Write the autouse fixture `_empty_working_directory` in both package `conftest.py` files. It takes `tmp_path` and `monkeypatch` and calls `monkeypatch.chdir(tmp_path)`.
- [ ] Write three tests in both `test_isolation.py` files. `test_working_directory_is_empty` asserts that `Path.cwd()` holds no entry. `test_sockets_are_blocked` expects `pytest_socket.SocketBlockedError` from `socket.socket()`. `test_early_bound_socket_is_blocked` expects the same error from a `socket` name that the module imports at its top with `from socket import socket`.
- [ ] Write `package_sources(name)` in `tests/test_purity.py`, with `PURE_PACKAGES = ("checkedtables", "datadesk.core")`. It finds each package's folder through `importlib.util.find_spec(name).submodule_search_locations`, so the scan does not depend on the working directory.
- [ ] Write `impurities(tree)` in `tests/test_purity.py` for the eight names of design section 11.1. It reports a call to `open`, `print` or `input`, a call to `.now()` or `.today()`, an attribute read on `os` or `time`, and any use or import of `random`.
- [ ] Make `impurities` also report any import of `builtins` and any attribute read on it.
- [ ] Make `impurities` also report mutable module state. That is an assignment at module level whose value is a list, dict or set display, a comprehension of one of those, or a call to `list`, `dict`, `set` or `bytearray`. `__all__` gets no exemption, so a package writes it as a tuple. Design section 3 allows tuples, frozen dataclasses and `MappingProxyType` as module constants.
- [ ] Add `builtins` and mutable module state to the purity row of design section 11.1, and record the change under Deviations in `docs/progress.md`. `CLAUDE.md` hard rule 3 says the purity test enforces the ban on mutable module state.
- [ ] Write `test_pure_packages_have_no_effects` in `tests/test_purity.py`. It fails with one `path:line` entry per hit.
- [ ] Write `test_scan_reports_each_banned_form` in `tests/test_purity.py`. It parses one source string per banned form and asserts one hit for each. The forms are the eight names, `import builtins`, `builtins.open("x")`, `CACHE: dict[str, str] = {}`, `ITEMS = []` and `SEEN = set()`.
- [ ] Write `test_scan_allows_immutable_constants` in `tests/test_purity.py`. It asserts no hit for `NAMES = ("a", "b")`, for `LOOKUP = MappingProxyType({"a": 1})`, and for a list assigned inside a function.
- [ ] Add `test_planted_socket_call_fails_pytest` to `tests/test_gates.py`. The clean copy gets a core test, `packages/datadesk/tests/core/test_planted_socket.py`, that only names `socket.socket`. The planted copy gets the same test with the call `socket.socket()`. It runs the `uv run pytest` gate with the extra arguments `-p no:cacheprovider` and `packages/datadesk/tests/core`, and asserts exit code 1 and the text `SocketBlockedError` for the planted copy.
- [ ] Add `test_planted_early_bound_socket_fails_pytest` to `tests/test_gates.py`. It is the same test with `from socket import socket` at the top of the planted module and the call `socket()`.
- [ ] Add a note to `docs/progress.md`. `--disable-socket` applies to every test, so a later adapter contract test that needs the network opts in with the `enable_socket` marker of pytest-socket. The marker reopens calls to `socket.socket()`. A name that a module binds with `from socket import socket` stays blocked under the marker, because the root `conftest.py` installs the block before that import runs (Appendix A).
- [ ] Leave the step 1 row of `docs/progress.md` at `in progress`. The row changes only after the verdict, in the Merge block below.

**You see.**

- [ ] `uv run pytest` ends with `20 passed`.
- [ ] A core test that calls `socket.socket()` fails with `pytest_socket.SocketBlockedError: A test tried to use socket.socket.`
- [ ] With `print(1)` appended to `packages/checkedtables/src/checkedtables/words.py`, `uv run pytest tests/test_purity.py` fails and names `words.py:1` and `print()`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_gates.py` gains `test_planted_socket_call_fails_pytest` and `test_planted_early_bound_socket_fails_pytest`. Run `uv run pytest tests/test_gates.py -k socket`.
  - [ ] In a scratch copy, remove `--disable-socket` from `addopts` and delete the root `conftest.py`. Both planted tests fail, and so do the socket tests in `test_isolation.py`.
  - [ ] In a scratch copy, delete only the root `conftest.py`. `test_planted_early_bound_socket_fails_pytest` and `test_early_bound_socket_is_blocked` fail.
- [ ] Both `test_isolation.py` files gain their three tests. Run `uv run pytest packages/checkedtables/tests packages/datadesk/tests/core`.
  - [ ] In a scratch copy, delete one package `conftest.py`. `test_working_directory_is_empty` fails in that folder.
- [ ] `tests/test_purity.py` gains `test_pure_packages_have_no_effects`, `test_scan_reports_each_banned_form` and `test_scan_allows_immutable_constants`. Run `uv run pytest tests/test_purity.py`.
- [ ] The branch log shows the planted tests and the isolation tests committed before `--disable-socket`, the root `conftest.py` and the fixtures, and failing at that commit.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus high` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run the six gates at the base, which is the S1-C head, and at the head. Then add `packages/datadesk/tests/core/test_planted_socket.py`, whose one test `test_planted` calls `socket.socket()`, on both sides, and run that node ID with `uv run pytest packages/datadesk/tests/core/test_planted_socket.py::test_planted`. Save `gates-clean.log`. Pass when the gates exit 0 on both sides, the node prints `1 passed` at the base, which is recorded against the base, and the node fails with `SocketBlockedError` at the head.
- [ ] Lane 2. Open a temporary PR from `verify/s1-d-lane-2` with a new `packages/datadesk/tests/core/test_planted_socket.py` that calls `socket.socket()`. Save `ci-socket.log`. Pass when the `pull_request` run fails and the `uv run pytest` step fails with `SocketBlockedError`.
- [ ] Lane 3. Plant three core tests that call `socket.create_connection(("example.com", 80))`, `urllib.request.urlopen("http://example.com")` and `asyncio.run(asyncio.open_connection("example.com", 80))`. Save `socket-routes.log`. Pass when each test fails with `SocketBlockedError`.
- [ ] Lane 4. Plant, in each core test folder, a test module that starts with `from socket import socket` and whose test calls `socket()`. Run `uv run pytest`. Save `early-binding.log`. Pass when both planted tests fail with `SocketBlockedError`.
- [ ] Lane 5. Plant a test in each core test folder that writes `out.txt` to the working directory. Run `uv run pytest`, then `git status --porcelain`. Save `empty-cwd.log`. Pass when both tests pass and `git status` lists only the two planted test files.
- [ ] Lane 6. Append `open("x")`, `print(1)` and `input()` to `checkedtables/words.py`, one at a time, and run `uv run pytest tests/test_purity.py` after each. Save `purity-kit.log`. Pass when each run fails and names the file, the line and the call.
- [ ] Lane 7. Append `datetime.now()`, `date.today()`, `time.time()`, `os.getcwd()`, `import random` and `from random import choice` to `datadesk/core/tables/birt.py`, one at a time, and run `uv run pytest tests/test_purity.py` after each. Save `purity-core.log`. Pass when each run fails and names the file and the line.
- [ ] Lane 8. Append `print(1)` and `open("x")` to `datadesk/shell/__init__.py`, then to `phillyledger/api.py`, and run `uv run pytest tests/test_purity.py`. Save `purity-shell.log`. Pass when every run passes.
- [ ] Lane 9. Append, one at a time, `CACHE: dict[str, str] = {}`, `ITEMS = []`, `__all__ = ["a"]` and the pair `import builtins` and `builtins.open("x")` to `checkedtables/words.py`, and run `uv run pytest tests/test_purity.py` after each. Then append only `NAMES = ("a", "b")` and run it again. Save `module-state.log`. Pass when the first four runs fail and name the line, and the last run passes.
- [ ] Lane 10. From an empty folder outside the repository, run `uv run --project <repo> pytest -c <repo>/pyproject.toml --rootdir <repo> <repo>/tests/test_purity.py`, then repeat with `print(1)` appended to `checkedtables/words.py`. Save `purity-any-cwd.log`. Pass when the first run passes and the second fails.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Warm wall time in seconds of the six gates, run in sequence. Both sides produce it.
- [ ] Probe. Record `uptime`, warm each side once, then time the sequence five times per side with `time -p`, alternating base and head, each in its own synced worktree. Every command must exit 0, and pytest must print its pass count.
- [ ] Baseline. Record the base median first.
- [ ] Rule. The head fails when its median exceeds the base median by more than 5.0 s, or when its median is 20.0 s or more.

**Review gate.** None. S1-D is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Every Codex finding is confirmed or dropped, and the summary is in the PR's `## Verification` section.
- [ ] Rebased onto the tip of `step-01/c-kit-shape` after the verdict, patch-id unchanged.
- [ ] After the verdict, the owner adds one commit that changes only `docs/progress.md`. It sets the step 1 row to `check passed` with that day's date and the four branch names. It records the SHA and run ID of the clean CI run and of the three failed plant runs for C2, C3 and C4.
- [ ] One verifier confirms that the commit touches only `docs/progress.md` and that the `CI` run at the new head is green.
- [ ] The root reports S1-D as verified, with its head SHA. The operator lands it after S1-C.

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] The step 1 row of `docs/progress.md` at the S1-D head shows `check passed`, the date, the four branch names and the four run IDs.
- [ ] The reference snapshot commands still print what `<root>/.audit/reference-baseline.txt` holds.
- [ ] `git ls-remote --heads origin 'verify/*'` prints nothing, and `gh pr list --state open --search "head:verify/"` lists no PR.
- [ ] Reply to the operator with the report that `autopilot-stack.md` names, each PR with its verdict.

## Appendix A. Prototype evidence

A `pstack:poteto-agent` delegate built a throwaway copy of the step 1 workspace on November 22,
2026, and the root reran the commands marked "rerun" below. The copy is in the session's scratch
folder, at commit `97768af1a81cd22b03a3a0a38b561755e9c4c504` of its own repository. The scratch
folder can be cleared at any time, so this appendix records the commands and what they printed.
None of the prototype's code is for reuse.

The versions that `uv lock` resolved were ruff 0.17.5, ty 0.0.104, import-linter 2.16, grimp 3.20,
prek 0.5.10, pytest 9.2.0 and pytest-socket 0.8.1, with uv 0.13.6 and Python 3.12.15.

| Question | Result | Evidence |
|---|---|---|
| Does a virtual root with three `uv_build` members sync on Python 3.12? | Yes. Each member installs as an editable through one `.pth` file. | Observed by the delegate. `uv_build` needs `src/<name>/__init__.py`. |
| Do the six gates pass on empty modules? | Yes. | Rerun. `5 passed`, `All checks passed!` twice, `Contracts: 8 kept, 0 broken.`, three hooks `Passed`. |
| Does the design's import-linter block load on five `__init__.py` files? | No. | Rerun. `Module 'checkedtables.checks' does not exist.`, exit 1. |
| What makes all eight contracts load? | 46 empty modules. import-linter has no option that tolerates a missing module. | Observed by the delegate in `importlinter/contracts/forbidden.py` line 107 and `independence.py` line 99. |
| Can a wildcard stand in for the missing modules? | No. `datadesk.core.tables.*` matches nothing and the contract is kept without a warning. | Observed by the delegate. |
| Do `checks/` and `_shell/` work as folders? | Yes. | Rerun by the root with both as packages. `Contracts: 8 kept, 0 broken.` |
| Does a planted `import boto3` in `datadesk.core` fail `lint-imports`? | Yes, with boto3 installed or not. | Rerun. `datadesk core is pure BROKEN`, `Contracts: 7 kept, 1 broken.`, exit 1. |
| Does import-linter enforce standard-library modules? | Yes. This settles the "Not verified" note in design sections 12.5 and 17.4. | Rerun for `import os`. The delegate observed the same for `pathlib`, `logging` and `time`. |
| Does the design's helper contract stop a helper that imports a table? | No. `qcmr_common` importing `birt` gives `Contracts: 8 kept, 0 broken.` | Run by the root after the Codex review. |
| Does the contract stop it with the 20 table modules added? | Yes. The clean tree keeps eight contracts, the plant breaks `family helpers do not import table modules`, and a table that imports a helper still passes. | Run by the root. |
| Which ruff shape scopes the bans and the `D` rules? | One root config with negated `per-file-ignores` globs. | Observed by the delegate. Three `TID251` in core, none in shell. |
| Does ruff report `TID251` for a call with no import? | No. Four bare calls give five `F821` and no `TID251`. The probe in S1-B lane 10 gives three `TID251` in core and none in shell. | Run by the root. |
| Do `D100` and `D104` fire on empty modules? | Yes, 21 errors in `checkedtables` and `phillyledger`. | Observed by the delegate. |
| Do the existing Python files pass the planned ruff config? | No. `docs/prototype/` and `.claude/hooks/` give 132 errors, and six files would be reformatted. | Run by the root, read-only. |
| What does a socket call in a core test raise? | `pytest_socket.SocketBlockedError: A test tried to use socket.socket.`, exit 1. | Observed by the delegate. |
| Does `--disable-socket` stop a module that runs `from socket import socket`? | No. The test opens a socket and prints `1 passed`. | Run by the root after the Codex review. |
| Does a root `conftest.py` that calls `disable_socket()` in `pytest_configure` stop it? | Yes. The same test fails with `SocketBlockedError`, and the other five tests still pass. | Run by the root. |
| Can a test still open a socket on purpose under that root `conftest.py`? | Yes, with the `enable_socket` marker and a call to `socket.socket()`. A name bound by `from socket import socket` stays blocked under the marker. The four-test probe prints `1 failed, 3 passed`. | Run by the root. |
| Does a planted test read the copy or the installed package? | The copy, only when `PYTHONPATH` names the copy's `src` folders. Without it the planted copy passes both gates. | Observed by the delegate with a negative control. |
| Do the three planted tests pass with sockets disabled? | Yes, in 0.43 s, 1.37 s and 1.34 s. | Rerun. `3 passed in 3.50s`. |
| What does the design's `bool` predicate miss? | `flag: bool \| None` and `flag: Optional[bool]`. | Rerun. Both exit 0. |
| Does a union-aware predicate catch them? | Yes, as types and as string annotations, with `inspect.signature(fn, eval_str=True)` and `typing.get_args`. A plain `get_args` test also flags `list[bool]`, so the predicate must check for a union first. | Run by the root. |
| Does the suite pass on Python 3.14? | Yes. | Run by the root on Python 3.14.10. `5 passed`. |
| Does `uv build --all-packages` work? | Yes. Three wheels and three source archives, with no `tests/` path in the `datadesk` wheel. | Run by the root. |
| Did this session's plain `git status` rewrite the reference index? | No. The index was last written on November 12, 2026, with the reference's HEAD commit. | Read by the root with `stat`. |

The delegate timed each gate five times, warm, on this Mac. The medians were 3.75 s for
`uv run pytest`, 0.21 s for `uv run lint-imports`, 0.22 s for `uv run prek run --all-files`, and
under 0.1 s each for the two ruff commands and `uv run ty check`. The spread was under 0.2 s for
every gate. The three planted tests took about 3.0 s of the pytest time. The delegate inferred
the limit, which is the start of an inner pytest at about 0.65 s per run. The load average was
18.6 when the root reran the gates, so a quiet machine is likely faster. The plan now has five
planted tests where the prototype had three. The budgets in the perf blocks are guesses with room
above these numbers, not measurements.

These stay unproven until the build.

- The GitHub Actions workflow, on a Linux runner. The prototype ran on macOS only.
- The temporary PRs, and `if: ${{ !cancelled() }}` on the gate steps.
- `run_gate` taking its command from `GATES`. The prototype passed the command as a list.
- Python 3.13. The prototype ran 3.12 and 3.14.
- Whether pytest-socket blocks every way to open a connection. The root planted the two import
  spellings of `socket`, and S1-D lane 3 covers the rest.
- The scan for mutable module state. Nothing has run it.

## Appendix B. Alternatives rejected

- **Enable four contracts now and add the rest as their modules arrive.** Each later step would
  have to remember its contract, and a forgotten one fails nothing. Design section 12.5 names the
  QSMR modules as the only ones that join the list later, in step 14.
- **Use wildcards in place of the empty modules.** A wildcard that matches nothing keeps the
  contract with no warning, so it guards nothing until the modules exist.
- **Create all 107 modules of design section 12 as empty files.** No gate needs the other 61.
- **Give each empty module a one-line docstring.** `CLAUDE.md` wants docstrings only on the names
  users import, so the plan ignores `D100` and `D104`.
- **Put a nested `ruff.toml` in each pure package.** That costs two more files and a second copy
  of the ban list.
- **Lint `docs/prototype/` and `.claude/hooks/`.** The vocabulary prototype is ported at step 5
  and never imported, and the hooks guard this repository. The plan excludes both from ruff and
  ty and changes neither.
- **Run `uv run` inside the planted tests.** Each run would build a second environment. The tests
  use the executables of the current one.
- **Make `lint-imports` and `pytest` prek hooks.** The planted tests already run both gates, and
  a pytest hook adds seconds to every commit.
- **Build the three guards as siblings on S1-A.** They share `pyproject.toml`, `uv.lock`,
  `ci.yml` and `tests/test_gates.py`, so two owners would write the same files in parallel.
- **Use two or three pull requests.** With four, each clause has one owner and one diff.
- **Commit a test that compares the contracts with the design's block.** Audit 2 of
  `verify-step` reads for that drift on every pull request.
- **Show the plants fail on pushes to `verify/**`.** A push is a different event from the one
  that guards a pull request, so a workflow could treat the two differently. The lanes use
  temporary PRs.
- **Keep the design's `bool` predicate and its helper contract as written.** Both pass a case
  that the design's own text bans, so the plan changes each with a Deviations entry.
- **Put the socket guard in each package `conftest.py`.** A root `conftest.py` with a hook is the
  form the root ran, and `run_gate` copies it.

## Appendix C. Risks

- **CI is unproven until the first pull request (S1-A).** The owner watches lanes 2 to 6. A red
  run on a clean head is a finding against `ci.yml`, not against the gates.
- **Claude Code has no control skill for a command line (every PR).** Lanes drive the gates with
  shell commands and return transcripts. The root reads the transcripts, not the lane's summary.
- **The plan changes the design in four places (S1-B, S1-C, S1-D).** The list is in "How to read
  this". Each is a stricter rule than the design gives. The owner kept all four on November 22,
  2026.
- **The purity scan matches names (S1-D).** It flags a parameter named `time` and a variable
  named `random`. It misses a renamed import such as `from os import environ`, which the import
  contract catches. It reads module-level assignments only, so a mutable class attribute passes.
- **`../gov-budget-data` already has six uncommitted entries (every PR).** Audit 7 of
  `verify-step` expects an empty status and uses a plain `git status`, which can rewrite the
  reference's index. Lanes run this plan's snapshot commands in its place. The skill itself is
  under `.claude/`, which no pull request touches, so changing it is the owner's call.
- **Temporary PRs are visible on GitHub (every PR).** Seven open and close during the run, and
  each sends its notifications. Close checks that none stays open and no `verify/` branch remains.
- **GitHub Actions usage (every PR).** The run starts about 14 jobs for the temporary PRs and two
  per push to a PR branch. The operator confirms the allowance at the go.
- **ty and prek are below version 1.0 (S1-A).** The plan pins both. An upgrade is its own change.
- **Verification is large for small diffs (every PR).** The playbook's swarm is 14 verifier runs
  per pull request, 56 for the step, plus four Codex reviews. The operator can cap the lanes at
  the go.

## Appendix D. Links and reading list

Read these before any edit.

- `CLAUDE.md`, all of it.
- `docs/design.md` section 15 step 1, section 3, section 11.1, section 11.4, section 12 and
  section 12.5.
- `docs/principles.md` section 7, the purity checklist.
- `.claude/skills/verify-step/SKILL.md` and `.claude/skills/codex-review/SKILL.md`.
- `../gov-budget-data/pyproject.toml`, `prek.toml` and `.github/workflows/ci.yml`, read-only.

No pull request in this plan needs `<pstack>/skills/how/SKILL.md`. Run
`<pstack>/skills/interrogate/SKILL.md` only if the owner contests the 46 empty modules. The owner
has settled the four design changes. The decision trail is `.audit/step-01.tsv`, kept out of git,
per `<pstack>/skills/show-me-your-work/SKILL.md`.

## Appendix E. Codex review

Codex reviewed this plan at commit `1c403c6d` on November 22, 2026, with `gpt-6.2-astra` at
`xhigh`. The report is `.codex-review/step-01-plan-1c403c6d.md`, which git ignores. It found that
every clause has exactly one owner, and it raised 14 findings. The root checked each one by a
rerun or by a read of the quoted lines. All 14 held, and none was dropped.

| # | Severity | Finding | How the root checked it | Revision |
|---|---|---|---|---|
| 1 | blocks | The live plants ran on a push, and a workflow can ignore a failure on `pull_request` and keep every `run` line. | Read the quoted plan lines. | Lanes open temporary PRs. `test_ci_runs_every_gate` bans `continue-on-error` and `github.event_name` and fixes every `if`. |
| 2 | blocks | A core test that runs `from socket import socket` opens a socket under `--disable-socket`. | Rerun. `1 passed`. | S1-D adds a root `conftest.py`, a second planted test and a third isolation test. |
| 3 | blocks | A plain `git status` can rewrite the reference's index, the status text hides later edits, and lanes could not find the baseline. | Read the git documentation, and ran the status with `--no-optional-locks`. | The snapshot uses `--no-optional-locks`, hashes the diffs and the untracked files, and lives at an absolute path. |
| 4 | blocks | `prek install` in a worktree installs the hook for every worktree. | Read the git documentation on the shared hooks folder. | S1-A lane 7 runs in its own clone, and the boot recipe bans `prek install` in a worktree. |
| 5 | should fix | The shape test left out the four family helpers. | Read design lines 3856 to 3860. | S1-C runs the first test over `FAMILY_HELPERS`, with a planted test and a lane. |
| 6 | should fix | The plan left `bool \| None` and `Optional[bool]` green. | Rerun. Both exit 0. | S1-C widens the predicate and changes design section 11.4. |
| 7 | should fix | The helper contract lets a helper import a table module. | Rerun. `8 kept, 0 broken`. | S1-B adds the 20 table modules to the contract and to design section 12.5. |
| 8 | should fix | The purity scan passes `builtins.open` and mutable module state. | Read the prototype's scanner and `CLAUDE.md` hard rule 3. | S1-D scans for both, with two tests on the scanner and a lane. |
| 9 | should fix | S1-B lane 10 gave `F821`, not `TID251`. | Rerun. Five `F821`, no `TID251`. | Lane 10 uses a probe with its imports. |
| 10 | should fix | S1-D lane 1 could pass at the base without collecting the plant, and `run_gate` had no way to take extra arguments. | Read the `testpaths` values in the plan. | Lane 1 runs the node ID on both sides, and `run_gate` takes `extra`. |
| 11 | should fix | Two green jobs do not show two Python versions. | Read the plan and the reference workflow. | The workflow passes the matrix value to `setup-uv` and asserts the version. |
| 12 | should fix | S1-D recorded the pass date before the proof. | Read the plan and `docs/progress.md`. | The row changes in a commit after the verdict. |
| 13 | should fix | The preconditions left out GitHub permissions and Actions usage. | Read `CLAUDE.md` hard rule 7. | Arm checks the token scopes and has the operator confirm the allowance. |
| 14 | minor | The kit size report did not reach the PR. | Read design line 3851. | The PR body carries the line from S1-C on. |
