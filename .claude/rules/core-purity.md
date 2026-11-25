---
paths:
  - "packages/checkedtables/**/*.py"
  - "packages/datadesk/**/core/**/*.py"
---

# Pure code

These modules decide; they never act. Design sections 1.4, 3 and 11.4 are the reference.

- No `open`, `print`, `input`, `os.`, `time.`, `random`, `.now()`, `.today()`, `logging`,
  sockets, subprocesses or environment reads. The purity test scans for them.
- No mutable module state: no module-level dicts or lists that change, no caches, no
  `initial={}` defaults.
- A function that would do something returns a plan or a value instead. The shell executes plans
  and never decides again.
- Problems are findings with a code and a severity, returned with the result. Raise only for a
  broken invariant, which is a bug.
- Values are frozen, slotted dataclasses. A value that is one piece of text with a rule, such as
  `Sha256`, may be a `str` subclass whose constructor checks the rule (`docs/principles.md`,
  section 8.3). Unions are closed and matched exhaustively.
- A value with a rule of its own has a type of its own, built by one function that checks the
  rule. A result with more than one outcome is a union of named types, never a bare `str` or
  `tuple` (`docs/principles.md`, section 8).
- Every public module, class, function and method has a numpy docstring that says what its
  signature cannot (`CLAUDE.md`, Code).
- In `checkedtables`: no Philadelphia names, no `bool` parameters, no flag fields. `checks`
  imports nothing that knows about words.
