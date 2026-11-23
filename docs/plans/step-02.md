# Build step 2 plan

Build step 2 of `docs/design.md` section 15 builds the part of `checkedtables` that turns the
words of a page into lines and typed cells. It ships no parser and publishes nothing. The work is
for the owner, who lands each pull request, and for the agents that build steps 3 to 14 on these
types. The plan enforces one rule. Each clause of the step's check belongs to exactly one pull
request, and a named test proves the clause. The pull requests stack in the order S2-A, S2-B,
S2-C, S2-D, S2-E.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `<pstack>/skills/poteto-mode/playbooks/autopilot-stack.md`. `<pstack>` is the
installed pstack plugin folder, the one that holds `skills/` and `docs/`. The operator decides
every landing (`CLAUDE.md`, hard rule 9), so all five pull requests stop at verified.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

This repository's rules add to the playbook, and the repository's rule wins where the two differ
(`CLAUDE.md`, "How work runs here"). The differences are these.

- Verification is the `verify-step` skill. Every swarm lane reads it.
- Verification is sized by what there is to prove (`docs/plans/README.md`). A pull request gets
  one live lane for each clause it owns and each risk this plan names. Every other lane and every
  perf box says "Not used", and no agent runs for it. The design names no time budget for step 2.
- What a lane drives is a command line. A lane saves a transcript as a `.log` file in place of a
  screenshot.
- Each lane runs in its own git worktree on this machine. Claude Code has no cloud agents.
- After the swarm, Codex reviews each pull request with the `codex-review` skill, and the root
  confirms or drops each finding. This repository has no Bugbot.
- "Trunk" is `main` for S2-A. For a stacked child, the base that a lane compares against is the
  head of the parent pull request.

Each clause of the step 2 check has one owner. The first sentence of the check names suites, so
the table splits it by suite. Design section 11.2 lists three properties that the step 2 modules
can run. The line grouping property is C1a, and the two lexer properties are C1b.

| Clause | Text in design section 15 | Owner | Named proof |
|---|---|---|---|
| C1a | Hypothesis suites pass, line grouping | S2-C | `test_every_word_lands_in_exactly_one_line` |
| C1b | Hypothesis suites pass, lexer | S2-D | `test_lexer_round_trip` and `test_amount_digits_are_the_digits_of_its_words` |
| C2 | The 55 probe inputs of VAL section 3.2 give the documented new results | S2-D | `test_val_probe_inputs_give_documented_results` and `test_val_probe_table_is_the_dossier_table` |
| C3 | `transliteration_ok` refuses "65.8" to "85.8" and "77,500,000" to "7,500,000" | S2-D | `test_transliteration_refuses_a_digit_swap` |

S2-A, S2-B and S2-E own no clause. S2-A delivers the owner's decision to pin the imports of the
pure packages (`docs/progress.md`, "The pure packages can still reach effects the gates do not
name"). S2-B and S2-E build modules that the step lists and the check does not name.

Clause C2 could not be proven as the design writes it, and the owner settled it. VAL section
3.2 says the probe ran on 55 inputs and prints 16 of them, with the old results only. No file in
this repository or in `../gov-budget-data` holds the other 39 inputs or any new result
(Appendix A). An agent does not reword a check (`CLAUDE.md`, hard rule 2), and a set that an
agent picks is not the set the check names. So the plan put two choices to the owner, to supply
the original inputs or to decide that Appendix E is the acceptance set.

On November 23, 2026 the owner decided, in these words, "[u]se your list, but make row 4
unreadable." Appendix E is the acceptance set for C2, with row 4 changed. It holds the 16 printed
inputs and 39 more that the dossier prints as examples in sections 1.3, 2 and 3.1. S2-D records
the decision as decision 12 of design section 16 and adds "(decision 12)" after the clause in
section 15. It adds the table to VAL as a new section 3.2.1, which says that the 39 inputs were
chosen and not recovered. The dossier's own table in section 3.2 stays as it is.

Row 4 is `12, 345`. The first draft joined it as 12,345 through a third join shape, tokens that
end in a comma. A rule that refuses `12, 345` and still joins `10, 936, 234` would have to count
tokens, and nothing on a page supports that. So the decision removes the shape. A cell printed with spaces after its commas is `Unreadable` and needs a
reviewed reading (Appendix C).

Five pull requests change `docs/design.md`. Each change is also an entry under Deviations in
`docs/progress.md`, in the same pull request. The owner can refuse any of them at the go.

- S2-A adds the import pin to section 11.1.
- S2-B changes the lists of steps 2 and 5 in section 15. `lex_cell` takes a `ColumnSpec`, and
  `records` takes `RowKey` and returns `Finding`. Those types live in `columns` and `table`,
  which step 2 does not list, and no step lists `table` at all. Step 2 gains `NumberFormat`,
  `ColumnSpec`, `RowKey`, `Severity` and `Finding`. Step 5 gains the rest of `table`.
- S2-B gives `WordRef` and `Finding` an ordering that puts `None` first in section 2.1. The
  design's `order=True` raises `TypeError` when one side holds `None` and the other an `int`
  (Appendix A).
- S2-C states four rules in section 3.1 that the design leaves open. They are the order
  `group_lines` takes words in, what a value word is, what `split_line_prefix` returns for a line
  of only prefix words, and what `lines_text` returns. It also adds one mark form to
  `parse_label`, a bare digit after a word, which ENT-Q07 documents and the design's list omits.
- S2-D replaces the one-sentence kerning rule of `lex_cell` in section 3.1 with the two join
  shapes of Appendix E, and records the owner's decision on clause C2 in sections 15 and 16.
- S2-E gives `reading_for` the page's words in place of the page number and states its finding
  codes.

Every design line number in this plan is a line of `docs/design.md` at commit `18cb167`, the
`main` this plan was written on. S2-A and S2-B add lines to the design, so a later owner finds a
block by its file comment, such as `# checkedtables/lex.py`.

## Program checklist

### Arm the program

The evidence for each box in this section is a row in the decision trail.

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on the operator's explicit go.
- [ ] Copy the operator's decision on clause C2 into the decision trail, word for word, from "How to read this". It is made, so no pull request waits on the operator before its parent is code-ready.
- [ ] Confirm the operator's preconditions before any owner starts. Agents never push to `main` (`CLAUDE.md`, hard rule 9).
  - [ ] `git rev-parse --abbrev-ref HEAD` prints `main`, and `git status --porcelain` prints nothing.
  - [ ] `git ls-remote origin main` prints the SHA that `git rev-parse main` prints.
  - [ ] `git show origin/main:docs/plans/step-02.md` prints this plan, with the revisions of Appendix G.
  - [ ] `gh auth status` lists the `repo` scope. The command masks the token.
- [ ] Start the decision trail at `.audit/step-02.tsv` per `<pstack>/skills/show-me-your-work/SKILL.md`.
- [ ] Save the reference snapshot as `<root>/.audit/reference-baseline.txt`, where `<root>` is the absolute path of the root's checkout. The snapshot is the output of the commands below this list. Give every lane both absolute paths.
- [ ] Read these from trunk at program start. Re-read them at every tick.
  - [ ] `git show origin/main:CLAUDE.md`
  - [ ] `git show origin/main:docs/plans/step-02.md`
  - [ ] `git show origin/main:docs/plans/README.md`
  - [ ] `git show origin/main:.claude/skills/verify-step/SKILL.md`
  - [ ] `git show origin/main:.claude/skills/codex-review/SKILL.md`
  - [ ] `git show origin/main:.claude/skills/deslop/SKILL.md`
- [ ] Read these from the installed pstack plugin. They are not in this repository.
  - [ ] `<pstack>/docs/harness/claude-code.md`
  - [ ] `<pstack>/skills/poteto-mode/playbooks/autopilot-stack.md` and `autopilot-full.md`
  - [ ] `<pstack>/skills/poteto-mode/playbooks/opening-a-pr.md` and `shipping.md`
  - [ ] `<pstack>/skills/swarm/SKILL.md` and `<pstack>/skills/no-comments/SKILL.md`
- [ ] On the operator's go, arm the audit tick as `/loop 1h` with the tick prompt below. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read `<pstack>/skills/poteto-mode/playbooks/autopilot-stack.md`, and re-read `docs/plans/step-02.md` and `CLAUDE.md` from trunk. Audit the operation against them and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then post a short status message to the operator in chat only when the audit found a tracked change that no earlier status message reported, such as a PR opened, a code-ready head, a round launched or closed, a verdict, a stuck agent and the action taken, a blocker added or cleared, or a decision only the operator can make. Name every such change and nothing else. Do not repeat a table or an unchanged blocker. If the audit found none, end the turn with no reply text. Either way, log this tick's row in your decision trail. The row names the items reported, or none."
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

Step 2 needs no R2 and no Textract credentials. It reads no PDF and spends no money.

### Spawn owners

- [ ] Spawn one owner per PR with the lifecycle that `autopilot-full.md` step 2 names, without the merge. Each owner is a fresh `pstack:poteto-agent` on the `feature, refactoring` line of `~/.claude/rules/pstack-models.md`, in its own git worktree.
- [ ] Write each owner a brief that stands alone.
  - [ ] It restates the user's goal in one sentence.
  - [ ] It names the PR's section of this plan by heading, and gives the absolute path of `<pstack>/skills/poteto-mode/SKILL.md`.
  - [ ] It names the design lines the PR builds from, as the PR's section lists them. The owner reads them and never works from memory of the design.
  - [ ] It lists the rules that bind the owner. Write the tests first and commit them failing. Never weaken a check. Keep the names and signatures the design gives. Never write under `../gov-budget-data`. Never push to `main`. Never merge.
- [ ] Follow this dependency graph. Each child is based on its parent's branch, because each child imports modules or extends pins that its parent creates.
  - [ ] S2-A is first. It branches from `main` as `step-02/a-import-pin`.
  - [ ] S2-B after S2-A, as `step-02/b-value-types`. It adds the first pairs to the pin that S2-A creates.
  - [ ] S2-C after S2-B, as `step-02/c-words-to-lines`. It builds on the types of S2-B.
  - [ ] S2-D after S2-C, as `step-02/d-lexer`. Its tests build pages with `page_from_text` of S2-C, and one property ties `lex_cell` to `has_values` of S2-C.
  - [ ] S2-E after S2-D, as `step-02/e-records`. `apply_reading` calls `transliteration_ok` of S2-D.
- [ ] Start a child only after its parent reports a code-ready head.
- [ ] Hold the file boundaries. Paths under `src/` are in `packages/checkedtables/src/checkedtables/`, and paths under `tests/kit/` stand for `packages/checkedtables/tests/`.
  - [ ] S2-A touches only `tests/test_purity.py`, `tests/test_gates.py`, and section 11.1 of `docs/design.md`.
  - [ ] S2-B touches only `refs.py`, `kinds.py`, `words.py`, `labels.py`, `cells.py`, `table.py` and `columns.py` under `src/`, the four new test files under `tests/kit/`, `tests/kit/test_library_shape.py`, `tests/test_purity.py`, `tests/test_workspace.py`, `tests/test_gates.py`, the root `conftest.py`, `pyproject.toml`, `uv.lock`, and sections 2.1, 11.1 and 15 of `docs/design.md`.
  - [ ] S2-C touches only `testing.py`, `text.py` and `lines.py` under `src/`, the three new test files under `tests/kit/`, `tests/kit/test_library_shape.py`, `tests/test_purity.py`, and sections 3.1 and 11.1 of `docs/design.md`.
  - [ ] S2-D touches only `lex.py` under `src/`, the two new test files under `tests/kit/`, `tests/test_evidence.py`, `tests/test_purity.py`, sections 3.1, 11.1, 15 and 16 of `docs/design.md`, and a new section 3.2.1 of `docs/evidence/dossiers/VAL.md`.
  - [ ] S2-E touches only `records.py` under `src/`, one new test file under `tests/kit/`, `tests/kit/test_library_shape.py`, `tests/test_purity.py`, and sections 3.1 and 11.1 of `docs/design.md`.
  - [ ] Every PR may also edit `docs/progress.md`. A PR edits `docs/plans/step-02.md` when the build shows this plan wrong.
  - [ ] No PR touches `packages/checkedtables/src/checkedtables/__init__.py`, `docs/evidence/coverage.tsv`, `docs/prototype/`, `.claude/`, `CLAUDE.md`, `.github/workflows/ci.yml` or anything under `../gov-budget-data`.
- [ ] Hold the review gate. No PR in this plan changes an interaction, so none is review-gated. Every PR still stops at verified and waits for the operator to land it.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Run `command -v origin`. When it fails, use `gh` for every PR operation and record the fallback. Never require `gt`.
- [ ] Open the PR ready, never draft, with `gh pr create --base <base-branch>`. S2-A targets `main`. A stack child targets its parent branch. Write the title as `type(scope): subject`.
- [ ] Write the PR body per `opening-a-pr.md`. Open `## Why` with the user's goal. Put the Codex summary and the line that the `Kit size report` step prints under `## Verification`.
- [ ] Write a numpy docstring on every public class, method and function under `packages/checkedtables/src`. Ruff's `D` rules fail the build without them, and `D105` asks for one on `__post_init__`, `__str__` and each comparison method too (Appendix A). Write no other comment, except one that cites a dossier quirk id.
- [ ] Run the repo's lint and typecheck once before the PR-facing push, with all six gates of `tests/test_gates.py`. Push with hooks on.
- [ ] Run `/deslop` from `.claude/skills/deslop/` before each commit and `/no-comments` before review.
- [ ] Rebase before the code-ready report. S2-A rebases onto current `main`. A child rebases onto the tip of its parent branch. Keep that merge base in fix rounds. Rebase again only on a `git merge-tree` conflict with the base, on a CI failure that comes from the base, or when the parent gets a new head.
- [ ] Report the code-ready head SHA to the root, then every later head.
- [ ] Say so in `docs/progress.md` when a module runs well past its estimate in design section 12.1.

This repository has no Bugbot. The Codex review in the next section takes its place.

### Verdict and merge, for every PR

- [ ] A full swarm runs once, at the code-ready head. Another full swarm runs only for new behavior, a redesign, or a large new diff. A rebase, a merge-conflict resolution, or a minor fix gets a single verifier at the new head, and a wording-only change gets none. Run each full swarm per `<pstack>/skills/swarm/SKILL.md`, with `general-purpose` workers in their own worktrees on the `swarm workers` line of `~/.claude/rules/pstack-models.md`.
  - [ ] The gates lane runs the Gates section of `verify-step`, and reads the `CI` run for the head SHA on Python 3.12 and 3.14.
  - [ ] The check lane runs the check section of `verify-step` for each clause the PR owns. It breaks the code the clause describes in a scratch copy and shows the named test fail. For a PR that owns no clause it runs the scratch-copy boxes of the PR's unit block.
  - [ ] The audit lane runs audits 1 to 7 of `verify-step` on the diff and distrusts the PR body. For audit 6 it checks that each quirk Appendix F gives the PR has a test whose name or comment carries the quirk id. For audit 7 it runs the reference snapshot commands and compares the output with `<root>/.audit/reference-baseline.txt`. It reports a difference to the operator and changes nothing in the reference.
  - [ ] One live lane runs for each lane the PR's live block fills. A lane that says "Not used" gets no agent, and no perf lane runs.
  - [ ] Every lane reports `PASS`, `ISSUES` or `BLOCKED`, with the head SHA and its transcript paths.
- [ ] The root audits the receipts in the merge-ready report before the verdict.
- [ ] Judge every finding by the blocking rule in `autopilot-full.md` step 4. The verdict is clean when none blocks. A failure on base behavior in a lane marked `Regression lane against trunk.` is recorded against the base and does not block the PR. A new head gets a fresh verdict, except for results that stay valid under the patch-id rule in `shipping.md`.
- [ ] After a clean swarm verdict, run the Codex review in a clean checkout held at the PR head. The script reviews the `HEAD` of the checkout it runs in and finds the reference beside that checkout.
  - [ ] Run `git worktree add --detach ../phillyledger-review-<pr-id> <head SHA>` from the root's checkout. The new folder sits beside the root's checkout, so `../gov-budget-data` resolves from it.
  - [ ] Run `.claude/skills/codex-review/run.sh pr 2 <base-branch>` in that folder, in the background. Change nothing in the folder until the run ends.
  - [ ] Check that the report's file name carries the first eight characters of the PR head SHA. Copy the report into the root's `.codex-review/`, then run `git worktree remove ../phillyledger-review-<pr-id>`.
- [ ] Confirm or drop each finding by a rerun of its command or a read of its quoted lines. Give each kept `blocks` or `should fix` finding to a fresh owner with the finding, its evidence and the original brief. Then run one `verify-step` verifier and the Codex review on the new head.
- [ ] The root reads the whole diff and writes its own summary. It does not pass through an owner's report.
- [ ] Stop at verified. Report each PR with its verdict and its head SHA. After the handoff, nobody pushes without the operator's go. The operator lands the stack bottom-up, or tells an agent to merge one named PR in that session (`CLAUDE.md`, hard rule 9). When a parent lands, its child moves onto `main` per `shipping.md` step 4, and the child's verdict stands when `git patch-id` is unchanged.

### Boot recipe, for every live lane

Each live lane runs in its own git worktree on this machine at the PR head. Claude Code has no
`control-cli` skill, so a lane drives the command line with shell commands and saves the
transcript.

- [ ] `git fetch origin <head-branch> && git checkout <head SHA>`.
- [ ] Run `uv sync --locked` and wait for exit code 0.
- [ ] Deliver input only as the shell commands that the lane names. The read-only diagnostics are `git status`, `uv tree`, `uv run python -V` and `gh run view`.
- [ ] Write a lane's own script in the lane's scratch folder, outside the worktree, and run it with `uv run python` from the worktree. A lane script imports only `checkedtables` and the standard library. It never imports the PR's tests, so it is a second reading of the design and not a rerun of the owner's.
- [ ] For a plant, edit the file that the lane names, in the lane's own worktree. Never commit a plant to the PR branch.
- [ ] To run the old lexer, copy `<reference>/packages/gov-budget-etl/src/gov_budget_etl/tables/amounts.py` into the lane's scratch folder, confirm the copy with `cmp`, and load the copy by path with `python -I`. Never run code inside `<reference>`.
- [ ] Never run `prek install` in a worktree. Linked worktrees share one hooks folder, so the hook would reach every other lane and the operator's checkout.
- [ ] Save every transcript to `/tmp/swarm-<pr-id>/worker-<n>/<slug>.log` and return the paths with the report.

## Pin the imports of the pure packages (S2-A)

**Depends on.** None. S2-A branches from `main`. It owns no clause. It delivers the owner's allow-list decision.

**Files.**

- [ ] Edit `tests/test_purity.py`.
- [ ] Edit `tests/test_gates.py`.
- [ ] Edit `docs/design.md` section 11.1, and `docs/progress.md`.

**Build.**

- [ ] Add `PURE_IMPORTS` to `tests/test_purity.py`. It maps each name in `PURE_PACKAGES` to a sorted tuple of `module.name` strings, one for each name the package imports from outside. Both tuples are empty at this head, because every file in both packages is empty (Appendix A).
- [ ] Add `INSIDE`. `checkedtables` counts `checkedtables` as inside. `datadesk.core` counts `datadesk.core` and `checkedtables` as inside. An import of a module at or under an inside name is never pinned. Resolve a relative import against the package of the module that holds it, then judge it the same way. `from . import refs` in `checkedtables/words.py` is inside. `from ... import shell` in `datadesk/core/tables/birt.py` names `datadesk.shell` and is outside.
- [ ] Write `outside_imports(tree, module)`, where `module` is the dotted name of the file being read. It returns the line and the `module.name` string of every name that a `from module import name` statement takes from an outside module. It walks every node, so it reads function bodies and `if TYPE_CHECKING` blocks.
- [ ] Give `impurities` the same `module` parameter. Make it also report an `import` statement that binds an outside module, in any spelling, a star import from an outside module, and an outside pair that `PURE_IMPORTS[package]` does not hold. `import datadesk.core.tables` names an inside module and binds `datadesk`, so it fails, and `import datadesk.core.tables as tables` passes.
- [ ] Delete `BANNED_IMPORTS` and its two cases in `effect`. The pin refuses `random` and `builtins` with every other module.
- [ ] Write `test_pure_imports_are_pinned`. For each pure package, the sorted pairs that `outside_imports` finds over `package_sources` equal `PURE_IMPORTS[package]`. A pinned pair that no file imports fails the test too.
- [ ] Write `module_valued(pairs)` and `test_pinned_imports_are_not_modules`. `module_valued` returns each pair that does not resolve, or that resolves to a module. The test first asserts that `module_valued` returns `dataclasses.sys`, `statistics.random` and `re.no_such_name`, which does not resolve, and does not return `dataclasses.dataclass`. Then it asserts that no pinned pair is module valued.
- [ ] Add these single-statement forms to `BANNED_FORMS`. `import sys`, `import os.path as p`, `import dataclasses`, `from io import FileIO`, `from collections import defaultdict`, `from dataclasses import sys`, `from re import *`, a `from uuid import uuid4` inside a function body, and a `from pathlib import Path` under `if TYPE_CHECKING`. Add `from ... import shell`, `from ...shell import run` and `import datadesk.core.tables`, read as `datadesk.core.tables.birt`.
- [ ] Change the `try` form in `BANNED_FORMS` so that `pass` stands where `import tomllib` stood. The form tests mutable state under `try`, and the import would now be a second hit.
- [ ] Add to `ALLOWED_FORMS`, read as `checkedtables.words`, the forms `from checkedtables.refs import Box`, `import checkedtables.lines` and `from . import refs`. Add `from . import catalog`, `from checkedtables.refs import Box` and `import datadesk.core.tables as tables`, read as `datadesk.core.tables.birt`.
- [ ] Add `test_planted_import_fails_purity_test` to `tests/test_gates.py`. It plants `from io import FileIO` at the end of `packages/datadesk/src/datadesk/core/tables/birt.py`, puts a copy of `tests/test_purity.py` in the workspace, runs the `uv run pytest` gate on that copy through `clean_then_planted`, and asserts exit code 1 and one output line that holds both `birt.py:` and `from io import FileIO`. The helper appends the plant, so the assertion names no line number.
- [ ] Add the import rule to the Purity row of design section 11.1, and the paragraph that Appendix D quotes. The closed list of modules is empty for both packages at this head.
- [ ] Add a Deviations entry to `docs/progress.md`. Rewrite the note "The pure packages can still reach effects the gates do not name" to say which of its ten plants now fail and which three still pass.

**You see.**

- [ ] `uv run pytest tests/test_purity.py` ends with `5 passed`.
- [ ] With `from io import FileIO` appended to `datadesk/core/tables/birt.py`, the same command fails and prints a line that holds `birt.py:` and `from io import FileIO`.
- [ ] `uv run pytest` exits 0, and `uv run lint-imports` prints `Contracts: 8 kept, 0 broken.`

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_purity.py` gains `test_pure_imports_are_pinned` and `test_pinned_imports_are_not_modules`, and `test_scan_reports_each_banned_form` and `test_scan_allows_immutable_constants` read the new forms. Run `uv run pytest tests/test_purity.py`.
  - [ ] In a scratch copy, add `"dataclasses.dataclass"` to `PURE_IMPORTS["checkedtables"]` with no import behind it. `test_pure_imports_are_pinned` fails.
  - [ ] In a scratch copy, make `outside_imports` skip function bodies. `test_scan_reports_each_banned_form` fails on the `from uuid import uuid4` form, which only that function collects.
  - [ ] In a scratch copy, make the scan treat every relative import as inside. `test_scan_reports_each_banned_form` fails on `from ... import shell`.
- [ ] `tests/test_gates.py` gains `test_planted_import_fails_purity_test`. Run `uv run pytest tests/test_gates.py -k purity`.
- [ ] The branch log shows the new forms and the planted test committed before the scan changes, and failing at that commit.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus high` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Plant the ten forms of the note in `docs/progress.md`, one at a time, in `datadesk/core/tables/birt.py`, and run the six gates at `main` and at the head. Save `ten-plants.log`. Pass when all ten pass every gate at `main`, and at the head `uv run pytest` fails for the seven that import (`io`, `sys` twice, `uuid`, `posix`, `_socket` and `collections`) and passes for `write = print`, `exec` and the mutable class attribute.
- [ ] Lane 2. Plant, one at a time in `checkedtables/words.py`, `import dataclasses` with `dataclasses.sys.stdout.write("x")`, `import enum` with `enum.bltns.open("x")`, `from dataclasses import sys`, `from statistics import random`, and `from functools import cache`. Then plant `from ... import shell` in `datadesk/core/tables/birt.py`. Run `uv run pytest tests/test_purity.py` after each. Save `reexports.log`. Pass when all six runs fail and name the planted line.
- [ ] Lane 3. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 4. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 5. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 6. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 7. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 8. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 9. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 10. Not used. Save `none`. Pass when no agent runs for this lane.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not used. The design names no time or size budget for this pull request.
- [ ] Probe. Not used. No probe runs.
- [ ] Baseline. Not used. No baseline is recorded.
- [ ] Rule. Not used. No number fails this pull request.

**Review gate.** None. S2-A is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Every Codex finding is confirmed or dropped, and the summary is in the PR's `## Verification` section.
- [ ] Rebased onto current `main` after the verdict, patch-id unchanged.
- [ ] The root reports S2-A as verified, with its head SHA. The operator lands it first.

## Build the kit's value types (S2-B)

**Depends on.** S2-A. The base is `step-02/a-import-pin`. S2-B owns no clause. It builds `refs`, `kinds`, `words`, `labels` and `cells`, and the five types that S2-D and S2-E take from `columns` and `table`.

**Files.**

- [ ] Create `refs.py`, `kinds.py`, `labels.py`, `cells.py` and `table.py` in `packages/checkedtables/src/checkedtables/`.
- [ ] Edit `words.py` and `columns.py` in that folder. Both are empty files today.
- [ ] Create `test_refs.py`, `test_words.py`, `test_cells.py` and `test_table.py` in `packages/checkedtables/tests/`.
- [ ] Edit `packages/checkedtables/tests/test_library_shape.py`, `tests/test_purity.py`, `tests/test_workspace.py`, `tests/test_gates.py` and the root `conftest.py`.
- [ ] Edit `pyproject.toml` and `uv.lock`.
- [ ] Edit `docs/design.md` sections 2.1, 11.1 and 15, and `docs/progress.md`.

**Build.**

- [ ] Add `hypothesis` to the `dev` group in `pyproject.toml` and run `uv lock`. Design section 12.5 already forbids `checkedtables` to import it, so strategies live in test files.
- [ ] Register one Hypothesis profile in the root `conftest.py` with `database=None`, `derandomize=True` and `deadline=None`, and load it. A derandomized run gives the same examples on every machine.
- [ ] In the same file, point Hypothesis at a temporary folder with `hypothesis.configuration.set_hypothesis_home_dir` before any test runs, and remove the folder when the session ends. With the profile alone, Hypothesis 6.170.15 still writes `.hypothesis/constants` into the working folder (Appendix A), and the core tests must leave their folder empty.
- [ ] Write `Box` and `WordRef` in `refs.py` from design lines 84 to 107. `Box.around` raises `ValueError` for no boxes.
- [ ] Order `WordRef` by its four fields with `None` before every `int` in `child`, through written comparison methods. Change line 102 of the design to say so.
- [ ] Write the five `StrEnum` classes of `kinds.py` from design lines 110 to 138.
- [ ] Write `WordSource`, `Word`, `Rule`, `Page` and `Document` in `words.py` from design lines 142 to 186. `Document.page` raises `KeyError` for a page the document does not hold.
- [ ] Write `Label` in `labels.py` from design lines 236 to 244.
- [ ] Write `Reading`, the six cell classes and the `Cell` union in `cells.py` from design lines 335 to 391.
- [ ] Write `Severity`, `Finding` and `RowKey` in `table.py` from design lines 422 to 449, and nothing else of that module. Order `Finding` with `None` before every `int` in `page`.
- [ ] Make `RowKey.of` sort its parts by name, and make `RowKey` raise `ValueError` for names that are not strictly ascending, for an empty name, and for a name or value that holds `|` or `=`. `RowKey.parse` is the inverse of `str`.
- [ ] Write `NumberFormat` and `ColumnSpec` in `columns.py` from design lines 249 to 262, and nothing else of that module.
- [ ] Add every new dataclass to `FIELD_SNAPSHOT` in the commit that creates it, and change the expected value of `test_bool_fields_are_page_facts_only` to `{("Word", "bold")}`.
- [ ] Pin each pair the new modules import in `PURE_IMPORTS["checkedtables"]`, and list each module in design section 11.1. The plan expects `collections.abc`, `dataclasses`, `decimal` and `enum`.
- [ ] Change design section 15. Step 2 gains "the `NumberFormat` and `ColumnSpec` types of `columns`, and the `RowKey`, `Severity` and `Finding` types of `table`". Step 5 gains `table`. Add both, and the two orderings, under Deviations in `docs/progress.md`.

**You see.**

- [ ] `uv run pytest packages/checkedtables/tests` exits 0 and its last line counts no failure.
- [ ] `uv run python packages/checkedtables/tests/test_library_shape.py` prints a line count above zero and `0 public names`.
- [ ] `uv run lint-imports` prints `Contracts: 8 kept, 0 broken.`

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_refs.py` gains `test_inverted_box_raises`, `test_box_around_holds_every_box` as a Hypothesis property, `test_box_around_nothing_raises` and `test_word_refs_sort_with_and_without_child` as a Hypothesis property. Run `uv run pytest packages/checkedtables/tests/test_refs.py`.
- [ ] `test_words.py` gains `test_page_refuses_a_word_from_another_page`, `test_page_refuses_a_word_from_another_document`, `test_document_page_returns_the_page` and `test_word_source_keeps_the_tool_string` for VAL-Q07. Run `uv run pytest packages/checkedtables/tests/test_words.py`.
- [ ] `test_cells.py` gains `test_amount_needs_words` and `test_reviewed_amount_names_its_review_and_only_then`. Run `uv run pytest packages/checkedtables/tests/test_cells.py`.
- [ ] `test_table.py` gains `test_row_key_parse_inverts_str` and `test_findings_sort_with_and_without_page` as Hypothesis properties, and `test_row_key_refuses_unsorted_names` and `test_row_key_has_occurrence`. Run `uv run pytest packages/checkedtables/tests/test_table.py`.
- [ ] `tests/test_workspace.py` gains `test_hypothesis_profile_is_derandomized`. It asserts that the loaded settings have `derandomize` and `database is None`. Run `uv run pytest tests/test_workspace.py`.
- [ ] `tests/test_gates.py` gains `test_hypothesis_writes_nothing_in_the_workspace`. It plants a property test and a copy of `test_working_directory_is_empty` in one new file under `packages/checkedtables/tests/` of a workspace copy, runs the `uv run pytest` gate on that file, and asserts exit code 0 and that no `.hypothesis` folder exists anywhere under the workspace. Run `uv run pytest tests/test_gates.py -k hypothesis`.
  - [ ] In a scratch copy, remove the `set_hypothesis_home_dir` call. The test fails.
- [ ] The shape and purity tests pass with the new pins. Run `uv run pytest packages/checkedtables/tests/test_library_shape.py tests/test_purity.py`.
  - [ ] In a scratch copy, put `order=True` back on `WordRef`. `test_word_refs_sort_with_and_without_child` fails with `TypeError`.
- [ ] The branch log shows each test file committed before its module, and failing at that commit.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus high` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run the six gates at the base, which is the S2-A head, and at the head. Record that the base has no kit types. Then run a lane script that builds each state the design lists under "What these make impossible" at lines 189 to 194 and 394 to 399 and that a constructor can refuse. They are an inverted `Box`, a `Page` with a word of another page, an `Amount` with no words, and a reviewed `Amount` with no review id. Save `illegal-states.log`. Pass when every gate exits 0 on both sides and each of the four raises `ValueError`.
- [ ] Lane 2. Delete any `.hypothesis` folder in the worktree. Run `uv run pytest --basetemp=<lane folder>/tmp -p no:cacheprovider`, then search the worktree and the lane folder for a `.hypothesis` folder, and print the Hypothesis version from `uv.lock`. Save `hypothesis-writes-nothing.log`. Pass when pytest exits 0 and the search prints nothing.
- [ ] Lane 3. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 4. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 5. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 6. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 7. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 8. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 9. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 10. Not used. Save `none`. Pass when no agent runs for this lane.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not used. The design names no time or size budget for this pull request.
- [ ] Probe. Not used. No probe runs.
- [ ] Baseline. Not used. No baseline is recorded.
- [ ] Rule. Not used. No number fails this pull request.

**Review gate.** None. S2-B is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Every Codex finding is confirmed or dropped, and the summary is in the PR's `## Verification` section.
- [ ] Rebased onto the tip of `step-02/a-import-pin` after the verdict, patch-id unchanged.
- [ ] The root reports S2-B as verified, with its head SHA. The operator lands it after S2-A.

## Group words into lines and read labels (S2-C)

**Depends on.** S2-B. The base is `step-02/b-value-types`. S2-C owns clause C1a. It builds `testing`, `text` and `lines`.

**Files.**

- [ ] Edit `testing.py`, `text.py` and `lines.py` in `packages/checkedtables/src/checkedtables/`. All three are empty files today.
- [ ] Create `test_testing.py`, `test_text.py` and `test_lines.py` in `packages/checkedtables/tests/`.
- [ ] Edit `packages/checkedtables/tests/test_library_shape.py` and `tests/test_purity.py`.
- [ ] Edit `docs/design.md` sections 3.1 and 11.1, and `docs/progress.md`.

**Build.**

- [ ] Write `page_from_text` in `testing.py` from design lines 1783 to 1786. A word is a run of characters with no space. Character column `c` of text line `r` starts at `x0 = 6c` and `top = 12r`, and a word's box is 12 points tall. Remove the `**` markers before layout. A marked word has `bold=True` and every other word `bold=False`, and each word has `size=12.0` and `confidence=None`. The page is as wide as its longest line and as tall as its lines, with rotation 0, and `WordRef.index` counts the words in reading order from 0.
- [ ] Make a block whose first line is `#ocr` drop that line and give every word `bold=None`, `size=None`, `confidence=100.0` and a `WordSource` of kind `OCR`.
- [ ] Write `doc_of` in `testing.py` from design line 1787. It sorts the pages by number and raises `ValueError` for no pages, for two hashes and for a repeated page number. Design section 12.1 puts it in this module and no step names it.
- [ ] Write `normalize_space`, `normalize_label` and `squash` in `text.py` from design lines 1611 to 1616. `normalize_space` turns every Unicode space into a plain space and U+2010 and U+2011 into `-`, removes the spaces around a hyphen that sits between two letters, and collapses runs. `normalize_label` replaces punctuation with a space, as `entities.py:95` of the old code does, and keeps a comma or a point that sits between two digits.
- [ ] Write `parse_label` from design lines 1617 to 1619. It takes marks off the end of the label until none is left and keeps them in print order. The mark forms are the nine of the label table in Appendix F. Eight are the design's, and the ninth, a bare digit after a word, comes from ENT-Q07 and `entities.py:54-61` of the old code.
- [ ] Write `split_line_prefix` from design lines 1620 to 1622. It takes every leading word that fullmatches the pattern. When every word matches, the line it returns has no words and keeps its box. The prefix words stay as evidence, and no value word is left to seed a lane. Name `Line` in `text.py` only under `TYPE_CHECKING`, and build the new line with `dataclasses.replace`, because `lines.py` imports `normalize_space` from `text.py` (Appendix A).
- [ ] Write `Line` and `PageLines` in `lines.py` from design lines 197 to 212.
- [ ] Write `group_lines` from design lines 1626 to 1628. Take the words in order of bottom, then `x0`, then `ref`. The first word opens a line. A later word joins the open line when its bottom is within 0.35 of the page's median word height of the bottom of the word that opened the line, and it opens a new line otherwise. Sort a line's words by `x0` and the lines by top.
- [ ] Write `page_lines` and `lines_text`. `lines_text` joins the lines' `text` with a newline.
- [ ] Write `has_values`. A line has values when its last word that is not a mark word is a value word. A mark word is one or more of `*`, `†`, `‡`, `§`, `#`, a backtick and the Unicode superscript digits, with nothing else. A value word is `N/A`, `NA`, a dash placeholder (`-`, `--`, an en dash or an em dash), or a text that holds a digit and otherwise only `,`, `.`, `$`, `%`, parentheses, a minus glyph and trailing marks. Keep the predicate private to `lines.py`.
- [ ] State the four rules and the ninth mark form in the comments of design section 3.1, and record them under Deviations in `docs/progress.md`.
- [ ] Add `Line` and `PageLines` to `FIELD_SNAPSHOT`, pin the new import pairs, and list any new module in design section 11.1.

**You see.**

- [ ] `uv run pytest packages/checkedtables/tests/test_lines.py -k exactly_one_line` ends with `1 passed`.
- [ ] `uv run pytest packages/checkedtables/tests` exits 0.
- [ ] `uv run python -c "import checkedtables.text"` and `uv run python -c "import checkedtables.lines"` both exit 0.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_lines.py` gains the Hypothesis properties `test_every_word_lands_in_exactly_one_line`, `test_a_line_never_spans_more_than_the_tolerance` and `test_group_lines_ignores_word_order`. Each draws pages of words with free boxes. Run `uv run pytest packages/checkedtables/tests/test_lines.py`.
  - [ ] In a scratch copy, make `group_lines` compare a word with the word before it. `test_a_line_never_spans_more_than_the_tolerance` fails.
  - [ ] In a scratch copy, make `group_lines` drop a word that fits no open line. `test_every_word_lands_in_exactly_one_line` fails.
- [ ] `test_lines.py` gains `test_debris_between_two_rows_joins_neither` for QCASH-Q16 and VAL-Q13, `test_a_label_that_ends_in_text_has_no_values` with "Class 100 Total", `test_a_row_that_ends_in_a_dash_has_values`, and `test_a_row_that_ends_in_a_mark_word_has_values` with `2.8` and a backtick word, row 34 of Appendix E.
- [ ] `test_text.py` gains one `parse_label` test for each row of the label table in Appendix F, the four controls included. Each asserts `printed`, `text` and `marks`, and carries the row's quirk ids. Run `uv run pytest packages/checkedtables/tests/test_text.py`.
  - [ ] In a scratch copy, remove the bare digit form. The "Sheriff 2" test fails while the "Human Services (1)" test passes, so one quirk id cannot hide the other form of ENT-Q07.
- [ ] `test_text.py` gains one test for each of the 12 other quirks that Appendix F gives `text.py`, with the quirk id in the test name or a comment. The input is the text that the quirk's dossier row quotes. Where the row quotes none, the test uses the text at the old file and line that the row cites, and its comment names that file and line.
- [ ] `test_text.py` gains `test_a_line_of_only_prefix_words_keeps_no_value_word` and the Hypothesis property `test_split_line_prefix_loses_no_word`. The first splits three lines that hold only `23`, `24` and `26`. Each prefix holds the word, each returned line has no words, and `has_values` is false for each.
  - [ ] In a scratch copy, make `split_line_prefix` keep the line's last word. `test_a_line_of_only_prefix_words_keeps_no_value_word` fails.
- [ ] `test_testing.py` gains `test_page_from_text_lays_out_six_by_twelve`, `test_double_asterisks_mark_bold_words`, `test_ocr_block_has_no_style` and `test_doc_of_refuses_two_hashes`. Run `uv run pytest packages/checkedtables/tests/test_testing.py`.
- [ ] The branch log shows each test file committed before its module, and failing at that commit.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus high` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run the six gates at the base, which is the S2-B head, and at the head. Record that the base has no `group_lines`. Then run a lane script that builds a page of 40 words by hand, each bottom 0.3 of the word height below the one before, and a second page of three rows 12 points apart with one word halfway between two rows. Save `never-chains.log`. Pass when every gate exits 0 on both sides, the staircase gives more than one line and no line spans more than 0.35 of the word height, and the halfway word is a line of its own.
- [ ] Lane 2. In fresh interpreters, import `checkedtables.text` first, then `checkedtables.lines` first, and call `split_line_prefix` on a line from `page_from_text`. Then run `uv run ty check` and `uv run lint-imports`. Save `text-lines-cycle.log`. Pass when both imports and the call succeed and both gates exit 0.
- [ ] Lane 3. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 4. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 5. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 6. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 7. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 8. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 9. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 10. Not used. Save `none`. Pass when no agent runs for this lane.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not used. The design names no time or size budget for this pull request.
- [ ] Probe. Not used. No probe runs.
- [ ] Baseline. Not used. No baseline is recorded.
- [ ] Rule. Not used. No number fails this pull request.

**Review gate.** None. S2-C is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Every Codex finding is confirmed or dropped, and the summary is in the PR's `## Verification` section.
- [ ] Rebased onto the tip of `step-02/b-value-types` after the verdict, patch-id unchanged.
- [ ] The root reports S2-C as verified, with its head SHA. The operator lands it after S2-B.

## Lex cells and check readings (S2-D)

**Depends on.** S2-C. The operator decided clause C2 on November 23, 2026, so nothing else holds it. The base is `step-02/c-words-to-lines`. S2-D owns clauses C1b, C2 and C3. It builds `lex`.

**Files.**

- [ ] Edit `packages/checkedtables/src/checkedtables/lex.py`, an empty file today.
- [ ] Create `test_lex.py` and `test_val_probe.py` in `packages/checkedtables/tests/`.
- [ ] Create `tests/test_evidence.py`.
- [ ] Edit `tests/test_purity.py`.
- [ ] Edit `docs/evidence/dossiers/VAL.md`, adding section 3.2.1 and changing no other line.
- [ ] Edit `docs/design.md` sections 3.1, 11.1, 15 and 16, and `docs/progress.md`.

**Build.**

- [ ] Write `PROBES` in `test_val_probe.py`, the 55 rows of Appendix E. A row holds the input, the column key, the two old results as text, and the new result as text.
- [ ] Write `describe(cell)` in `test_val_probe.py`. It prints a cell the way Appendix E writes a new result, such as `Amount -3.0`, `Amount 242096 marks *`, `Dash no_value`, `NotApplicable` and `Unreadable two_tokens`.
- [ ] Add the table to VAL as section 3.2.1, "Acceptance inputs for the new lexer", below the dossier's own table and without a change to it. Open the section with where its inputs come from. 16 are the inputs of section 3.2. 39 are examples from sections 1.3, 2 and 3.1, which the owner made part of the acceptance set on November 23, 2026. They are not the 39 that the original probe ran.
- [ ] Add decision 12 to the table of design section 16. The question is "Which 55 inputs does the probe clause of step 2 mean?" The answer is "The 55 of VAL section 3.2.1. The original inputs are in no file. The owner decided on November 23, 2026, with the words '[u]se your list, but make row 4 unreadable.'" Then add "(decision 12)" after the probe clause of step 2 in section 15, and change no other word of the check.
- [ ] Write one private number reader in `lex.py`. It reads one signed token. Paired parentheses or one leading minus glyph make the number negative, and a `$` may stand before the digits on either side of the minus glyph or the opening parenthesis. The minus glyphs are `-`, U+2212, the en dash and the em dash (`tables/amounts.py:13`). The digits are `\d{1,3}(,\d{3})*` or `\d+`, then an optional `\.\d+`, and a leading zero is legal only as the whole integer part. The reader returns a `Decimal` built from the text, so it never inserts a decimal point and never uses `float`. `lex_cell` and `apply_reading` of S2-E both call it, so a reading of `(29.1)` reads as a cell of `(29.1)` does.
- [ ] Write `lex_cell` from design lines 1685 to 1693 as these rules, in order.
  - [ ] No words gives `Blank`. A `YEAR`, `CODE` or `TEXT` column gives `Text`.
  - [ ] The text `N/A` or `NA` gives `NotApplicable`. The text `-`, `--`, an en dash or an em dash gives `Dash(col.dash)`.
  - [ ] Marks leave the end of the cell and go to `Amount.marks`. A mark is one of `*`, `†`, `‡`, `§`, `#` and a backtick (`tables/amounts.py:25`), a Unicode superscript digit, or a last digit word whose size is under 0.7 of the size of the number word before it and whose bottom is above that word's bottom (VAL-Q28). The design measures against the cell's type size, which is the number's and not that of a small `$` in front.
  - [ ] A `$` word of its own leaves the cell's tokens. The number reader takes the `$`, the parentheses and the minus glyph of each token.
  - [ ] Two or more tokens join only in the two shapes of Appendix E, with their token limits, and only in a `MONEY` or `PERCENT` column on a text layer. Any other cell of two or more tokens is `Unreadable`, a detached minus glyph or `%` and a token that ends in a comma included.
  - [ ] A `%` is legal as `col.fmt.percent` says. When `col.fmt.decimals` is a number, the printed decimals must equal it.
  - [ ] An `Amount` and an `Unreadable` keep the cell's word texts joined by one space, and the refs of every word of the cell, the `$` and mark words included.
  - [ ] Every other cell is `Unreadable` with the first reason that applies, in the order `not_a_number`, `two_tokens`, `sign`, `percent_sign`, `grouping`, `decimals`, as Appendix E defines them.
- [ ] Write `split_numeric_runs` from design lines 1682 to 1684. A boundary falls between a letter and a comma-grouped number on either side, as `tables/text_cleaning.py:14-20` requires, so `FY2016` stays one word. A boundary also falls after a `%` or a `)` that a digit, a `(` or a `$` follows. Children get `WordRef.child` from 0 and boxes cut in proportion to characters. A word with one run comes back unchanged.
- [ ] Write `transliteration_ok` from design lines 1694 to 1697. Pin the confusable glyphs as one tuple in `lex.py`. They are `B` and `b` for 8, `D`, `d`, `O`, `o`, `Q` and `q` for 0, and `&` for 6 (`tables/value_recovery.py:46-58`).
- [ ] Write `tests/test_evidence.py` with `test_val_probe_table_is_the_dossier_table`. It loads `test_val_probe.py` by path, renders each row of `PROBES` as a table row, and asserts that the table of VAL section 3.2.1 holds exactly those 55 rows in order.
- [ ] Rewrite the `lex_cell` comment of design section 3.1 to state the two join shapes, the minus glyphs and the six reasons. Record it under Deviations in `docs/progress.md`. Pin the new import pairs and list any new module in design section 11.1.

**You see.**

- [ ] `uv run pytest packages/checkedtables/tests/test_val_probe.py` ends with `1 passed`.
- [ ] `uv run pytest packages/checkedtables/tests/test_lex.py -k "round_trip or digits_of_its_words or digit_swap"` ends with `3 passed`.
- [ ] `uv run pytest tests/test_evidence.py` ends with `1 passed`.
- [ ] `uv run pytest` exits 0.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] C1b. `test_lex.py` gains the Hypothesis property `test_lexer_round_trip`. It draws a `Decimal` with 0 to 12 decimals and prints it grouped or plain, with parentheses or a minus glyph when negative, and with or without a `$`. It names `0.00001` and `1234.567890` as explicit examples. The cell that `lex_cell` returns in a column with decimals as printed is an `Amount` whose `printed` has the same sign, digits and exponent.
  - [ ] In a scratch copy, make the number reader drop a trailing zero of the fraction. The property fails.
  - [ ] In a scratch copy, make the number reader refuse a fraction of more than four digits. The property fails.
- [ ] C1b. `test_lex.py` gains the Hypothesis property `test_amount_digits_are_the_digits_of_its_words`. It draws word texts from digits, separators, signs, letters, spaces and marks. Whenever the cell is an `Amount`, the decimal digits of `printed` are the decimal digits of the words that are not marks, in order, and the exponent is minus the count of digits after the last point.
  - [ ] In a scratch copy, make `lex_cell` join two bare integers. The property still passes, because a join keeps the digits, so `test_bare_integers_never_join` is the test that fails. Record both results.
  - [ ] In a scratch copy, make the number reader accept `007` as 7. The property fails.
- [ ] C2. `test_val_probe.py` gains `test_val_probe_inputs_give_documented_results`. It asserts `len(PROBES) == 55`. For each row it builds the words with `page_from_text`, lexes them in the row's column, and asserts that `describe` of the cell equals the row's new result. Row 39 also asserts the two children of `split_numeric_runs`.
  - [ ] In a scratch copy, change one new result in VAL section 3.2.1. `test_val_probe_table_is_the_dossier_table` fails.
  - [ ] In a scratch copy, change one new result in `PROBES`. Both C2 tests fail.
- [ ] C3. `test_lex.py` gains `test_transliteration_refuses_a_digit_swap` with the four assertions of design lines 3755 to 3759, and `test_confusable_glyphs_are_pinned` with the nine pairs as a literal.
  - [ ] In a scratch copy, make `transliteration_ok` compare digit counts only. `test_transliteration_refuses_a_digit_swap` fails on "65.8" to "85.8".
- [ ] `test_lex.py` gains `test_bare_integers_never_join` as design lines 3750 to 3752 give it, and `test_two_amounts_in_one_cell_never_join` with `4727 402.5`, `1234.5 6`, `12 3,456`, `204,935 3,344` and `746,066,499 726,847,660`.
- [ ] `test_lex.py` gains `test_count_and_ocr_cells_never_join`. `1 23,456` in a `COUNT` column is `Unreadable`, and so are `67,215,504.0 0` on a page that starts with `#ocr`, and `-1 37,332,523` and `$1 37,332,523` in a `MONEY` column on a text layer. The same two inputs in a `MONEY` column on a text layer are the amounts 123456 and 67215504.00.
- [ ] `test_lex.py` gains `test_spaces_after_commas_never_join`. `10, 936, 234` and `(1, 130, 698)` in a `MONEY` column on a text layer are `Unreadable two_tokens`, by the owner's decision on row 4 of Appendix E.
  - [ ] In a scratch copy, let join shape 2 take any number with a decimal point. `test_two_amounts_in_one_cell_never_join` fails on `1234.5 6`.
- [ ] `test_lex.py` gains one test for each of the 21 quirks that Appendix F gives `lex.py`, with the quirk id in the test name or a comment.
- [ ] `test_lex.py` gains `test_a_raised_digit_after_a_small_dollar_sign_is_a_mark` for VAL-Q28. It builds by hand a 6-point `$`, a 12-point `2.8` and a raised 6-point `1`. The cell is `Amount 2.8` with the mark `1` and three word refs.
  - [ ] In a scratch copy, measure the raised digit against the first word. The test fails, because the cell becomes 2.81 through join shape 2.
- [ ] `test_lex.py` gains the Hypothesis property `test_a_lexed_value_is_a_value_word`. Every cell of one or more words that `lex_cell` reads as `Amount`, `Dash` or `NotApplicable` in a `PERCENT` column with an optional percent sign makes `has_values` true for a line that ends in those words. The strategy draws cells with a mark word and cells with a `$` word.
- [ ] The branch log shows the tests committed before `lex.py`, and failing at that commit.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus high` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run the six gates at the base, which is the S2-C head, and at the head. Record that the base has no lexer. Then run a lane script that reads the 55 rows from VAL section 3.2.1, runs each input through a copy of the old `parse_amount` and `parse_decimal`, and through `page_from_text` and `lex_cell`, and prints the three results beside the three the dossier documents. This lane proves C2. Save `probe-55.log`. Pass when every gate exits 0 on both sides and all 165 results equal the dossier's.
- [ ] Lane 2. This lane proves C1b. Run `uv run pytest packages/checkedtables/tests/test_lex.py -k "round_trip or digits_of_its_words" --hypothesis-show-statistics`, then run a lane script that prints 200 amounts of its own choosing in each of the eight printed forms and lexes them. Save `lexer-suite.log`. Pass when pytest reports two passed tests, the statistics show at least 100 passing examples for each, and the script reads back every amount it printed.
- [ ] Lane 3. This lane proves C3. Run a lane script that calls `transliteration_ok` on the four pairs of the check and on every one-digit change of "77,500,000" and "291.8". Save `transliteration.log`. Pass when "1o4.o" to "104.0" and "2918" to "291.8" are accepted, "65.8" to "85.8" and "77,500,000" to "7,500,000" are refused, and every one-digit change is refused.
- [ ] Lane 4. Run a lane script that lexes `4727 402.5`, `1234.5 6`, `12 3,456`, `204,935 3,344`, `1 23,456` in a count column, `2100` in a one-decimal column, and `69,2`, and prints each cell. Then build 40 cells of two or three tokens from the two join shapes and from tokens that end in a comma, with and without a `$`, a minus glyph and parentheses, and with one token changed so the shape no longer fits. Lex each in a money column on a text layer and run each through a copy of the old `parse_decimal`. Save `no-repair.log`. Pass when all seven are `Unreadable`, no `Amount` holds a digit or a point that its words do not print, the new lexer gives an `Amount` for none of the 40 cells that the old reader refuses, and every cell with a token that ends in a comma is `Unreadable`.
- [ ] Lane 5. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 6. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 7. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 8. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 9. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 10. Not used. Save `none`. Pass when no agent runs for this lane.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not used. The design names no time or size budget for this pull request.
- [ ] Probe. Not used. No probe runs.
- [ ] Baseline. Not used. No baseline is recorded.
- [ ] Rule. Not used. No number fails this pull request.

**Review gate.** None. S2-D is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Every Codex finding is confirmed or dropped, and the summary is in the PR's `## Verification` section.
- [ ] Rebased onto the tip of `step-02/c-words-to-lines` after the verdict, patch-id unchanged.
- [ ] The root reports S2-D as verified, with its head SHA. The operator lands it after S2-C.

## Apply reviewed readings to cells (S2-E)

**Depends on.** S2-D. The base is `step-02/d-lexer`. S2-E owns no clause. It builds `records`.

**Files.**

- [ ] Edit `packages/checkedtables/src/checkedtables/records.py`, an empty file today.
- [ ] Create `packages/checkedtables/tests/test_records.py`.
- [ ] Edit `packages/checkedtables/tests/test_library_shape.py` and `tests/test_purity.py`.
- [ ] Edit `docs/design.md` sections 3.1 and 11.1, and `docs/progress.md`.

**Build.**

- [ ] Write `ReviewedReading`, `EveryRow`, `DashRule` and `CellRecords` in `records.py` from design lines 653 to 686.
- [ ] Write `reading_for` from design lines 1701 to 1704 with the signature `reading_for(cell_words, page_words, source, readings)`. `page_words` takes the place of the design's `page` number, which every word's ref already carries. Design lines 689 to 690 make a reading stale when the words inside its box stop joining to `seen`, and the function cannot see those words unless the caller passes them.
- [ ] A reading is a candidate for a cell when its document, page and source match and its box holds at least one of the cell's words, with 1.0 point of slack. No candidate gives `None`. Two candidates give a `duplicate_reading` finding.
- [ ] For the one candidate, take every word of `page_words` that the box holds. Those words must be exactly the cell's words, and their texts joined by one space, left to right, must equal `seen`. Otherwise the result is a `stale_reading` finding. A box that holds two cells is stale for both.
- [ ] Write `apply_reading` from design lines 1705 to 1707. Only an `Amount` or an `Unreadable` cell takes a reading, and any other cell gives a `reading_refused` finding. The cell's `text` must equal the reading's `seen`, or the result is `stale_reading`. Both arguments of `transliteration_ok` come from the record, so without this test a reading could put its value on another cell's words.
- [ ] A reading of `None` gives `Unreadable` with `accepted_by` set. An `Unreadable` cell keeps its reason, and an `Amount` gets the reason `reviewed_null`.
- [ ] Any other reading must pass `transliteration_ok(seen, reading)` and must read as one signed number through the number reader of `lex.py`, or the result is `reading_refused`.
- [ ] Build the reviewed `Amount` from the cell's text and words, the reading's source, `Reading.REVIEWED` and the reading's id.
- [ ] Give all three findings `Severity.BLOCK`, the reading's page, and the subject `<first eight of the hash>:reading:<reading id>`. `reading_for` has no table name, so the subject cannot take the form of design line 447.
- [ ] Change the signature of `reading_for` in design section 3.1, and state the three codes, the subject, the slack and the two tests of `apply_reading` in its comments. Record them under Deviations in `docs/progress.md`, with a note for the step 5 plan that `assemble` passes the words of the cut page.
- [ ] Add the four dataclasses to `FIELD_SNAPSHOT`, pin the new import pairs, and list any new module in design section 11.1.
- [ ] After the verdict, set the step 2 row of `docs/progress.md` to `check passed`, with the date, the five branch names, the SHA of the verified code head and the ID of that head's `CI` run. Do it in a commit of its own.
- [ ] That commit is a new head. Wait for its `CI` run, run one `verify-step` verifier on it, and report its SHA as the head to land.

**You see.**

- [ ] `uv run pytest packages/checkedtables/tests/test_records.py` exits 0.
- [ ] `uv run pytest` exits 0, and the `CI` run for the head is green on Python 3.12 and 3.14.
- [ ] `uv run python packages/checkedtables/tests/test_library_shape.py` prints the kit's line count.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_records.py` gains `test_a_reading_restores_a_lost_separator` for VAL-Q35 with "2918" to "291.8", and `test_a_reading_replaces_letters_with_digits` for VAL-Q36 with "1o4.o" to "104.0". Run `uv run pytest packages/checkedtables/tests/test_records.py`.
- [ ] `test_records.py` gains `test_a_reading_cannot_change_a_digit` with "65.8" to "85.8" for QCASH-Q22 and "77,500,000" to "7,500,000" for MSCH-Q26. Both give `reading_refused`.
  - [ ] In a scratch copy, remove the `transliteration_ok` call from `apply_reading`. The test fails.
- [ ] `test_records.py` gains `test_moved_text_makes_a_reading_stale`, `test_a_box_that_holds_part_of_a_cell_is_stale`, `test_two_readings_for_one_cell_is_a_finding`, `test_a_reading_on_another_page_or_source_is_no_candidate` and `test_a_null_reading_accepts_an_unreadable_cell`.
- [ ] `test_records.py` gains `test_a_box_that_holds_two_cells_is_stale`. Two one-word cells of `7` sit in one box whose reading has `seen` "7". `reading_for` gives `stale_reading` for each cell.
  - [ ] In a scratch copy, make `reading_for` ignore `page_words`. The test fails.
- [ ] `test_records.py` gains `test_a_reading_never_lends_its_value_to_another_cell`. A cell of `65.8` and a record with `seen` "85.8" and `reading` "85.8" give `stale_reading` from `apply_reading`.
  - [ ] In a scratch copy, remove the comparison of the cell's text with `seen`. The test fails.
- [ ] `test_records.py` gains `test_a_negative_reading_is_read` with a cell of `(29 1)` and a reading of "(29.1)", the form of `config/layouts/qcmr-cash.yml:165` in the old repository, and `test_a_null_reading_on_an_amount_gives_reviewed_null`.
- [ ] `test_records.py` gains the Hypothesis property `test_a_reviewed_amount_keeps_the_digits_seen`. For any digits and any separators a reading adds, the `Amount` that `apply_reading` returns has the digits of `seen`.
- [ ] The branch log shows the tests committed before `records.py`, and failing at that commit.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus high` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run the six gates at the base, which is the S2-D head, and at the head. Record that the base has no `records`. Then run a lane script that lays out a one-decimal cash row with `page_from_text`, lexes `2918` and `1o4.o` as `Unreadable`, and applies readings of "291.8", "104.0", "85.8" over a seen "65.8", and `None`. It applies a record with `seen` "85.8" to the cell that prints `65.8`. Then it moves the reading's box off the cell and asks `reading_for` again. Save `readings.log`. Pass when every gate exits 0 on both sides, the first two give reviewed amounts of 291.8 and 104.0, the third gives `reading_refused`, the fourth gives an accepted `Unreadable`, the record for another cell gives `stale_reading`, and the moved box gives `None`.
- [ ] Lane 2. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 3. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 4. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 5. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 6. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 7. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 8. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 9. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Lane 10. Not used. Save `none`. Pass when no agent runs for this lane.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not used. The design names no time or size budget for this pull request.
- [ ] Probe. Not used. No probe runs.
- [ ] Baseline. Not used. No baseline is recorded.
- [ ] Rule. Not used. No number fails this pull request.

**Review gate.** None. S2-E is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Every Codex finding is confirmed or dropped, and the summary is in the PR's `## Verification` section.
- [ ] Rebased onto the tip of `step-02/d-lexer` after the verdict, patch-id unchanged.
- [ ] The root reports S2-E as verified, with its head SHA. The operator lands it after S2-D.

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] At the S2-E head, `uv run pytest -k "exactly_one_line or round_trip or digits_of_its_words or val_probe or digit_swap"` runs the six named proofs of the clause table and all pass.
- [ ] The step 2 row of `docs/progress.md` at the final S2-E head shows `check passed`, the date, the five branch names, the SHA of the verified code head and that head's `CI` run ID. The `CI` run of the final head is green too.
- [ ] The reference snapshot commands still print what `<root>/.audit/reference-baseline.txt` holds.
- [ ] Reply to the operator with the report that `autopilot-stack.md` names, each PR with its verdict.

## Appendix A. Prototype evidence

The root ran the commands below on November 23, 2026, in the session's scratch folder. Two
`pstack:poteto-agent` explorers read the old repository and the design, and the root reran or
read what the table marks. The scratch folder can be cleared at any time, so this appendix
records what each run printed. None of the prototype code is for reuse.

| Question | Result | Evidence |
|---|---|---|
| Does any file hold the 55 probe inputs? | No. VAL section 3.2 prints 16 and says "The surprising results". The design names the probe only at line 4390. | Read by the root. An explorer searched both repositories for `12 345`, `1,234 5`, `$(1,234)`, `+12.3%` and `- 0` and found one docstring, `tables/amounts.py:71`. |
| Do the 16 printed inputs still give the old results the dossier prints? | Yes, all 16, at reference commit `22f355da`. The dossier was written at `49b59ea`. | Run by the root on a copy of `tables/amounts.py` that `cmp` reports identical. |
| Do the examples the dossier prints give 55 inputs? | Yes. 16 in section 3.2, 36 in the table of section 3.1, and 3 in sections 1.3 and 2. All 55 are distinct. | Run by the root. Appendix E lists them with the old results of that run. |
| Can import-linter express "may import only these"? | No. Its contract types are forbidden, layers, independence, protected and acyclic siblings, and it reduces `collections.abc` to `collections`. | Read by an explorer in `importlinter/application/use_cases.py` lines 395 to 407, and run on a probe module. |
| Does a pin of `module.name` pairs refuse the import forms? | Yes. 19 planted forms fail and 3 controls pass. The 19 include `from io import FileIO`, `import sys`, `import posix`, `import _socket`, `from collections import defaultdict`, an import in a function body and one under `TYPE_CHECKING`. | Run by the root with a 40-line scan on Python 3.12.15. |
| Would a list of whole modules be enough? | No. `dataclasses.sys`, `enum.bltns`, `typing.sys`, `statistics.random`, `re.enum`, `re.functools` and `re.copyreg` are all modules. | Run by the root. An explorer ran `dataclasses.sys.stdout.write` and `enum.bltns.open` past a module-level list. |
| Which of the ten plants of `docs/progress.md` does an import pin leave open? | `write = print`, `exec("print(1)")` and the mutable class attribute. | Run by an explorer through a copy of the current scan. |
| What do the pure packages import today? | Nothing. All 42 files are empty. | Run by an explorer. |
| Can `lines` import `normalize_space` from `text` while `text` names `Line`? | Yes, when `text` names `Line` only under `TYPE_CHECKING` and builds the line with `dataclasses.replace`. Both import orders work, and `ty check` passes. | Run by the root on a two-module copy. |
| Does `order=True` sort a `WordRef` and its child? | No. `TypeError: '<' not supported between instances of 'NoneType' and 'int'`. `Finding.page` has the same shape. | Run by the root. |
| Does the old label code delete punctuation or replace it with a space? | It replaces it with a space. | Read by the root at `entities.py:95`. |
| Is Hypothesis installed? | No. `uv.lock` does not name it, and the old repository never used it. | Read by the root and by an explorer. |
| Does a profile with `database=None` stop Hypothesis writing files? | No. Hypothesis 6.170.15 writes `.hypothesis/constants` into the working folder. With `set_hypothesis_home_dir` on a temporary folder, or with `HYPOTHESIS_STORAGE_DIRECTORY` set, the working folder stays as it was. | Run by the root after the Codex review, with one property test in three scratch folders. |
| Does ruff ask for docstrings on magic methods? | Yes. `D105` fires on `__post_init__` and `__lt__` under the repository's rule set, and `from re import compile` passes it. | Run by the root with `ruff check --isolated` and the selected rules. |
| Does a relative import leave `datadesk.core`? | Yes. `importlib.util.resolve_name("..", "datadesk.core")` returns `datadesk`. | Run by the root after the Codex review. |
| Does the old lexer join `1234.5 6`? | No. It returns `None`, and it joins `1,234.5 6`, `123.5 6`, `1 23,456` and `2.8 1`. | Run by the root after the Codex review. |
| Which signed forms of its three joins does the old lexer make? | The digit-first join only with a bare first digit or inside parentheses. `-1 37,332,523` and `$1 37,332,523` give `None`. The decimal join and the comma join with a `$`, a minus or parentheses. | Run by the root on 21 cells after the Codex review. |

These stay unproven until the build.

- Hypothesis under the socket block and the audit hook of the root `conftest.py`. The root ran it in scratch folders only.
- Every lexer rule on a real page. Step 2 reads no PDF. Step 5 runs the lexer on the word fixtures of 20 editions.
- The 39 inputs of Appendix E that the dossier did not print in section 3.2. They are a choice, not a recovery.
- Whether any family prints a superscript digit, a trailing minus or a plus sign (VAL section 12).

## Appendix B. Alternatives rejected

- **Pin a list of whole modules.** A bound module object reaches `sys` and `builtins` through its own attributes (Appendix A). Half the modules the design needs also hold an effect or global state beside the names the design uses, such as `io.open`, `functools.cache` and `decimal.getcontext`.
- **Write the import rule as an import-linter contract.** import-linter has no such contract type and cannot tell `collections.abc` from `collections`.
- **Pin the pairs in the design as well as in the test.** `FIELD_SNAPSHOT` lives in its test alone. The design lists the modules, which change rarely, and the test pins the names.
- **Also ban builtin names such as `print`, `exec` and `getattr`.** The owner chose the allow-list for the import forms. A list of legal builtins is a second closed list and a separate decision. Appendix C records what stays open.
- **Build all of `table.py` in S2-B.** `records` needs three of its ten names. `Table`, `Row`, `Column` and `TableId` have no user before `rows` and `assemble`, which step 5 builds.
- **Give `lex_cell` the kind, the format and the dash meaning as three parameters.** The design gives it a `ColumnSpec`, and five parameters would fail the shape test.
- **Move `split_line_prefix` into `lines.py`.** It would end the cycle with no `TYPE_CHECKING` import. It would also change section 12.1, section 3.1 and four rows of `coverage.tsv` for a function whose signature already works.
- **Make `has_values` call the lexer.** `lines` would import `lex`, `lex` imports `columns` for `ColumnSpec`, and at step 5 `columns` imports `lines`. The plan keeps a loose predicate in `lines.py` and ties it to the lexer with the property `test_a_lexed_value_is_a_value_word`.
- **Use the design's one-sentence kerning rule as written.** A join that only needs one separator and a legal result turns `4727 402.5` into 4727402.5 and `12 3,456` into 123,456. The old code names both as two values (`tables/amounts.py:63-97`). The plan ports its two narrow shapes with their token limits.
- **Read the reading's number in `records.py` with its own pattern.** Two number grammars drift. `apply_reading` imports the one private reader of `lex.py`. A public name for it would add to the kit's shape for one caller.
- **Keep the 55 inputs in a fixture file alone.** The check says the results are documented in VAL. `test_val_probe_table_is_the_dossier_table` pins the dossier to the test, as `test_ci_runs_every_gate` pins `ci.yml`.
- **Let Hypothesis draw new examples on every run.** A gate that fails on one run in fifty blocks an unrelated pull request. The profile is derandomized, and a wider search is a command a person runs.
- **Build `lex` and `text` as sibling pull requests.** Both would edit `tests/test_purity.py` and `docs/progress.md`, and the lexer's tests use `page_from_text`.
- **Leave `doc_of` for a later step.** Design section 12.1 puts it in `testing.py`, no step names it, and it is three lines beside the function that needs the same checks.

## Appendix C. Risks

- **Clause C2 rests on a chosen set (S2-D).** The original 55 inputs are in no file. The owner made Appendix E the acceptance set, so 39 of its inputs are examples the dossier prints elsewhere and not the ones the first probe ran. If the original list turns up, it replaces rows 17 to 55 by a new decision.
- **Spaces after commas make a cell unreadable (S2-D).** VAL section 3.1 reports the form `10, 936, 234 (1, 130, 698)` on text layers and names no family. Each such cell blocks until a reviewed reading supplies its value. The first step that parses a page with the form shows how many readings that costs, and the owner can then restore the join by a new decision.
- **No lexer rule has met a page (S2-D).** The rules come from the design, the dossiers and the old code. Step 5 parses 20 editions and compares every cell with the pinned release at step 6. The two join shapes join nothing the old lexer refused to join. Rows 5, 15 and 52 of Appendix E are amounts that the old page lexer refused, for a `-$` order, a `$` before a parenthesis and a superscript mark. Step 6 compares positions only, so the cash and collections steps carry the test of those three on real pages.
- **`split_line_prefix` can take a value (S2-C).** With a prefix pattern that a short count also matches, a line of values with no label goes into the prefix, whole or in part. The words stay on the row as its prefix, so `match_rows` sees a row with no label. The positions parser of step 5 is the first to declare a prefix (`prefix=_LINE_NO`, design line 2484), so the step 5 plan owns the test on real pages. The Budget in Brief line numbers are a `CODE` column (design line 3270) and never reach this rule.
- **A footnote mark reads as a value word (S2-C).** `(1)` at the end of "Human Services (1)" is a number in parentheses to `has_values`, as it is to the lexer. The design's rule seeds a lane from it. Step 5 builds `lanes_from_values` and owns that test.
- **A bare digit after a word becomes a mark (S2-C).** "Sheriff 2" loses its digit to `Label.marks`, as the old code did (`entities.py:54-61`). A label that ends in a real one-digit number would lose it too. `Label.printed` keeps every word, and two labels that differ only in that digit collide as a `duplicate_row` finding. The owner can refuse this form at the go.
- **Join shape 1 can join two cells (S2-D).** In a money column on a text layer, a one-digit cell and a comma-grouped cell that fall in one lane read as one number, as `1 37,332,523` does. The old code joined them too (`tables/amounts.py:79-91`). A count column and an OCR page never join. Lanes come from geometry, so the test of the cut belongs to step 5 and its fixtures.
- **A value word is defined twice (S2-C, S2-D).** `lines.py` has a loose predicate and `lex.py` a strict reader. The property `test_a_lexed_value_is_a_value_word` fails when the loose one stops covering the strict one. Step 5 decides whether `lanes_from_values` needs the predicate as a public name.
- **The design's rule gives a sentence that ends in a number values (S2-C).** `has_values` is true for a note line that ends in "2025". The design's own uses at lines 3297 to 3318 pair it with a second test. The plan implements the rule as written.
- **The import pin reads static imports (S2-A).** Pure code can still reach an effect with no import. `write = print`, `exec`, `getattr(__builtins__, "open")`, `dataclass.__globals__["sys"]` and a mutable class attribute all pass. A subprocess that a core test starts also passes. Review reads for these.
- **The pin makes every new import a two-line change (every PR).** A pull request that imports a new name edits `PURE_IMPORTS`, and one that imports from a new module also edits design section 11.1. That is the intent, and it costs each later step a few lines.
- **`datadesk core is pure` forbids `urllib` (step 3 or 13).** The listing parsers may need `urllib.parse`. This plan does not touch the contract. The plan for the step that builds the listings decides.
- **Design section 13 and `coverage.tsv` disagree on two counts (S2-C, S2-D).** Section 13 gives `lex_cell` 14 quirks and `parse_label` 9. `coverage.tsv` gives 16 and 10. Appendix F follows `coverage.tsv`. The plan changes neither file.
- **`../gov-budget-data` has six uncommitted entries (every PR).** Lanes run this plan's snapshot commands in place of the plain `git status` of `verify-step` audit 7.
- **Claude Code has no control skill for a command line (every PR).** Lanes drive the kit with shell commands and their own scripts, and return transcripts. The root reads the transcripts, not the lane's summary.
- **`codex-review/run.sh` reviews the checkout it runs in (every PR).** It takes the head from that checkout and the reference's path from the checkout's parent. The root's checkout stays on `main`, and a worktree under `.claude/worktrees/` has no reference beside it. Each review runs in a detached worktree beside the root's checkout, held at the PR head until the run ends.

## Appendix D. Links and reading list

Read these before any edit.

- `CLAUDE.md`, all of it, and `.claude/rules/core-purity.md`.
- `docs/design.md` section 15 step 2, section 2.1 to line 400 and lines 652 to 691, section 3 to line 1708, sections 9, 11.1 to 11.4, 12.1 and 12.5.
- `docs/evidence/dossiers/VAL.md` sections 3 and 9, and the dossier row of each quirk in Appendix F.
- `docs/principles.md` section 7, the purity checklist.
- `.claude/skills/verify-step/SKILL.md` and `.claude/skills/codex-review/SKILL.md`.
- In `../gov-budget-data/packages/gov-budget-etl/src/gov_budget_etl/`, read-only, `tables/amounts.py`, `tables/text_cleaning.py` lines 1 to 22 and 183 to 274, `entities.py` lines 50 to 98, and `tables/value_recovery.py` lines 46 to 58. For S2-C, also `packages/gov-budget-etl/tests/test_entities.py` lines 1207 to 1232 and the `config/entities.yml` lines that Appendix F cites.

S2-A adds this paragraph to design section 11.1, after the paragraph on the audit hook.

```text
The pure packages import from outside themselves only by name. tests/test_purity.py pins, for
each pure package, every module.name pair that it imports, and the test fails when the pairs in
the source differ from the pin in either direction. An import statement that binds an outside
module, a star import, and a pinned name that is itself a module all fail, so pure code never
holds a module object from outside. checkedtables counts its own modules as inside.
datadesk.core counts its own modules and checkedtables as inside. A relative import is resolved
to its full module name first and then judged the same way. The modules each package
imports from are a closed list, given below. A pull request that imports from a module outside
the list changes the list and the pin together.
```

No pull request in this plan needs `<pstack>/skills/how/SKILL.md`. Run
`<pstack>/skills/interrogate/SKILL.md` on the join shapes of Appendix E only if the owner
contests them. The decision trail is `.audit/step-02.tsv`, kept out of git, per
`<pstack>/skills/show-me-your-work/SKILL.md`.

## Appendix E. The acceptance inputs for VAL section 3.2.1

The owner decided on November 23, 2026 that this table is the acceptance set for clause C2, in
these words, "[u]se your list, but make row 4 unreadable." Rows 1 to 16 are the inputs that VAL
section 3.2 prints. Rows 17 to 52 are the examples of the table in VAL section 3.1, in its
order. Rows 53 to 55 are examples from VAL sections 1.3 and 2. The old results are from the
root's run of the old lexer (Appendix A). Rows 4, 10, 15 and 24 carried a choice that the dossier
and the design do not settle. The owner changed row 4 and accepted the other three.

Each input becomes words by a split on spaces, and `lex_cell` reads them in one of four columns.

| Key | Column |
|---|---|
| M | `MONEY`, decimals as printed |
| M1 | `MONEY`, one decimal, the QCMR cash format |
| C | `COUNT`, no decimals |
| P | `PERCENT`, decimals as printed, the sign optional |

Tokens join only in a `MONEY` or `PERCENT` column whose words come from a text layer, and only in
two shapes. VAL section 3.1 reports kerning splits on text layers alone, and VAL section 11 asks
for one word in each cell of a count table. The shapes are read after the marks and a pair of
parentheses around the whole cell leave, and the joined text must then read as one number. In
shape 1 the first token is a bare digit, with no `$` and no minus glyph. In shape 2 the first
token may carry both.

1. One digit, then one or two digits and one or more comma groups, as in `1 37,332,523` (`tables/amounts.py:88-91`).
2. A number with a decimal point whose integer part is comma-grouped or at most three digits, then one digit, as in `67,215,504.0 0` (`tables/amounts.py:92-95`).

No shape joins a cell that both old readers, `parse_amount` and `parse_decimal`, refuse to join.
Both return `None` for `1234.5 6`, `12 3,456`, `-1 37,332,523` and `$1 37,332,523`, and no shape
joins any of the four (Appendix A).

The old lexer also joined tokens that end in a comma, such as `12, 345` and `10, 936, 234`, by
removing every space (`tables/amounts.py:132`). The first draft of this plan kept that join as a
third shape. The owner's decision on row 4 refuses it. A rule that refuses `12, 345` and still
joins `10, 936, 234` would have to count tokens, and nothing on a page supports that. A cell printed with spaces after its commas is `Unreadable`.

An `Unreadable` cell carries the first reason that applies.

| Reason | Meaning |
|---|---|
| `not_a_number` | a token holds a character that no number, sign, mark or separator uses, or the cell holds no digit |
| `two_tokens` | two or more tokens that match no join shape |
| `sign` | a plus sign, a trailing minus, an unpaired parenthesis or two signs |
| `percent_sign` | a `%` that the column's format does not allow, or a missing one that it requires |
| `grouping` | digits and separators that are not one strictly grouped number |
| `decimals` | printed decimals that differ from the column's format |

| # | Input | Old `parse_amount` | Old `parse_decimal` | Column | New result | Decided by |
|---|---|---|---|---|---|---|
| 1 | `12 345` | `12345.0` | `12345` | C | `Unreadable two_tokens` | QPOS-Q27, design line 1690 |
| 2 | `1 2` | `12.0` | `12` | C | `Unreadable two_tokens` | QPOS-Q27 |
| 3 | `12 345 678` | `12345678.0` | `12345678` | C | `Unreadable two_tokens` | QPOS-Q27 |
| 4 | `12, 345` | `12345.0` | `12345` | M | `Unreadable two_tokens` | The owner's decision. VAL-Q21 lists this input beside rows 1 and 2 |
| 5 | `-$61,397,587` | `None` | `-61397587` | M | `Amount -61397587` | VAL-Q22 |
| 6 | `-` | `0.0` | `None` | M | `Dash no_value` | design line 1688 |
| 7 | `--` | `0.0` | `None` | M | `Dash no_value` | BIB-Q50 |
| 8 | `—` | `0.0` | `None` | M | `Dash no_value` | design line 1688 |
| 9 | `---` | `None` | `None` | M | `Unreadable not_a_number` | design line 1692 |
| 10 | `- 0` | `-0.0` | `-0` | M | `Unreadable two_tokens` | A dash word and a number word. The owner accepted it |
| 11 | `(12.3%)` | `-12.3` | `-12.3` | P | `Amount -12.3` | VAL-Q27 |
| 12 | `+12.3%` | `None` | `None` | P | `Unreadable sign` | VAL-Q26 |
| 13 | `123-` | `None` | `None` | M | `Unreadable sign` | VAL-Q26 |
| 14 | `.5` | `None` | `None` | M | `Unreadable grouping` | design line 1692 |
| 15 | `$(1,234)` | `None` | `None` | M | `Amount -1234` | Design line 1686 splits the `$` off. The owner accepted it |
| 16 | `1,234 5` | `None` | `None` | M | `Unreadable two_tokens` | MSCH-Q29 |
| 17 | `1,234,567` | `1234567.0` | `1234567` | M | `Amount 1234567` | strict grouping |
| 18 | `11.6` | `11.6` | `11.6` | M1 | `Amount 11.6` | strict grouping |
| 19 | `(3.0)` | `-3.0` | `-3.0` | M1 | `Amount -3.0` | QCASH-Q53 |
| 20 | `828,904.89` | `828904.89` | `828904.89` | M | `Amount 828904.89` | strict grouping |
| 21 | `44,646,313` | `44646313.0` | `44646313` | M | `Amount 44646313` | strict grouping |
| 22 | `(5,678)` | `-5678.0` | `-5678` | M | `Amount -5678` | MSCH-Q34 |
| 23 | `-4.5` | `-4.5` | `-4.5` | M1 | `Amount -4.5` | QCASH-Q53 |
| 24 | `–7` | `-7.0` | `-7` | M | `Amount -7` | An en dash that touches the digits is a minus. The owner accepted it |
| 25 | `-11.0` | `-11.0` | `-11.0` | M1 | `Amount -11.0` | QCASH-Q53 |
| 26 | `$-61,397,587` | `-61397587.0` | `-61397587` | M | `Amount -61397587` | VAL-Q22 |
| 27 | `–` | `0.0` | `None` | M | `Dash no_value` | design line 1688 |
| 28 | `N/A` | `None` | `None` | M | `NotApplicable` | MCITY-Q34 |
| 29 | `12.3%` | `12.3` | `12.3` | P | `Amount 12.3` | VAL-Q27 |
| 30 | `69%` | `69.0` | `69` | P | `Amount 69` | VAL-Q27 |
| 31 | `26.6%` | `26.6` | `26.6` | P | `Amount 26.6` | VAL-Q27 |
| 32 | `74.98` | `74.98` | `74.98` | P | `Amount 74.98` | SUPOP-Q12 |
| 33 | `242,096*` | `242096.0` | `242096` | M | `Amount 242096 marks *` | VAL-Q28 |
| 34 | `2.8` then a backtick word | `2.8` | `2.8` | M1 | `Amount 2.8` with the backtick as its mark | VAL-Q28 |
| 35 | `TOTAL TAX REVENUE *` | `None` | `None` | M | `Unreadable not_a_number` | design line 1692 |
| 36 | `1 37,332,523` | `137332523.0` | `137332523` | M | `Amount 137332523` | join shape 1 |
| 37 | `67,215,504.0 0` | `67215504.0` | `67215504.00` | M | `Amount 67215504.00` | join shape 2 |
| 38 | `10, 936, 234 (1, 130, 698)` | `None` | `None` | M | `Unreadable two_tokens` | MSCH-Q29. Each half alone is `Unreadable` too, by the owner's decision on row 4 |
| 39 | `TAX434,605,553` | `None` | `None` | M | `Unreadable not_a_number` | VAL-Q34. `split_numeric_runs` gives `TAX` and `434,605,553` |
| 40 | `408,491,218 NET PROFITS TAX` | `None` | `None` | M | `Unreadable not_a_number` | design line 1692 |
| 41 | `2100` | `2100.0` | `2100` | M1 | `Unreadable decimals` | QCASH-Q21, design line 1692 |
| 42 | `266 1` | `2661.0` | `2661` | M1 | `Unreadable two_tokens` | QCASH-Q21 |
| 43 | `69,2` | `None` | `None` | M1 | `Unreadable grouping` | QCASH-Q21 |
| 44 | `67: 3` | `None` | `None` | M1 | `Unreadable not_a_number` | QCASH-Q21 |
| 45 | `B` | `None` | `None` | M1 | `Unreadable not_a_number` | VAL-Q36 |
| 46 | `O` | `None` | `None` | M1 | `Unreadable not_a_number` | VAL-Q36 |
| 47 | `Q` | `None` | `None` | M1 | `Unreadable not_a_number` | VAL-Q36 |
| 48 | `D` | `None` | `None` | M1 | `Unreadable not_a_number` | VAL-Q36 |
| 49 | `&` | `None` | `None` | M1 | `Unreadable not_a_number` | VAL-Q36 |
| 50 | `(59.8j` | `None` | `None` | M1 | `Unreadable not_a_number` | VAL-Q36 |
| 51 | `:` | `None` | `None` | M1 | `Unreadable not_a_number` | VAL-Q36 |
| 52 | `1,234¹` | `None` | `None` | M | `Amount 1234 marks ¹` | VAL-Q28 |
| 53 | `(29 1)` | `-291.0` | `-291` | M1 | `Unreadable two_tokens` | QCASH-Q21 |
| 54 | `1o4.o` | `None` | `None` | M1 | `Unreadable not_a_number` | VAL-Q36 |
| 55 | `110,626,142.01 92.31` | `None` | `None` | M | `Unreadable two_tokens` | VAL-Q15 |

The old lexer joined the tokens of rows 1 to 4, 10, 42 and 53 into one number. All seven are
`Unreadable` now.

## Appendix F. Quirks by pull request

`docs/evidence/coverage.tsv` gives these 48 quirks to functions that step 2 builds. Each gets a
test in the pull request that builds its function.

| Pull request | Function | Quirks |
|---|---|---|
| S2-B | `words.WordSource` | VAL-Q07 |
| S2-C | `text.normalize_space` | QOBL-Q02 |
| S2-C | `text.normalize_label` | BSALES-Q46, BSALES-Q47, SUPOP-Q32 |
| S2-C | `text.squash` | ENT-Q10, MCITY-Q13, MSCH-Q20, SUPOP-Q19 |
| S2-C | `text.parse_label` | BIB-Q38, BIB-Q47, BSALES-Q27, ENT-Q07, QOBL-Q24, QOBL-Q43, QOBL-Q48, QPOS-Q11, RTT-Q38, WAGE-Q44 |
| S2-C | `text.split_line_prefix` | ENT-Q08, QOBL-Q55, QPOS-Q08, QPOS-Q10 |
| S2-C | `lines.group_lines` | QCASH-Q16, VAL-Q13 |
| S2-D | `lex.lex_cell` | BIB-Q50, BSALES-Q38, MCITY-Q34, MSCH-Q29, MSCH-Q34, QCASH-Q52, QCASH-Q53, QPOS-Q21, RTT-Q39, SUPCAP-Q28, SUPCAP-Q34, SUPOP-Q12, VAL-Q09, VAL-Q26, VAL-Q27, VAL-Q28 |
| S2-D | `lex.split_numeric_runs` | BSALES-Q36, RTT-Q22, VAL-Q08, VAL-Q33, VAL-Q34 |
| S2-E | `records.apply_reading` | VAL-Q35, VAL-Q36 |

`parse_label` reads nine mark forms. Each row is one test. The last form is not in the design's
list at lines 1618 to 1619, and the row says where it comes from.

| Form | `printed` | `text` | `marks` | Quirks | Evidence in the old repository |
|---|---|---|---|---|---|
| a number in parentheses | `Human Services (1)` | `Human Services` | `(1)` | QPOS-Q11, ENT-Q07, BIB-Q47 | `config/entities.yml:935`, `entities.py:54-61` |
| the same with two digits | `Office of Prison Oversight (10)` | `Office of Prison Oversight` | `(10)` | QOBL-Q43, QOBL-Q48 | `tests/test_entities.py`, lines 1215 to 1225 |
| an asterisk in parentheses | `Full-Time Positions (*)` | `Full-Time Positions` | `(*)` | QOBL-Q24 | none. The row of `coverage.tsv` names the form, and the label is made up |
| a line formula | `Adjusted Fund Balance (23+29)` | `Adjusted Fund Balance` | `(23+29)` | BIB-Q38 | `config/resolved_assertions.yml:270` holds the normalized "23 29". The label is rebuilt from it |
| two asterisks and a digit | `Total RTT records **1` | `Total RTT records` | `**1` | RTT-Q38, BSALES-Q27, ENT-Q07 | `config/entities.yml:4226` |
| one asterisk | `TOTAL TAX REVENUE *` | `TOTAL TAX REVENUE` | `*` | VAL-Q28 | VAL section 3.1, the footnote mark row |
| a comma and "subtotal" | `Manufacturing, subtotal` | `Manufacturing` | `, subtotal` | BSALES-Q27 | `config/entities.yml:4248` |
| "see note", with or without its space | `Federal Gov't (includes US Post Office) see note` | `Federal Gov't (includes US Post Office)` | `see note` | WAGE-Q44 | `config/entities.yml:3679-3680`. The second line prints `seenote` |
| one bare digit after a word | `Sheriff 2` | `Sheriff` | `2` | ENT-Q07 | `entities.py:54-61`, and `tests/test_entities.py`, lines 1215 to 1225 |

Four controls keep every word and give no mark. They are `CLASS 100`, `10 COMMUNITY DEVELOPMENT`,
`(Over) Under`, and `5 Sheriff`, whose leading digit is a prefix that a table declares
(QPOS-Q08).

Four more quirks have no row for a step 2 function and still get a step 2 test. QPOS-Q27 and
VAL-Q21 are the bare-integer join that `test_bare_integers_never_join` refuses. MSCH-Q26 and
QCASH-Q22 are the two digit swaps of clause C3.

## Appendix G. Codex review

Codex reviewed this plan at commit `a85529ea` on November 23, 2026, with `gpt-6.2-astra` at
`xhigh`. The report is `.codex-review/step-02-plan-a85529ea.md`, which git
ignores. It found that each clause has one named owner, and it raised 14 findings. The root
checked each one by a rerun or by a read of the quoted lines. All 14 held, and none was dropped.
Codex has not reviewed the revisions below.

| # | Severity | Finding | How the root checked it | Revision |
|---|---|---|---|---|
| 1 | blocks | C2 could pass against 55 inputs that an agent chose. | Read the plan, design lines 4388 to 4391 and VAL lines 123 to 139. | C2 stays open until the owner supplies the original inputs or decides that Appendix E is the acceptance set. The decision goes into design section 16, and the table into a new VAL section 3.2.1 beside the dossier's own. |
| 2 | blocks | Join shape 2 took `1234.5 6`, which the old lexer refuses, and the shapes applied to count columns. | Rerun. The old lexer returns `None` for `1234.5 6` and joins `1,234.5 6`. Read VAL section 11, item 4. | The shapes carry the old token limits and apply only to money and percent columns on a text layer. Two tests and S2-D lane 4 hold the counterexamples. Appendix C no longer says that every rule refuses more than the old code. |
| 3 | blocks | A reviewed amount could carry another cell's words, and a box that holds two cells matched both. | Read design lines 688 to 691 and 1701 to 1707 against the S2-E boxes. | `apply_reading` compares the cell's text with `seen`. `reading_for` takes the page's words and requires the words inside the box to be exactly the cell's. Two tests hold the counterexamples. |
| 4 | should fix | A signed reading could not be read, and a null reading on an `Amount` had no reason. | Read `config/layouts/qcmr-cash.yml:165` in the reference, which holds `(29 1)`. | One signed reader serves `lex_cell` and `apply_reading`. A null reading on an `Amount` gets the reason `reviewed_null`. |
| 5 | should fix | A mark word hid a valued row from `has_values`, and a small `$` hid a raised digit from the mark rule. | Read the plan boxes. Rerun. The old lexer joins `2.8 1` into 2.81. | `has_values` skips mark words. The raised digit is measured against the number word. A test builds the three-word cell by hand. |
| 6 | should fix | The round trip drew at most four decimals. | Read the plan and design lines 3714 to 3719. | The property draws 0 to 12 decimals, names two examples, and has a scratch mutation that caps the fraction. |
| 7 | should fix | Keeping the last word left a lane of bare prefixes, and the first prefix on real pages is at step 5. | Read design lines 1620 to 1622, 2484 and 3270. | A line of only prefix words returns no words. A test holds `23`, `24` and `26`. Appendix C names step 5 and drops Budget in Brief. |
| 8 | should fix | Hypothesis writes `.hypothesis/constants` under the planned profile. | Rerun on Hypothesis 6.170.15 in three scratch folders. | The root `conftest.py` points Hypothesis at a temporary folder, and a gate test asserts that a workspace stays clean. |
| 9 | should fix | A relative import could leave `datadesk.core` unpinned. | Rerun. `resolve_name("..", "datadesk.core")` gives `datadesk`. | The scan resolves a relative import before it judges it. Forms on both sides and S2-A lane 2 cover it. |
| 10 | should fix | The function-body mutation tested the wrong collector, and the planted gate asserted line 1. | Read. `import uuid` parses as `ast.Import`, and `run_gate` appends its plant. | The form is `from uuid import uuid4`, and the assertion names no line number. |
| 11 | should fix | One quirk id could hide a second label form, and some dossier rows quote no text. | Read ENT-Q07, BIB-Q47 and the old tests at lines 1215 to 1225. | Appendix F names nine forms with `printed`, `text` and `marks`, four controls, and the evidence for each. The bare digit form is new to the design. |
| 12 | should fix | The Codex review of a pull request would read the root's `main`. | Read `run.sh` lines 28 to 49. | Each review runs in a detached worktree beside the root's checkout, held at the PR head. |
| 13 | minor | The progress commit makes a head that no CI run covers. | Read the plan and `docs/progress.md` lines 23 to 27. | The row records the verified code SHA and its run. The final head gets its own CI run and one verifier. |
| 14 | minor | The checklist named an Appendix G that did not exist. | Read. | This appendix. |

The root found one more thing while it checked finding 8. Ruff's `D105` asks for a docstring on
each magic method of the kit (Appendix A), and "PR mechanics" now says so.

The owner decided clause C2 on November 23, 2026, after this review. Row 4 of Appendix E and the
join shapes changed with that decision, and Codex has not reviewed the change.
