# Build step plans

One file per build step, `step-NN.md`, written by the Multi-phase plan playbook of
`/pstack:poteto-mode` from step N of `docs/design.md` section 15. Each plan lists the pull
requests in landing order, what each depends on, the files each may touch, and how each is
verified. Every clause of the step's check is assigned to exactly one pull request.

A plan is written, reviewed by the owner, and only then built. When building shows the plan was
wrong, the plan file is updated in the same pull request as the change.
