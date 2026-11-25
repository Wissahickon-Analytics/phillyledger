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
- Claude usage is the scarce budget, Fable's most of all, and Codex usage is not. So each model
  has one job, and no long session runs on Fable. Fable plans a step and reads each finished
  diff once. Opus runs each build and writes the code, as `pstack:poteto-agent` delegates. Codex
  reviews each plan, and verifies and reviews each pull request. Model roles live in
  `~/.claude/rules/pstack-models.md`, written by `/pstack:setup-pstack`, never in this file.
- Each build step takes a Plan run, then one Build run for each pull request. This is the full
  track.
  1. **Plan**, in a session on Fable. `/pstack:poteto-mode` turns step N of design section 15
     into `docs/plans/step-NN.md`, in the short format of `docs/plans/README.md`: every clause
     of the step's check with the pull request that owns it and the test that proves it, and
     the pull requests in landing order with the files each touches. Codex reviews the plan
     once (`codex-review plan N`), and the session revises it for each finding it confirms. The
     run stops there.
  2. **Build**, in a session on Opus, one session for each pull request. After the owner's go,
     `/pstack:poteto-mode` runs the Feature playbook on that pull request. One Opus owner
     builds it, and the session runs `just gates`. Codex verifies and reviews it in one pass
     (`codex-review pr N <base>`), and the session confirms or drops each finding. The findings
     that block go to one fix round by a fresh Opus owner, and Codex reads the fix diff
     (`codex-review fix N <reviewed-head>`). Last, a fresh Fable delegate reads the whole diff
     once. The owner decides each landing (hard rule 9).
- **The loop stops.** A pull request gets one Codex review and one fix round, and a second
  round needs the owner's go. `docs/plans/README.md` says which confirmed findings block. Every
  other one is a follow-up, listed in the pull request's text.
- **Codex verifies, and no Claude agent does.** No Claude agent verifies a pull request, reviews
  its comments or reviews a decision trail, and no swarm runs. The Opus owner applies
  `no-comments` and `deslop` to its own diff. The plan and the design give the shapes, the names
  and the signatures, so the session marks the Feature playbook's `how` and `architect` steps
  `skip` and runs no `arena`. This differs from pstack, and the project rule wins.
  `docs/plans/README.md` has the measurements behind it.
- Pull requests stack only where one builds on another. From step 3 on, a step's stacked pull
  requests are one GitHub stack, built and kept linear with `gh stack` (`docs/plans/README.md`).
  Contested design goes to `/pstack:interrogate`.
- **Light track.** The owner may start a step on the light track when its diff cannot change a
  published value, the label or period a value is published under, the kit's public shape, or
  the release protocol. `docs/plans/README.md` says which steps qualify. It skips the Plan run.
  The Build session writes the short plan as the first commit of the pull request, and Codex
  does not review the plan. The rest of the Build run and every hard rule below still hold.
- After steps 6, 13 and 14, Codex also reviews the whole design against the code, the way it
  reviewed the design on November 22, 2026 (`docs/reviews/`).
- Start every session by reading `docs/progress.md`, then the part of `docs/design.md` the work
  needs. Never work from memory of the design. `docs/deviations/`, `docs/plan-notes.md` and
  `docs/followups.md` hold history and notes for single steps. Read one only when the work
  names it.

## Where things are

- `docs/design.md`: the design. Section 15 is the build order with each step's check. Section 12
  lists every module with its job and size estimate; 12.5 has the import rules. Section 16 has
  the owner's decisions, 17 the known gaps, 18 the Codex review.
- `docs/plans/`: one plan per build step.
- `docs/working-with-claude-code.md`: one-time setup and the prompts for each step.
- `docs/progress.md`: step status and the notes every session needs.
- `docs/deviations/step-NN.md`: what each step changed in the design, and why.
- `docs/plan-notes.md`: notes a step left for the plan of a later step.
- `docs/followups.md`: confirmed findings that did not block their pull request.
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
- `just check`, `just test`, `just fix` and `just gates` wrap the commands above (`Justfile`).
  `just gates` runs the six gates that CI runs, and a test keeps the two lists equal.
- `uv run --env-file .env datadesk fetch qcmr --saved <folder>` archives the reports that a folder
  of saved City responses lists, then writes the index file. `.env` holds the four
  `DATADESK_R2_*` variables. The command sends the City no request.

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
   A design change is recorded in `docs/design.md` and in `docs/deviations/step-NN.md` in the
   same pull request.
8. Credentials (R2, Textract) come from the environment. Never commit or print them. Textract
   calls through `datadesk ocr --spend` need the owner's go-ahead.
9. Agents open pull requests ready for review. The owner decides every landing. An agent merges
   a pull request only when the owner tells it to, in that session and for that pull request, and
   only at the verified head with CI passing. That instruction does not carry over to a later
   pull request or session. Agents never push to `main` and never force-push a branch they did
   not create. The one exception is a branch of the step's own GitHub stack: the owner of a pull
   request in that stack, a fix-round owner included, may force-push it after a rebase, with a
   lease on the head it last fetched.
10. A commit message names no model and no tool as an author: no `Co-Authored-By` line of any
    kind and no "Generated with" line. A squash merge takes the pull request title and a blank
    body. Agents never change the git author name or email.

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
- The `verify-step` skill is this repo's verification beside the gates: the check clause by
  clause, and the audits pstack's Prove It Works asks for. Codex runs it for every pull request,
  through the `codex-review` skill.

## Writing

Docs, commit messages and pull request text follow pstack's `unslop` and `technical-writing`
skills: plain and direct, no em-dashes. When a choice rests on evidence, cite the page or the
dossier quirk id. Pull request titles are `type(scope): subject`. An entry in
`docs/deviations/` is a few sentences: what changed, why, the run that shows it and the design
section. The pull request holds the history of its rounds.

## Data this repo does not hold

PDFs never go in git. From step 3 they live in the archive bucket on Cloudflare R2, keyed by
sha256. The City's feed and 21 QCMR reports, as a browser saved them on November 23, 2026, are in
`/Users/nhand/DataProjects/phillyledger-held/qcmr-city`, which `datadesk fetch qcmr --saved` reads.
