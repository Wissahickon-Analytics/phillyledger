# Build step plans

One file per build step, `step-NN.md`, from step N of `docs/design.md` section 15.

Work that is not a build step, such as a standards sweep, gets a plan with a name of its own,
such as `standards-sweep-b.md`. Section 15 has no entry for it, so the plan holds its own check
table. When the work changes the design, the plan names the `docs/deviations/step-NN.md` file
that records the change. The `codex-review` commands take the plan's name in place of a step
number, as in `codex-review pr standards-sweep-b <base>`.

## What a plan holds

A plan is short. The design says how the code works, and the plan says who proves what.

- The clause table: every clause of the step's check, the one pull request that owns it, and
  the test that proves it, by name.
- The pull requests in landing order, with what each builds on and the files it may touch.
- The risks the build should probe, each with the quirk id or the design line behind it.
- The questions only the owner can answer, asked before the build.

A plan does not follow the Multi-phase plan format of `/pstack:poteto-mode`. It has no lanes, no
perf boxes and no list of edits. This differs from pstack, and the project rule wins. The plans
of steps 1 and 2 used that format and ran to 713 and 909 lines, which every owner and verifier
then read.

A plan is written, reviewed once by Codex and then by the owner, and only then built. When
building shows the plan was wrong, the plan changes only where a pull request that is not yet
built would be built wrong from it. The design holds each rule as it now stands, and
`docs/deviations/step-NN.md` holds the reason, so a fix round does not restate its change in the
plan.

## Stacks

From step 3 on, the pull requests of a step that build on one another are one GitHub stack
(GitHub's stacked pull requests). The plan names the stack's branches in order, bottom first.

- Owners create and update the branches with the `gh stack` extension of the GitHub CLI
  (`gh stack init`, `gh stack add`, `gh stack submit`). `gh stack link` links pull requests
  that already exist.
- A branch takes its parent's new head by a rebase (`gh stack rebase`), never by a merge
  commit, and is pushed with a lease (`gh stack push`). Hard rule 9 of `CLAUDE.md` allows that
  force-push inside the step's own stack and nowhere else.
- A rebase gives a branch new commit SHAs. Its verdict carries over when the pull request's
  diff against its base is unchanged, shown by an equal `git patch-id` of
  `git diff <base>...<head>` before and after, and `CI` passes at the new head.
- The owner lands the stack from its top pull request by squash. Each layer lands as one
  commit, in order.

Step 2 was built before this rule, and shows why it exists. Hard rule 9 then forbade a
force-push by an agent that did not create the branch, so each fix round merged the parent
branch into its child. The five branches ended with eleven merge commits, and most of those
merges conflicted in `docs/progress.md`. GitHub linked the five pull requests as a stack and
reported four of them as not rebaseable, so the stack could land only as a whole.

## How a pull request is verified

Each pull request gets one Build session on Opus (`CLAUDE.md`, "How work runs here"). In order:

1. One Opus owner builds it, tests first, and opens the pull request.
2. The session runs `just gates` at the head. CI runs the same six gates.
3. Codex verifies and reviews it in one pass (`codex-review pr N <base>`). It runs the check and
   the audits of the `verify-step` skill and then the review, in a throwaway worktree where it
   can run tests and break code.
4. The session confirms each finding with a run or a quote, and sorts it by the rule below.
5. The findings that block go to one fix round by a fresh Opus owner. Codex then reads only the
   fix diff (`codex-review fix N <reviewed-head>`), and the gates run at the new head.
6. A fresh Fable delegate reads the whole diff once, against the plan and the design.
7. The session hands the pull request to the owner with its verdict and its follow-ups.

No Claude agent verifies the pull request, reviews its comments or reviews a decision trail.
The Opus owner applies the `no-comments` and `deslop` skills to its own diff. Both keep the
docstrings that the Code section of `CLAUDE.md` asks for.

Codex's sandbox has no network. A clause that needs a run outside it, such as a CI run on a
planted change or a call to R2, is proven by the Opus owner, who records the run in the pull
request, and the session checks that record.

A timing or size check exists only where the design or the step's check names a budget. The
Opus owner writes it as a test.

## What blocks a pull request

A finding counts once the session has confirmed it, as the `codex-review` skill says. A
confirmed finding blocks when it shows one of these at the reviewed head:

1. A gate fails.
2. A clause of the step's check that the pull request owns has no test, or has a test that
   still passes with the clause false.
3. The diff breaks a hard rule of `CLAUDE.md`.
4. The code gives a number, a label or a period that the words do not print, for an input that
   a dossier, a word fixture or the design shows.
5. A sentence the diff adds to the design, the rules or a skill is false, or contradicts
   another one.

Every other confirmed finding is a follow-up. Steps 1 and 2 give the usual kinds: a stricter
check in a constructor, a scan that a contrived input gets past, a mutant that survives behind a
clause whose test stands, a wrong reading of an input that no page is known to print, and a
reworded message.

The session lists follow-ups under `## Follow-ups` in the pull request's text, which no other
branch of a stack edits. When the step's last pull request is verified, the session shows the
owner the step's follow-ups. The ones he keeps go into `docs/followups.md`, and one cleanup pull
request fixes the ones he picks.

A pull request gets one Codex review and one fix round. A second round needs the owner's go,
whatever asks for it: a blocking finding in the fix diff, or one from the Fable read after the
fix round is spent.

pstack draws the same line for a verified queue: only a bug a user would hit, a failed gate or
a wrong shipped doc blocks, and everything else goes in a follow-up (the Autopilot-full
playbook, step 4).

## Why verification is this size

The Build runs of steps 1 and 2, on November 22 and 23, 2026, gave each pull request a swarm of
Opus verifiers and ran a whole step in one Fable session. Step 2 also sent a pull request back
to Codex after its fix rounds.
The counts below come from the session transcripts and from the decision trails
`.audit/step-01.tsv` and `.audit/step-02.tsv`, which are kept out of git, so they are recorded
here.

What it cost:

- In about 31 hours the two steps used 48% of the weekly Fable limit and 39% of the weekly
  limit for all models, as the plan's usage card read on November 23, 2026.
- The Fable main session was 96% of the Fable use. In the step 2 Build run it made 557 calls
  at an average context of 534,000 tokens, because one session carried five pull requests. The
  shares here weigh a cache read at 0.1 of an input token, a cache write at 1.25 and an output
  token at 5. How the plan's limits weigh them is not published.
- Of the Opus use, 92 verifier agents were 31%, 26 fix-round owners 39% and 13 first-build
  owners 24%.
- The five pull requests of step 2 took 16 fix rounds and 15 runs of a verifier at a fix head,
  and the step ran 24 Codex reviews of a pull request. `docs/deviations/step-02.md` says of one
  pull request's rounds that "the list had no natural end".

What it found:

- In step 1, the first two pull requests ran every lane of the Multi-phase format. The root's
  read of the diff found one hole before any lane ran. The check and audit lanes found eight
  workflow edits that left the CI test green, a folder without `__init__.py` that import-linter
  did not see, and one wrong sentence in a note. The twenty live lanes found no defect. The two
  timing lanes measured gates that ran in 0.59 s and 1.53 s, against a budget of 5.0 s and an
  allowance of 3.0 s over the base.
- The last two pull requests of step 1 each got four lanes. An audit lane found a socket that
  a fixture could open during teardown.
- Codex ran four reviews in step 1 and raised eighteen findings, and all eighteen were
  confirmed. Each review took under ten minutes. The review of the whole stack raised ten of
  the eighteen and ran before the last fix round, so Codex did not review those fixes. That is
  why Codex reads every fix diff.
- In step 2, `docs/deviations/step-02.md` credits a Codex review in 11 of its 17 entries, across
  all five pull requests. It credits verifiers in 6: 5 entries of the build, and the entry on
  decisions 13 to 17. The entries count 18 mutants that survived the tests. A surviving mutant
  is a gap in the tests, and by the rule above it is a follow-up unless it leaves a clause
  unproven.

What Codex can do in place of the verifiers, run on November 23, 2026: `codex exec --sandbox
workspace-write`, in a throwaway worktree with a synced environment, ran the 217 tests with
`.venv/bin/python -m pytest` and again with `uv run --no-sync pytest`, ran `ruff check`,
`ty check` and `lint-imports`, copied a package to a scratch folder and read the git history.
The sandbox refused a write to the main checkout (`Operation not permitted`) and a call to the
network.

## Which track a step runs on

Every step is built as above. A step on the light track skips the Plan run: the Build session
writes the plan as the first commit of its pull request, and Codex does not review the plan.
The owner may start a step on the light track when its diff can change none of these:

- a published value,
- the label or the period a value is published under,
- the kit's public shape,
- the release protocol.

By that rule steps 2 and 4 to 14 take a Plan run. Step 1 qualified for the light track, and ran
before this rule existed. Step 3 is the owner's call. Its storage and index code qualify, but
`confirm_period` decides the period a report is filed under. A step that is mixed or unclear
takes a Plan run.
