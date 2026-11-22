---
name: deslop
description: Remove AI-generated code slop from the branch diff and clean up code style. pstack's Opening a PR step runs this before commit.
---

# Remove AI code slop

Adapted for Python from the `deslop` skill in Cursor's `cursor-team-kit` plugin (MIT, see
`LICENSE` in this folder). That plugin is not in the Claude Code marketplace, so pstack's
`/deslop` step resolves here.

Check the diff against `main` and remove AI-generated slop introduced in the branch.

## Focus areas

- Comments that narrate the code or repeat its names. Keep the ones `CLAUDE.md` keeps: public
  API docstrings in `checkedtables` and `phillyledger`, and comments that cite a dossier quirk
  id.
- Defensive checks or `try`/`except` blocks that are abnormal for trusted internal code. Inside
  `checkedtables` and `datadesk.core`, types are already parsed at the boundary.
- `typing.cast`, `Any` or `# type: ignore` used only to get past the type checker.
- Deeply nested code that early returns or a `match` on a closed union would flatten.
- Wrappers with one caller, flags that pick between two behaviors, and anything else that does
  not match the surrounding code.

## Guardrails

- Keep behavior unchanged unless fixing a clear bug.
- Prefer small, focused edits over broad rewrites.
- Keep the final summary to one to three sentences.
