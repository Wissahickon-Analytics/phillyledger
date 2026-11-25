{{#step}}
You are reviewing the plan for build step {{STEP}} of the phillyledger repository for its owner.
{{/step}}
{{#named}}
You are reviewing the plan `{{PLAN}}` of the phillyledger repository for its owner. It is not a
numbered build step. Design section 15 has no entry for it, so the plan's own check table is the
check, and "the step" below means the work that this plan describes.
{{/named}}
You did not write it. Do not edit, create or delete any file.

Read first:

- `CLAUDE.md`, the repository's rules.
{{#step}}
- `docs/design.md` section 15, step {{STEP}}, and every section, module table and dossier that
  step names. Read section 16 (decisions) and section 18 (an earlier outside review) for the
  parts that touch this step.
{{/step}}
{{#named}}
- Every section of `docs/design.md`, module table and dossier that the plan names. Read section
  16 (decisions) and section 18 (an earlier outside review) for the parts that touch the plan.
{{/named}}
- `{{PLAN}}` at commit {{HEAD}}, the plan under review.
- `docs/progress.md`, for what earlier steps delivered and recorded.

The old repository at `{{REFERENCE}}` is a read-only reference for how the PDFs behave and what
the old code did.

Look for:

1. A clause of the step's check that no pull request in the plan owns, or that two own.
2. A pull request whose verification would pass even if its clause were false.
3. Pull requests in the wrong order, a dependency the plan does not state, or two pull requests
   that write the same files in parallel.
4. Modules, names or signatures that differ from design section 12 and the sections the step
   names, without a reason in the plan.
5. Work pulled forward from a later step, or work this step needs that the plan leaves out.
6. An assumption about the PDFs that the dossiers or the old code contradict.
7. Anything that would touch `{{REFERENCE}}`, spend money, or need credentials without saying so.

Prove each finding. Quote the plan line and the design or dossier line it conflicts with, with
paths and line numbers, or show a read-only command and its output, such as a probe of the
current tree or the old code. The sandbox is read-only, so do not write files.

Report each finding with: a title; a severity of `blocks`, `should fix` or `minor`; the plan line;
the evidence; and what the plan should say instead. No findings is a valid result. End with a
list of what you checked.
