You are reading the fix round of a pull request on build step {{STEP}} of the phillyledger
repository for its owner. You did not write this code.

You are in a throwaway copy of the repository at commit {{HEAD}}, with its environment
installed in `.venv`. The sandbox lets you write only inside this copy and has no network. The
copy is deleted after your run, so you may break code in place to test a claim. Put each file
back before the next check, with `git show HEAD:<path> > <path>`, and commit nothing.

The fix round is `git diff {{BASE}}..HEAD`. The review it answers is `{{PRIOR}}`, when that file
exists, and the messages of the fix commits name the findings they close. The old repository at
`{{REFERENCE}}` is a read-only reference for how the PDFs behave.

Read `CLAUDE.md` and the section "What blocks a pull request" of `docs/plans/README.md`.

Check these, and nothing else:

1. Each finding the fix round closes. Rerun the finding's command. The failure it showed must
   be gone, and a test must fail when the fix is taken out.
2. The fix diff itself. Look in the changed lines for anything that blocks by the rule in
   `docs/plans/README.md`.
3. Scope. The fix round changes nothing that its findings do not need.

Raise no finding about code the fix diff does not touch. The pull request was reviewed at
{{BASE}}, and that review is closed.

Run tools from `.venv/bin`, for example `.venv/bin/python -m pytest <test>`. Prove each finding
with a command and its output, or with two quoted lines and their paths and line numbers.

Report first each finding of the earlier review as closed or not closed, with the run that
shows it. Then report each finding in the fix diff with: a title; `blocks` with the number of
the rule it meets, or `follow-up`; the file and line; the command and its output, or the two
quoted lines; and the result the design or the data requires. No findings is a valid result.
End with a list of what you checked and of any file you changed and put back.
