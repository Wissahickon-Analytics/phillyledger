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
runs that gate. The two together prove the clause, and one live lane per clause shows the real CI
run fail.

## Program checklist

### Arm the program

The evidence for each box in this section is a row in the decision trail.

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on the operator's explicit go.
- [ ] Confirm the operator's preconditions before any owner starts. On November 22, 2026 `main` held only `README.md`, and the design, the rules and this plan were untracked. Agents never push to `main` (`CLAUDE.md`, hard rule 9).
  - [ ] `git rev-parse --abbrev-ref HEAD` prints `main`, and `git status --porcelain` prints nothing.
  - [ ] `git ls-remote origin main` prints the SHA that `git rev-parse main` prints.
  - [ ] `gh repo view --json nameWithOwner,defaultBranchRef` names the repository and `main`.
  - [ ] `git show origin/main:docs/plans/step-01.md` prints this plan.
  - [ ] Appendix E holds the result of `/codex-review plan 1`.
- [ ] Start the decision trail at `.audit/step-01.tsv` per `<pstack>/skills/show-me-your-work/SKILL.md`.
- [ ] Save the output of `git -C ../gov-budget-data status --porcelain` as `.audit/reference-baseline.txt`. On November 22, 2026 the output had six entries, all the owner's own work. Audit 7 of `verify-step` compares against this file.
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
  - [ ] S1-C touches only `pyproject.toml`, `.github/workflows/ci.yml`, `tests/test_gates.py` and `packages/checkedtables/tests/test_library_shape.py`.
  - [ ] S1-D touches only `pyproject.toml`, `uv.lock`, `tests/test_gates.py`, `tests/test_purity.py`, and the `conftest.py` and `test_isolation.py` files in `packages/checkedtables/tests/` and `packages/datadesk/tests/core/`.
  - [ ] Every PR may also edit `docs/progress.md`. A PR edits `docs/plans/step-01.md` when the build shows this plan wrong.
  - [ ] No PR touches `docs/prototype/`, `.claude/`, `CLAUDE.md` or anything under `../gov-budget-data`.
- [ ] Hold the review gate. No PR in this plan changes an interaction, so none is review-gated. Every PR still stops at verified and waits for the operator to land it.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Run `command -v origin`. When it fails, use `gh` for every PR operation and record the fallback. Never require `gt`.
- [ ] Open the PR ready, never draft, with `gh pr create --base <base-branch>`. S1-A targets `main`. A stack child targets its parent branch. Write the title as `type(scope): subject`.
- [ ] Write the PR body per `opening-a-pr.md`. Open `## Why` with the user's goal. Put the Codex summary under `## Verification`.
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
  - [ ] Audit lane 2 runs audits 1 to 7 of `verify-step` on the diff and distrusts the PR body. For audit 7 it compares with `.audit/reference-baseline.txt`.
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
- [ ] For a lane that needs real CI, cut `verify/<pr-id>-lane-<n>` from the head SHA, commit the plant there, push the branch, wait with `gh run watch`, save `gh run view --log-failed`, then delete the branch with `git push origin --delete`.
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
- [ ] Write `test_ci_runs_every_gate` in `tests/test_gates.py`. It reads `.github/workflows/ci.yml` and fails, with the gate in the message, unless the text holds the line `run: <gate>` for every member of `GATES`.
- [ ] Write `test_workspace_packages_import` in `tests/test_workspace.py`. It imports `checkedtables`, `phillyledger`, `datadesk.core` and `datadesk.shell`.
- [ ] Write `.github/workflows/ci.yml` with one job named `gates`. It runs on `pull_request`, on a push to `main`, and on a push to `verify/**`. The matrix is Python 3.12 and 3.14. Pin `actions/checkout` and `astral-sh/setup-uv` to the commit SHAs in `../gov-budget-data/.github/workflows/ci.yml`.
- [ ] Give the `gates` job the step `uv sync --locked`, then one step per member of `GATES`. Give each gate step `if: ${{ !cancelled() }}`, so one failed gate does not hide the others.
- [ ] Add `.audit/` to `.gitignore`.
- [ ] Set the step 1 row of `docs/progress.md` to `in progress` with the branch name.

**You see.**

- [ ] `uv sync --locked` exits 0, and `uv run python -c "import checkedtables, phillyledger, datadesk.core, datadesk.shell"` prints nothing.
- [ ] `uv run ruff check .` and `uv run ty check` each print `All checks passed!`.
- [ ] `uv run prek run --all-files` prints `Passed` for `ruff check`, `ruff format` and `ty check`.
- [ ] `uv run pytest` ends with `2 passed`.
- [ ] The `CI` run for the PR head shows two green `gates` jobs, one per Python version.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_gates.py` gains `test_ci_runs_every_gate`. Run `uv run pytest tests/test_gates.py`.
  - [ ] Delete the `uv run ty check` step in a scratch copy of `ci.yml`. The test fails and names that gate.
- [ ] `tests/test_workspace.py` gains `test_workspace_packages_import`. Run `uv run pytest tests/test_workspace.py`.
- [ ] The branch log shows both tests committed before the packages and `ci.yml`, and failing at that commit.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus high` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `uv sync --locked` and the five gates at `main` and at the head. `main` has no workspace, so record that `uv sync` fails there, and gate the head. Save `gates-clean.log`. Pass when the `main` failure is recorded and every gate exits 0 at the head with `2 passed`.
- [ ] Lane 2. Read the real CI run for the head SHA with `gh run list --commit <head SHA>` and `gh run view`. Save `ci-green.log`. Pass when the `CI` run concludes `success` and both `gates` jobs, Python 3.12 and 3.14, show every gate step green.
- [ ] Lane 3. Push `verify/s1-a-lane-3` with `import json` appended to `packages/datadesk/src/datadesk/shell/__init__.py`. Save `ci-ruff-check.log`. Pass when the run fails, the `uv run ruff check .` step reports `F401`, and the `uv run pytest` step still ran.
- [ ] Lane 4. Push `verify/s1-a-lane-4` with the line `x  =  1` appended to the same file. Save `ci-ruff-format.log`. Pass when the run fails and the `uv run ruff format --check .` step reports that the file would be reformatted.
- [ ] Lane 5. Push `verify/s1-a-lane-5` with the line `X: int = "a"` appended to the same file. Save `ci-ty.log`. Pass when the run fails and the `uv run ty check` step reports `invalid-assignment`.
- [ ] Lane 6. Push `verify/s1-a-lane-6` with a new `tests/test_planted_failure.py` whose one test asserts `1 == 2`. Save `ci-pytest.log`. Pass when the run fails and the `uv run pytest` step reports `1 failed`.
- [ ] Lane 7. Run `uv run prek install`, append `x  =  1` to a tracked Python file, stage it, and run `git commit`. Save `prek-hook.log`. Pass when `git commit` exits non-zero, the `ruff format` hook reports a changed file, and `git log -1` still shows the head SHA.
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
- [ ] Copy the TOML block of design section 12.5, lines 4061 to 4132 of `docs/design.md`, into `pyproject.toml` word for word. The evidence is an empty `diff` between the two blocks.
- [ ] Create the 46 empty files that the contracts name. import-linter refuses a contract that names a module that does not exist (Appendix A). The evidence is that `git ls-files 'packages/*/src/*.py' | wc -l` prints 51 and every one of those files has size 0.
- [ ] Add `TID251` to the ruff `select` list, and add the `banned-api` table with `datetime.datetime.now`, `datetime.date.today` and `tomllib.load`.
- [ ] Scope the ban with one `per-file-ignores` entry, `"!packages/{checkedtables/src/checkedtables,datadesk/src/datadesk/core}/**" = ["TID251"]`.
- [ ] Add `uv run lint-imports` to `GATES` in `tests/test_gates.py`, and add the step `run: uv run lint-imports` to `ci.yml` with the same `if` as the other gates.
- [ ] Write `run_gate(workspace, plants, gate)` in `tests/test_gates.py`. It copies `packages/` and `pyproject.toml` into `workspace`, appends each plant to its file, and runs the gate with the copy as the working directory.
- [ ] Make `run_gate` take a member of `GATES`, drop the `uv run` prefix, and run that executable from the folder of `sys.executable`. It sets `PYTHONPATH` to the three `src` folders of the copy, so the gate reads the copy and not the installed packages. It passes `--no-cache` to `lint-imports`.
- [ ] Write `clean_then_planted(tmp_path, clean, planted, gate)` in `tests/test_gates.py`. It runs the gate on a clean copy, asserts exit code 0, then returns the result of the planted copy.
- [ ] Write `test_planted_boto3_import_fails_lint_imports`. It plants `import boto3` at the end of `packages/datadesk/src/datadesk/core/__init__.py` and asserts a non-zero exit code and the text `datadesk core is pure BROKEN`.
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
- [ ] Lane 2. Push `verify/s1-b-lane-2` with `import boto3` appended to `packages/datadesk/src/datadesk/core/__init__.py`. Save `ci-boto3.log`. Pass when the run fails and the `uv run lint-imports` step fails with `datadesk core is pure BROKEN`.
- [ ] Lane 3. Append `import os`, `from pathlib import Path`, `import logging` and `import time` to the same file, one at a time, and run `uv run lint-imports` after each. Save `stdlib-plants.log`. Pass when each run exits 1 with `datadesk core is pure BROKEN`.
- [ ] Lane 4. Append `import datadesk` to `checkedtables/words.py`, then separately `import pytest` to `checkedtables/testing.py`, and run `uv run lint-imports` after each. Save `kit-contract.log`. Pass when each run exits 1 with `checkedtables holds no I/O and no Philadelphia BROKEN`.
- [ ] Lane 5. Append `from checkedtables import words` to `checkedtables/checks/__init__.py` and run `uv run lint-imports`. Save `arithmetic-contract.log`. Pass when the run exits 1 with `arithmetic never sees words BROKEN`.
- [ ] Lane 6. Append `import datadesk` to `phillyledger/api.py`, then separately `from phillyledger import api` to `phillyledger/manifest.py`, and run `uv run lint-imports` after each. Save `reader-contracts.log`. Pass when the first run breaks `the reader stands alone` and the second breaks `the reader's core is pure`.
- [ ] Lane 7. Append `import datadesk.shell` to `datadesk/core/__init__.py`, then separately `import boto3` to `datadesk/shell/__init__.py`, and run `uv run lint-imports` after each. Save `layers.log`. Pass when the first run breaks `shell over core` and the second prints `Contracts: 8 kept, 0 broken.`
- [ ] Lane 8. Append `from datadesk.core.tables import birt` to `datadesk/core/tables/sales.py`, then separately `from datadesk.core.tables import catalog` to `datadesk/core/tables/qcmr_common.py`. Save `table-contracts.log`. Pass when the first run breaks `table modules do not import each other` and the second breaks `family helpers do not import table modules`.
- [ ] Lane 9. Delete `packages/checkedtables/src/checkedtables/lex.py` and run `uv run lint-imports`. Save `missing-module.log`. Pass when the run exits 1 with `Module 'checkedtables.lex' does not exist.`
- [ ] Lane 10. Append calls to `datetime.now()`, `date.today()`, `tomllib.load(handle)` and `tomllib.loads("")` to `datadesk/core/tables/birt.py` and run `uv run ruff check .`. Move the lines to `datadesk/shell/__init__.py` and run the command again. Save `banned-api.log`. Pass when the first run reports three `TID251` errors and none for `tomllib.loads`, and the second reports no `TID251`.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Warm wall time in seconds of the gate sequence, five gates at the base and six at the head. Both sides produce it.
- [ ] Probe. Record `uptime`, warm each side once, then time the sequence five times per side with `time -p`, alternating base and head, each in its own synced worktree. Every command must exit 0, and pytest must print its pass count.
- [ ] Baseline. Record the base median first.
- [ ] Rule. The head fails when its median exceeds the base median by more than 3.0 s, or when its median is 15.0 s or more.

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
- [ ] Edit `docs/progress.md`.

**Build.**

- [ ] Write `public_functions(package)` in `packages/checkedtables/tests/test_library_shape.py`. It imports the package and every submodule that `pkgutil.walk_packages` finds, and it skips a dotted name when any part starts with `_`.
- [ ] Make `public_functions` yield every public function that a module defines, and every public method of every public class that a module defines, class methods and static methods included. A name is public when it does not start with `_`. A module defines an object when the object's `__module__` is the module's name.
- [ ] Type the return value of `public_functions` as `Iterator[types.FunctionType]`. With `Callable[..., object]`, `uv run ty check` rejects `fn.__qualname__` (Appendix A).
- [ ] Write `test_no_bool_parameters_and_at_most_four` as design section 11.4 gives it. For a method, do not count the bound first parameter.
- [ ] Write `kit_dataclasses()`, `field_names(cls)` and `FIELD_SNAPSHOT = {}`, then `test_kit_dataclass_fields_are_pinned` as the design gives it.
- [ ] Write `bool_fields(classes)` and `test_bool_fields_are_page_facts_only`. At this step the expected value is `set()`. The design's two members arrive in the pull requests that create `Word` and `Column`.
- [ ] Write `source_lines(package)`, `public_names(package)` and `report_budget()`. `source_lines` counts the lines of the package's `.py` files that are neither blank nor comments. `public_names` returns the names in the package's namespace that do not start with `_` and are not modules.
- [ ] Call `report_budget()` under `if __name__ == "__main__"`. At this step it prints `checkedtables: 0 lines (budget 3,800), 0 public names (budget 140)`.
- [ ] Leave `test_closed_lists_are_pinned` out, because none of its lists exists yet. Record in `docs/progress.md` that each list's pin lands in the pull request that creates the list (`CLAUDE.md`, hard rule 6).
- [ ] Add `packages/checkedtables/tests` to `testpaths` in `pyproject.toml`.
- [ ] Add `test_planted_bool_parameter_fails_shape_test` to `tests/test_gates.py`. It plants `def planted(flag: bool) -> None: ...` at the end of `packages/checkedtables/src/checkedtables/__init__.py`, runs the `uv run pytest` gate on the shape test file with `-p no:cacheprovider`, and asserts exit code 1 and the text `AssertionError: planted`.
- [ ] Add a CI step named `Kit size report` that runs `uv run python packages/checkedtables/tests/test_library_shape.py`. Keep it out of `GATES`, because the report never fails the build (design section 18.2).

**You see.**

- [ ] `uv run pytest packages/checkedtables/tests` ends with `3 passed`.
- [ ] `uv run python packages/checkedtables/tests/test_library_shape.py` prints `checkedtables: 0 lines (budget 3,800), 0 public names (budget 140)`.
- [ ] `uv run pytest` ends with `7 passed`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `packages/checkedtables/tests/test_library_shape.py` gains `test_no_bool_parameters_and_at_most_four`, `test_kit_dataclass_fields_are_pinned` and `test_bool_fields_are_page_facts_only`. Run `uv run pytest packages/checkedtables/tests/test_library_shape.py`.
- [ ] `tests/test_gates.py` gains `test_planted_bool_parameter_fails_shape_test`. Run `uv run pytest tests/test_gates.py::test_planted_bool_parameter_fails_shape_test`.
  - [ ] In a scratch copy, delete the `bool` assertion from `test_no_bool_parameters_and_at_most_four`. The planted test fails.
- [ ] The branch log shows the planted test committed before the shape test, and failing at that commit.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus high` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run the six gates at the base, which is the S1-B head, and at the head. Record that the base has no shape test. Save `gates-clean.log`. Pass when every gate exits 0 on both sides and the head prints `7 passed`.
- [ ] Lane 2. Push `verify/s1-c-lane-2` with `def planted(flag: bool) -> None: ...` appended to `packages/checkedtables/src/checkedtables/__init__.py`. Save `ci-bool.log`. Pass when the run fails and the `uv run pytest` step fails with `AssertionError: planted`.
- [ ] Lane 3. Put `from __future__ import annotations` and `def planted(flag: bool) -> None: ...` in `checkedtables/words.py` and run the shape test. Save `submodule-string-annotation.log`. Pass when the test fails and names `planted`.
- [ ] Lane 4. Plant `def planted(*, flag: bool = False) -> None: ...` in `checkedtables/lex.py` and run the shape test. Save `keyword-only-default.log`. Pass when the test fails and names `planted`.
- [ ] Lane 5. Plant a public function with five `int` parameters in `checkedtables/text.py` and run the shape test. Remove one parameter and run it again. Save `parameter-count.log`. Pass when the first run fails and names the function, and the second run passes.
- [ ] Lane 6. Plant `def _helper(flag: bool) -> None: ...` in `checkedtables/rows.py` and run the shape test. Save `private-function.log`. Pass when the test passes.
- [ ] Lane 7. Plant a public class `Planted` with a class method `of(cls, flag: bool)` in `checkedtables/pages.py` and run the shape test. Replace the method with `def of(self, a: int, b: int, c: int, d: int)` and run it again. Save `methods.log`. Pass when the first run fails and names `Planted.of`, and the second run passes.
- [ ] Lane 8. Plant a frozen dataclass `Planted` with the field `x: int` in `checkedtables/words.py` and run the shape test. Save `field-snapshot.log`. Pass when `test_kit_dataclass_fields_are_pinned` fails and shows `Planted`.
- [ ] Lane 9. Plant a frozen dataclass `Planted` with the field `flag: bool` in `checkedtables/words.py` and run the shape test. Save `bool-field.log`. Pass when `test_bool_fields_are_page_facts_only` fails and shows `("Planted", "flag")`.
- [ ] Lane 10. Read the `Kit size report` step in the real CI run for the head SHA. Then plant 141 public functions in `checkedtables/__init__.py` and run the report command locally. Save `kit-size-report.log`. Pass when the CI step prints the `0 lines` and `0 public names` line, and the local run prints `141 public names` and exits 0.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Warm wall time in seconds of the six gates, run in sequence. Both sides produce it.
- [ ] Probe. Record `uptime`, warm each side once, then time the sequence five times per side with `time -p`, alternating base and head, each in its own synced worktree. Every command must exit 0, and pytest must print its pass count.
- [ ] Baseline. Record the base median first.
- [ ] Rule. The head fails when its median exceeds the base median by more than 3.0 s, or when its median is 15.0 s or more.

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
- [ ] Create `packages/checkedtables/tests/conftest.py` and `packages/checkedtables/tests/test_isolation.py`.
- [ ] Create `packages/datadesk/tests/core/conftest.py` and `packages/datadesk/tests/core/test_isolation.py`.
- [ ] Create `tests/test_purity.py`.
- [ ] Edit `docs/progress.md`.

**Build.**

- [ ] Add `pytest-socket>=0.8` to the `dev` group and run `uv lock`.
- [ ] Set `addopts = "--import-mode=importlib --disable-socket"` and add `packages/datadesk/tests` to `testpaths` in `pyproject.toml`.
- [ ] Write the autouse fixture `_empty_working_directory` in both `conftest.py` files. It takes `tmp_path` and `monkeypatch` and calls `monkeypatch.chdir(tmp_path)`.
- [ ] Write `test_working_directory_is_empty` and `test_sockets_are_blocked` in both `test_isolation.py` files. The first asserts that `Path.cwd()` holds no entry. The second expects `pytest_socket.SocketBlockedError` from `socket.socket()`.
- [ ] Write `package_sources(name)` in `tests/test_purity.py`, with `PURE_PACKAGES = ("checkedtables", "datadesk.core")`. It finds each package's folder through `importlib.util.find_spec(name).submodule_search_locations`, so the scan does not depend on the working directory.
- [ ] Write `impurity(node)` in `tests/test_purity.py` for the eight names of design section 11.1. It reports a call to `open`, `print` or `input`, a call to `.now()` or `.today()`, an attribute read on `os` or `time`, and any use or import of `random`.
- [ ] Write `test_pure_packages_have_no_effects` in `tests/test_purity.py`. It fails with one `path:line` entry per hit.
- [ ] Add `test_planted_socket_call_fails_pytest` to `tests/test_gates.py`. The clean copy gets a core test, `packages/datadesk/tests/core/test_planted_socket.py`, that only names `socket.socket`. The planted copy gets the same test with the call `socket.socket()`. Assert exit code 1 and the text `SocketBlockedError` for the planted copy.
- [ ] Set the step 1 row of `docs/progress.md` to `check passed`, with the date and the four branch names.
- [ ] Add a note to `docs/progress.md`. `--disable-socket` applies to every test, so a later adapter contract test that needs the network opts in with the `enable_socket` marker of pytest-socket.

**You see.**

- [ ] `uv run pytest` ends with `13 passed`.
- [ ] A core test that calls `socket.socket()` fails with `pytest_socket.SocketBlockedError: A test tried to use socket.socket.`
- [ ] With `print(1)` appended to `packages/checkedtables/src/checkedtables/words.py`, `uv run pytest tests/test_purity.py` fails and names `words.py:1` and `print()`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_gates.py` gains `test_planted_socket_call_fails_pytest`. Run `uv run pytest tests/test_gates.py::test_planted_socket_call_fails_pytest`.
  - [ ] In a scratch copy, remove `--disable-socket` from `addopts`. The planted test fails, and so does `test_sockets_are_blocked`.
- [ ] Both `test_isolation.py` files gain `test_working_directory_is_empty` and `test_sockets_are_blocked`. Run `uv run pytest packages/checkedtables/tests packages/datadesk/tests/core`.
  - [ ] In a scratch copy, delete one `conftest.py`. `test_working_directory_is_empty` fails in that folder.
- [ ] `tests/test_purity.py` gains `test_pure_packages_have_no_effects`. Run `uv run pytest tests/test_purity.py`.
- [ ] The branch log shows the planted test and the isolation tests committed before `--disable-socket` and the fixtures, and failing at that commit.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus high` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run the six gates at the base, which is the S1-C head, and at the head. Add a core test that calls `socket.socket()` on both sides. Save `gates-clean.log`. Pass when the gates exit 0 on both sides before the plant, the planted test passes at the base, which is recorded against the base, and the planted test fails at the head.
- [ ] Lane 2. Push `verify/s1-d-lane-2` with a new `packages/datadesk/tests/core/test_planted_socket.py` that calls `socket.socket()`. Save `ci-socket.log`. Pass when the run fails and the `uv run pytest` step fails with `SocketBlockedError`.
- [ ] Lane 3. Plant three core tests that call `socket.create_connection(("example.com", 80))`, `urllib.request.urlopen("http://example.com")` and `asyncio.run(asyncio.open_connection("example.com", 80))`. Save `socket-routes.log`. Pass when each test fails with `SocketBlockedError`.
- [ ] Lane 4. Plant the `socket.socket()` test in `packages/checkedtables/tests/` and run `uv run pytest`. Save `kit-socket.log`. Pass when the planted test fails with `SocketBlockedError`.
- [ ] Lane 5. Plant a test in each core test folder that writes `out.txt` to the working directory. Run `uv run pytest`, then `git status --porcelain`. Save `empty-cwd.log`. Pass when both tests pass and `git status` lists only the two planted test files.
- [ ] Lane 6. Append `open("x")`, `print(1)` and `input()` to `checkedtables/words.py`, one at a time, and run `uv run pytest tests/test_purity.py` after each. Save `purity-kit.log`. Pass when each run fails and names the file, the line and the call.
- [ ] Lane 7. Append `datetime.now()`, `date.today()`, `time.time()`, `os.getcwd()`, `import random` and `from random import choice` to `datadesk/core/tables/birt.py`, one at a time, and run `uv run pytest tests/test_purity.py` after each. Save `purity-core.log`. Pass when each run fails and names the file and the line.
- [ ] Lane 8. Append `print(1)` and `open("x")` to `datadesk/shell/__init__.py`, then to `phillyledger/api.py`, and run `uv run pytest tests/test_purity.py`. Save `purity-shell.log`. Pass when every run passes.
- [ ] Lane 9. From an empty folder outside the repository, run `uv run --project <repo> pytest -c <repo>/pyproject.toml --rootdir <repo> <repo>/tests/test_purity.py`, then repeat with `print(1)` appended to `checkedtables/words.py`. Save `purity-any-cwd.log`. Pass when the first run passes and the second fails.
- [ ] Lane 10. Append `from os import environ`, `from time import monotonic` and `import os as o` to `datadesk/core/__init__.py`, one at a time, and run `uv run pytest tests/test_purity.py` and `uv run lint-imports` after each. Save `scan-and-contract.log`. Pass when `uv run lint-imports` exits 1 for every plant, whatever the purity scan reports.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Warm wall time in seconds of the six gates, run in sequence. Both sides produce it.
- [ ] Probe. Record `uptime`, warm each side once, then time the sequence five times per side with `time -p`, alternating base and head, each in its own synced worktree. Every command must exit 0, and pytest must print its pass count.
- [ ] Baseline. Record the base median first.
- [ ] Rule. The head fails when its median exceeds the base median by more than 3.0 s, or when its median is 15.0 s or more.

**Review gate.** None. S1-D is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Every Codex finding is confirmed or dropped, and the summary is in the PR's `## Verification` section.
- [ ] Rebased onto the tip of `step-01/c-kit-shape` after the verdict, patch-id unchanged.
- [ ] The root reports S1-D as verified, with its head SHA. The operator lands it after S1-C.

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] The step 1 row of `docs/progress.md` at the S1-D head shows `check passed`, the date and the four branch names.
- [ ] `git -C ../gov-budget-data status --porcelain` still matches `.audit/reference-baseline.txt`.
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
| Which ruff shape scopes the bans and the `D` rules? | One root config with negated `per-file-ignores` globs. | Observed by the delegate. Three `TID251` in core, none in shell. |
| Do `D100` and `D104` fire on empty modules? | Yes, 21 errors in `checkedtables` and `phillyledger`. | Observed by the delegate. |
| Do the existing Python files pass the planned ruff config? | No. `docs/prototype/` and `.claude/hooks/` give 132 errors, and six files would be reformatted. | Run by the root, read-only. |
| What does a socket call in a core test raise? | `pytest_socket.SocketBlockedError: A test tried to use socket.socket.`, exit 1. | Observed by the delegate. |
| Does a planted test read the copy or the installed package? | The copy, only when `PYTHONPATH` names the copy's `src` folders. Without it the planted copy passes both gates. | Observed by the delegate with a negative control. |
| Do the three planted tests pass with sockets disabled? | Yes, in 0.43 s, 1.37 s and 1.34 s. | Rerun. `3 passed in 3.50s`. |
| What does the design's `bool` predicate miss? | `flag: bool \| None` and `flag: Optional[bool]`. | Rerun. Both exit 0. |
| Does the suite pass on Python 3.14? | Yes. | Run by the root on Python 3.14.10. `5 passed`. |
| Does `uv build --all-packages` work? | Yes. Three wheels and three source archives, with no `tests/` path in the `datadesk` wheel. | Run by the root. |

The delegate timed each gate five times, warm, on this Mac. The medians were 3.75 s for
`uv run pytest`, 0.21 s for `uv run lint-imports`, 0.22 s for `uv run prek run --all-files`, and
under 0.1 s each for the two ruff commands and `uv run ty check`. The spread was under 0.2 s for
every gate. The three planted tests took about 3.0 s of the pytest time. The delegate inferred
the limit, which is the start of an inner pytest at about 0.65 s per run. The load average was
18.6 when the root reran the gates, so a quiet machine is likely faster. The budgets in the perf
blocks are guesses with room above these numbers, not measurements.

These stay unproven until the build.

- The GitHub Actions workflow, on a Linux runner. The prototype ran on macOS only.
- The `verify/**` push trigger and `if: ${{ !cancelled() }}` on the gate steps.
- `run_gate` taking its command from `GATES`. The prototype passed the command as a list.
- Python 3.13. The prototype ran 3.12 and 3.14.
- Whether pytest-socket blocks every way to open a connection. The prototype planted
  `socket.socket()` only, and S1-D lane 3 covers the rest.

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
  a pytest hook adds about 3 s to every commit.
- **Build the three guards as siblings on S1-A.** They share `pyproject.toml`, `uv.lock`,
  `ci.yml` and `tests/test_gates.py`, so two owners would write the same files in parallel.
- **Use two or three pull requests.** With four, each clause has one owner and one diff.
- **Commit a test that compares the contracts with the design's block.** Audit 2 of
  `verify-step` reads for that drift on every pull request.

## Appendix C. Risks

- **CI is unproven until the first pull request (S1-A).** The owner watches lanes 2 to 6. A red
  run on a clean head is a finding against `ci.yml`, not against the gates.
- **Claude Code has no control skill for a command line (every PR).** Lanes drive the gates with
  shell commands and return transcripts. The root reads the transcripts, not the lane's summary.
- **The design's shape test passes `flag: bool | None` and `flag: Optional[bool]` (S1-C).**
  `CLAUDE.md` hard rule 5 bans `bool` parameters. S1-C builds the predicate as the design gives
  it. Whether to widen it is the owner's call, and a change goes into design section 11.4 first.
- **The purity scan matches names (S1-D).** It flags a parameter named `time` and a variable
  named `random`. It misses `from os import environ`, which the import contract catches, and
  `builtins.open`, which nothing catches.
- **`../gov-budget-data` already has six uncommitted entries (every PR).** Audit 7 of
  `verify-step` expects an empty status. Audit lane 2 compares with the saved baseline.
- **`verify/**` branches run real CI (every PR).** Each lane deletes its branch. The root lists
  remote branches at Close and removes any that remain.
- **ty and prek are below version 1.0 (S1-A).** The plan pins both. An upgrade is its own change.
- **Verification is large for small diffs (every PR).** The playbook's swarm is 14 verifier runs
  per pull request, 56 for the step, plus four Codex reviews. The operator can cap the lanes at
  the go.

## Appendix D. Links and reading list

Read these before any edit.

- `CLAUDE.md`, all of it.
- `docs/design.md` section 15 step 1, section 11.1, section 11.4, section 12 and section 12.5.
- `docs/principles.md` section 7, the purity checklist.
- `.claude/skills/verify-step/SKILL.md` and `.claude/skills/codex-review/SKILL.md`.
- `../gov-budget-data/pyproject.toml`, `prek.toml` and `.github/workflows/ci.yml`, read-only.

No pull request in this plan needs `<pstack>/skills/how/SKILL.md`. Run
`<pstack>/skills/interrogate/SKILL.md` only if the owner contests the 46 empty modules or the
`bool` predicate. The decision trail is `.audit/step-01.tsv`, kept out of git, per
`<pstack>/skills/show-me-your-work/SKILL.md`.

## Appendix E. Codex review

Not run yet. `codex-review` reviews a committed HEAD, and this plan was untracked when it was
written. After the plan is committed, run `/codex-review plan 1` and record here each finding
that is kept, with the revision it led to, and each finding that is dropped, with the reason.
