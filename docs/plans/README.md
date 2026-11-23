# Build step plans

One file per build step, `step-NN.md`, from step N of `docs/design.md` section 15. Each plan lists
the pull requests in landing order, what each depends on, the files each may touch, and how each
is verified. Every clause of the step's check is assigned to exactly one pull request.

A plan is written, reviewed by the owner, and only then built. When building shows the plan was
wrong, the plan file is updated in the same pull request as the change.

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

## How much verification a pull request gets

A full-track plan follows the Multi-phase plan playbook of `/pstack:poteto-mode`. Its format has
ten live lanes and four perf boxes for every pull request. Fill only the ones that prove
something.

- One live lane for each clause of the check the pull request owns.
- One live lane for each risk the plan names, such as a quirk or a layout seam.
- The perf boxes only where the design or the step's check names a time or size budget.

Write every other lane and perf box like this. The playbook's check script accepts both forms,
and the Build run spawns no agent for them.

```text
- [ ] Lane 9. Not used. Save `none`. Pass when no agent runs for this lane.
- [ ] Metric. Not used. The design names no time or size budget for this pull request.
```

The reason is the Build run of step 1 on November 22 and 23, 2026. Its decision trail,
`.audit/step-01.tsv`, is kept out of git, so the counts are recorded here.

The first two pull requests ran every lane the format has.

- The root's read of the diff found one hole in the first pull request before any lane ran.
- The check and audit lanes found eight workflow edits that left the CI test green, a folder
  without `__init__.py` that import-linter did not see, and one wrong sentence in a note.
- The twenty live lanes on those two pull requests found no defect. The lanes that own a clause
  still produced the red CI run the check asks for, which is why those stay.
- The two timing lanes measured gates that ran in 0.59 s and 1.53 s, against a budget of 5.0 s
  and an allowance of 3.0 s over the base.

The last two pull requests each got a swarm of four lanes: the gates, the live lane for the
clause, and two audit lanes. An audit lane found a socket that a fixture could open during
teardown, and the step's check passed.

Codex ran four reviews: one of the first pull request, two of the second, and one of the whole
stack at its top, which was the only one to cover the last two pull requests. It raised eighteen
findings, and all eighteen were confirmed. Each review took under ten minutes. The stack review
raised ten of the eighteen and ran before the last fix round, so Codex did not review those
fixes. That is why Codex reviews every pull request.

## Which track a step runs on

A step runs on the full track unless its diff can change none of these:

- a published value,
- the label or the period a value is published under,
- the kit's public shape,
- the release protocol.

By that rule steps 2 and 4 to 14 are full. Step 1 qualifies for the light track, and ran on the
full one before this rule existed. Step 3 is the owner's call. Its storage and index code
qualify, but `confirm_period` decides the period a report is filed under. A step that is mixed
or unclear runs on the full track.

A light-track plan is short: the clause table with a named test for each clause, the files, and
one pull request, or two where one builds on the other. It does not follow the Multi-phase
format, and it is the first commit of its pull request.
