# phillyledger

The rules for this repository are in `CLAUDE.md`. Read it before any work here. The design is
`docs/design.md`; section 15 is the build order with each step's check.

Codex verifies and reviews this repository; it does not build it. A review of a pull request
runs in a throwaway copy. Break code there only to test a claim, put it back, and commit
nothing. Prove each finding with a command and its output or with exact quotes, and report
findings without fixing them. `../gov-budget-data` is a read-only reference: never change
anything there.
