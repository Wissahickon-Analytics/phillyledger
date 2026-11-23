# phillyledger

Checked tables of Philadelphia budget and finance data, extracted from the City's and the School
District's PDFs. Every published number comes from words on a printed page, and every table
carries declared arithmetic checks. This repo replaces parts of `gov-budget-data`. It is built
from scratch, one step at a time, from the design in `docs/design.md`. There is no deadline: a
step is finished when its check passes.

## How work runs here

- Engineering work follows pstack (the `pstack` Claude Code plugin). Substantive work starts with
  `/pstack:poteto-mode`, and its principles apply. The project rules below add to pstack. Where
  they differ, the project rule wins and says so.
- The main session runs Fable. It plans, owns the design, reviews every diff and verifies every
  claim. Code is written by `pstack:poteto-agent` delegates on Opus 5.5. Model roles live in
  `~/.claude/rules/pstack-models.md`, written by `/pstack:setup-pstack`, never in this file.
- Each build step goes through two runs of `/pstack:poteto-mode`. This is the full track.
  1. **Plan.** The Multi-phase plan playbook turns step N of design section 15 into
     `docs/plans/step-NN.md`: the pull requests in landing order, the files each touches, and
     each one's verification, with every clause of the step's check assigned to a pull request.
     Codex then reviews the plan (`codex-review plan N`), and the Fable session revises it for
     each finding it confirms. The run stops there.
  2. **Build.** After the owner's go, the Autopilot-stack playbook runs that plan. Opus owners
     build each pull request, and a swarm verifies it with the `verify-step` skill. Codex then
     reviews it (`codex-review pr N <base>`), and the Fable session confirms or drops each Codex
     finding, sends confirmed ones back to a fresh Opus owner, and gives the final review.
     Contested design goes to `/pstack:interrogate`. Pull requests stack only where one builds
     on another. The owner decides each landing (hard rule 9).
- **Verification is sized by what there is to prove.** A pull request's swarm is the three
  parts of `verify-step` (the gates, the check and the audits), each as its own lane, plus one
  live lane for each clause the pull request owns and each risk its plan names. It gets a
  timing lane only where the design or the step's check names a time or size budget. pstack's
  plan format asks for ten live lanes and four perf boxes on every pull request. The plan
  writes the ones it does not need as "Not used", and no agent runs for them. This differs
  from pstack, and the project rule wins. `docs/plans/README.md` has the wording and the reason.
- **Light track.** The owner may start a step on the light track when its diff cannot change a
  published value, the label or period a value is published under, the kit's public shape, or
  the release protocol. `docs/plans/README.md` says which steps qualify. It is one run of
  `/pstack:poteto-mode` with the Feature playbook. The session writes a short plan as the first
  commit of the pull request, one Opus owner builds it, one verifier runs `verify-step` in full
  at the finished head, and Codex reviews the pull request once. There is no plan review and no
  swarm. Every hard rule below still holds.
- After steps 6, 13 and 14, Codex also reviews the whole design against the code, the way it
  reviewed the design on November 22, 2026 (`docs/reviews/`).
- Start every session by reading `docs/progress.md`, then the part of `docs/design.md` the work
  needs. Never work from memory of the design.

## Where things are

- `docs/design.md`: the design. Section 15 is the build order with each step's check. Section 12
  lists every module with its job and size estimate; 12.5 has the import rules. Section 16 has
  the owner's decisions, 17 the known gaps, 18 the Codex review.
- `docs/plans/`: one plan per build step.
- `docs/working-with-claude-code.md`: one-time setup and the prompts for each step.
- `docs/progress.md`: step status, deviations from the design, and notes for later sessions.
- `docs/principles.md`: functional core, imperative shell, and plan-then-execute, with sources.
- `docs/evidence/dossiers/<FAMILY>.md`: what the PDFs actually contain. Quirk ids such as
  `QPOS-Q12` refer to these files. `docs/evidence/quirks.tsv` lists every quirk, and
  `docs/evidence/coverage.tsv` says which module handles each one.
- `docs/prototype/vocab/`: a tested prototype of the column vocabulary. Port it at step 5; never
  import from it.
- `docs/reviews/`: outside reviews of the design. `AGENTS.md` points Codex at this file.
- `../gov-budget-data`: the old repo, a read-only reference. Design section 14 says what to port.

## Packages (one uv workspace)

- `packages/checkedtables`: the general kit, from words to checked tables. No I/O and nothing
  about Philadelphia. Goes to PyPI after step 14.
- `packages/phillyledger`: the reader for released data. Goes to PyPI. Built at step 13.
- `packages/datadesk`: everything specific to Philadelphia. Never published. `datadesk.core` is
  pure; `datadesk.shell` holds every effect behind six ports.

## Commands

Step 1 creates these. Keep this list true as tooling changes.

- `uv sync`
- `uv run pytest`
- `uv run ruff check .` and `uv run ruff format --check .`
- `uv run ty check`
- `uv run lint-imports`
- `uv run prek run --all-files`

## Hard rules

1. Never modify `../gov-budget-data`. Read it, quote it and port from it. Never edit, commit,
   branch, stash, reset or check out anything there. A hook blocks it.
2. A step is finished only when every clause of its check in design section 15 passes. Never
   weaken, skip, mark xfail or reword a check to make it pass. A check that looks wrong is a
   finding to report, not a test to change.
3. `checkedtables` and `datadesk.core` are pure: no files, sockets, processes, clock,
   environment, randomness, logging or mutable module state. A problem comes back as a finding,
   not a log line. The purity test enforces this.
4. A number is published only from words on the page. No value repair, no guessing, no search
   over hypotheses. A human reading of a cell is a record with a page and a reason.
5. Public functions in `checkedtables` take no `bool` parameters, and its types have no flag
   fields. The shape test enforces this.
6. Closed lists stay closed. Adding a member to a pinned list (check relations, note kinds, the
   six vocabulary lists) changes the pin test and the design in the same pull request.
7. Following pstack, settle a question by running something when a run can settle it, make the
   reversible choice, and record it. Stop for the owner only on calls no run can settle: what a
   printed number means, what gets published, money, or anything touching `../gov-budget-data`.
   A design change is recorded in `docs/design.md` and under Deviations in `docs/progress.md` in
   the same pull request.
8. Credentials (R2, Textract) come from the environment. Never commit or print them. Textract
   calls through `datadesk ocr --spend` need the owner's go-ahead.
9. Agents open pull requests ready for review. The owner decides every landing. An agent merges
   a pull request only when the owner tells it to, in that session and for that pull request, and
   only at the verified head with CI passing. That instruction does not carry over to a later
   pull request or session. Agents never push to `main` and never force-push a branch they did
   not create.

## Code

- Python 3.12 or later. Frozen, slotted dataclasses for values, `StrEnum` for closed lists,
  `Decimal` for every amount, never `float`. Type hints everywhere; `ty check` passes.
- ruff, line length 100. Start from the rule set in `../gov-budget-data/pyproject.toml`.
- Docstrings (numpy style) only on the public API of `checkedtables` and `phillyledger`, the
  names users import. Apply ruff's `D` rules to those two packages only. Elsewhere names and
  types carry the meaning. This narrows the old repo's rule set to fit pstack's `no-comments`.
- A comment that explains a PDF quirk cites its dossier id (`# QPOS-Q12: ...`). The publisher's
  PDFs are an outside source this repo cannot reshape, so these comments stay.
- Keep the names and signatures the design gives. If a module runs well past its estimate in
  section 12, say so in progress.md.

## Tests

- Write the step's check as failing tests first, then the code.
- Core tests run with sockets disabled (pytest-socket) in an empty temporary directory.
- Property tests use Hypothesis.
- Real pages enter tests only as word fixtures that `datadesk fixture <sha> <pages>` writes to
  `tests/fixtures/words/` as Python literals. Regenerate a fixture only on purpose, and say so
  in the commit.
- The `verify-step` skill is this repo's verification: the gates, the check clause by clause,
  and the audits pstack's Prove It Works asks for.

## Writing

Docs, commit messages and pull request text follow pstack's `unslop` and `technical-writing`
skills: plain and direct, no em-dashes. When a choice rests on evidence, cite the page or the
dossier quirk id. Pull request titles are `type(scope): subject`.

## Data this repo does not hold

PDFs never go in git. From step 3 they live in the archive bucket on Cloudflare R2, keyed by
sha256. Before that, the owner's held reports are on his machine: ask for the path when step 3
starts.
