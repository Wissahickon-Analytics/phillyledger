You are verifying and reviewing work on build step {{STEP}} of the phillyledger repository for
its owner. You did not write this code.

You are in a throwaway copy of the repository at commit {{HEAD}}, with its environment
installed in `.venv`. The sandbox lets you write only inside this copy and has no network. The
copy is deleted after your run, so you may break code in place to test a claim. Put each file
back before the next check, with `git show HEAD:<path> > <path>`, and commit nothing.

Read first:

- `CLAUDE.md`, the repository's rules.
- `docs/design.md` section 15, step {{STEP}}, and every section, module table and dossier that
  step names.
- `docs/plans/step-{{NN}}.md`, to see which part of the step this pull request claims to deliver.
- `docs/plans/README.md`, the section "What blocks a pull request".
- `docs/deviations/step-{{NN}}.md`, when it exists, for the design changes this step recorded.

The change under review is `git diff {{BASE}}...HEAD`. The old repository at `{{REFERENCE}}` is
a read-only reference for how the PDFs behave.

If the diff changes no file under `packages/` or `tests/`, it changes only docs, rules or
scripts. Skip the two parts below. Look for a sentence the diff makes wrong: one that
contradicts `CLAUDE.md`, the design, another document, or what the code and the scripts do.
Read a changed script, and run it only when it needs no network.

Part 1, verify. Follow `.claude/skills/verify-step/SKILL.md`, where `$0` is {{STEP}} and `$1` is
{{BASE}}. Do its sections "The check" and "Audits". CI runs the gates, so run a gate only when
a finding needs one. To show that a test would pass with its clause false, break the code the
clause describes, run the test, and put the file back.

Part 2, review. Look for:

1. Code that changes, fills or guesses a printed number, or binds a column by position where a
   printed caption exists.
2. File, socket, process, clock, environment, randomness or logging use, or mutable module
   state, in `checkedtables` or `datadesk.core`.
3. Names, signatures, types or module boundaries that differ from the design without a recorded
   deviation.
4. A wrong reading of the PDFs, checked against `docs/evidence/dossiers/` and the old code.
5. Bugs a user of the data would hit.
6. A comment in the diff that neither cites a dossier quirk id nor gives a reason the code
   cannot show.

Run tools from `.venv/bin`, for example `.venv/bin/python -m pytest <test>`. Prove each finding
with a run against the real code when a run can show it. When only reading can show a finding,
such as a mismatch with the design, quote the design line and the code line with their paths
and line numbers.

Report each finding with: a title; `blocks` with the number of the rule it meets in
`docs/plans/README.md`, or `follow-up`; the file and line; the command and its output, or the
two quoted lines; and the result the design or the data requires. Leave out style and naming
unless they break a rule in `CLAUDE.md`. No findings is a valid result. End with each clause of
the check that this pull request owns, proven by which test or not proven, then a list of what
you checked and of any file you changed and put back.
