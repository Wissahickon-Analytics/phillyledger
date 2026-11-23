# Build progress

The build order and each step's check are in `docs/design.md` section 15. Update this file in the
same branch as the work: status, the date the check passed, and anything a later session needs.

| Step | What | Status | Branch | Check passed |
|---|---|---|---|---|
| 1 | Workspace, tooling, purity and shape tests | check passed | `step-01/a-workspace`, `step-01/b-import-contracts`, `step-01/c-kit-shape`, `step-01/d-test-isolation` | November 22, 2026, runs 45093444380, 45079756579, 45082927896 and 45092206629 |
| 2 | Kit, words to cells | not started | | |
| 3 | Archive for the QCMR from FY2022 | not started | | |
| 4 | Words: PDF adapter with font repair, word cache, codec | not started | | |
| 5 | QCMR positions parser, registry, row schemas, column vocabulary | not started | | |
| 6 | Checks, gate and release for positions (first release-quality dataset) | not started | | |
| 7 | Older QCMR positions | not started | | |
| 8 | Cash, O-2, O-3, source comparison, `suggest` | not started | | |
| 9 | Monthly City and School collections | not started | | |
| 10 | Five tax families | not started | | |
| 11 | Budget in Brief | not started | | |
| 12 | Supplemental reports, one statement at a time | not started | | |
| 13 | `watch`, the reader, first full release | not started | | |
| 14 | QSMR, the held-out test of the kit | not started | | |

The step 1 check passed in four `pull_request` runs of `.github/workflows/ci.yml`:

- Clean: run 45093444380 at `d3a9477dad72aa38751277fd2d4f3ee684b49ce1`, the head of
  `step-01/d-test-isolation` after the restack and before the commit that set this row. Every
  gate passed on Python 3.12 and 3.14.
- C2: run 45079756579 at `4395f899294790a878db848e00db2a08d5850ed7`, with `import boto3` planted
  in `datadesk.core`. The `uv run lint-imports` step failed with `datadesk core is pure BROKEN`.
- C3: run 45082927896 at `ec19cf4fd446023fa76f8f5197e3e14d00861a25`, with a `bool` parameter
  planted in `checkedtables`. The `uv run pytest` step failed with `AssertionError: planted`.
- C4: run 45092206629 at `71a76f3d16b74a8bb5c604dac03a3c170f7d8636`, with a `socket.socket()`
  call planted in a core test. The `uv run pytest` step failed with `SocketBlockedError`.

The three plant runs came from temporary pull requests 7, 9 and 13, which are closed. Each ran on
the head of its stack branch at the time, not on the final heads. C2 ran on `805cd23` of
`step-01/b-import-contracts`, C3 on `bd0f2f1` of `step-01/c-kit-shape`, and C4 on `b4eda02` of
`step-01/d-test-isolation`, which has the same patch id as `d3a9477`, the restacked S1-D head
that the clean run used.

## Deviations from the design

Each entry: step, what changed, why, and the design section updated.

- **Step 1: the helper contract forbids the 20 table modules** (November 22, 2026, S1-B). The
  contract "family helpers do not import table modules" forbade only
  `datadesk.core.tables.catalog`. A planted `from datadesk.core.tables import birt` in
  `qcmr_common.py` kept all eight contracts. With the 20 table modules of the independence
  contract added to `forbidden_modules`, the same plant breaks the helper contract. The QSMR table
  modules join the list in step 14, and `qsmr_common` joins the sources. Design section 12.5.
- **Step 1: import-linter forbids listed standard-library modules** (November 22, 2026, S1-B).
  The design marked this "Not verified". Planted one at a time in `datadesk.core`, `import os`,
  `from pathlib import Path`, `import logging`, `import time` and `import random` each broke
  `datadesk core is pure` under import-linter 2.16. Section 12.5 now states the result, and the
  item leaves the list in section 17.4.
- **Step 1: a test fails a source folder with no `__init__.py`** (November 22, 2026, S1-B, found
  in the Codex reviews). import-linter does not scan a folder with no `__init__.py`, and Python
  still imports the modules in it. With `import subprocess` and `RUN = subprocess.run` in a new
  `datadesk/core/sneaky/mod.py`, `uv run lint-imports --no-cache` printed `Contracts: 8 kept, 0
  broken.` and `uv run ruff check .` passed. `test_source_folders_are_packages` in
  `tests/test_gates.py` now fails, naming the folder, when a folder under the three
  `packages/*/src` trees holds a `.py` file, directly or below it, and has no `__init__.py`. It
  first proves its own check on small trees. A first fix used ruff's `INP001`. The build dropped
  it because ruff passed two modules. For `core/reports/probe.py` with `import boto3` and
  `SDK = boto3`, ruff reported `INP001`, and with `#!/usr/bin/env python3` as the first line it
  printed `All checks passed!`. Ruff also passed `import subprocess` in `core/venv/mod.py`, a
  folder it excludes by name, with all eight contracts kept. Design section 12.5.
- **Step 1: the pure packages forbid `importlib`** (November 22, 2026, S1-B, found in the Codex
  review). With `from importlib import import_module` and `import_module("boto3")` in
  `datadesk/core/tables/birt.py`, `uv run lint-imports --no-cache` printed `Contracts: 8 kept, 0
  broken.` The contracts `checkedtables holds no I/O and no Philadelphia` and `datadesk core is
  pure` now forbid `importlib`, and the same plant breaks `datadesk core is pure`. The design
  never uses `importlib`, `import_module` or `__import__`. The purity test that S1-D writes
  reports a call to the builtin `__import__`. Design section 12.5.
- **Step 1: the shape test fails on `bool | None` and `Optional[bool]`** (November 22, 2026,
  S1-C). The design's assertion, `p.annotation in (bool, "bool")`, passed `flag: bool | None` and
  `flag: Optional[bool]`, which `CLAUDE.md` hard rule 5 bans. Section 11.4 now asserts
  `not bool_parameters(fn)`. `bool_parameters` names a parameter whose annotation is `bool` or a
  union with `bool` as a member. Planted in `checkedtables/lex.py`, both forms fail the test,
  with and without `from __future__ import annotations`, and `tuple[bool, ...]` and `int | None`
  pass. The first version read annotations through `inspect.signature(fn, eval_str=True)`. The
  Codex review of the step 1 stack found that it passed `flag: Optional["bool"]`, whose quoted
  `bool` stays a `ForwardRef`, and raised `NameError` on `def valid() -> "Decimal"` with
  `Decimal` imported only under `TYPE_CHECKING`. `bool_parameters` now evaluates each parameter's
  annotation and each union member in the function's globals, where a name that does not
  resolve stands for an unknown type, and it never reads the return type. Planted in scratch
  copies, `Optional["bool"]` fails the test, a module that uses such a `Decimal` in a parameter
  and a return type passes, and the same module fails once a function in it takes `flag: bool`.
  Design section 11.4.
- **Step 1: the shape test reads private re-exports, constructors and inherited members**
  (November 22, 2026, S1-C, found in the build and in the Codex review). `public_functions` kept
  an object only when its `__module__` was the public module being read, and it skipped every
  name that starts with `_`. So a public name could reach a `bool` parameter the test never read.
  Before the change, `uv run pytest packages/checkedtables/tests/test_library_shape.py` printed
  `4 passed` with `def parse(flag: bool)` in a new `checkedtables/_impl.py` and
  `from checkedtables._impl import parse` in `checkedtables/__init__.py`. It printed `4 passed`
  again for a public class in `words.py` whose `__init__` takes `strict: bool`, and for one whose
  `__init__` takes five parameters. Now an object counts when a public name in a public module
  reaches it and its `__module__` is the scanned module or a module under it, and a public class
  that is not a dataclass has its own `__init__` checked without `self`. All three plants fail,
  and a dataclass with five pinned fields passes. The test still read `vars(cls)` only, so
  `class Reader(_Base): pass` passed with `def read(self, strict: bool)` on a private `_Base`,
  and the same held for an inherited `__init__`. A public class's methods and its `__init__` now
  include those it inherits from a base class in the scanned package, private or not, each read
  once as the class resolves it, and a base outside the package adds nothing. Planted in scratch
  copies, the inherited method, the inherited `__init__` and an inherited method with five
  parameters each fail, and a subclass of `json.JSONEncoder`, whose `__init__` takes eight
  parameters, passes. Design section 11.4.
- **Step 1: the purity scan reports `builtins`, `__import__` and mutable module state**
  (November 22, 2026, S1-D, found in the Codex review and the build). The design's scan lists
  eight names. With `impurities` cut back to those eight, `uv run pytest tests/test_purity.py`
  passed with `builtins.open("x")`, `__import__("boto3")` and `CACHE: dict[str, str] = {}`
  appended to `checkedtables/words.py`. `CLAUDE.md` hard rule 3 says the purity test enforces the
  ban on mutable module state, and `__import__` gets past the `importlib` ban of S1-B with no
  import. The scan now also reports any import of `builtins` or read on it, a call to
  `__import__`, and a module-level assignment of a list, dict or set display, a comprehension of
  one, or a call to `list`, `dict`, `set` or `bytearray`. `__all__` gets no exemption, so a
  package writes it as a tuple. The same three lines now fail the test. The Codex review of the
  stack found that the scan read only the direct children of the module body. With
  `if __debug__:` and `CACHE = {}` under it, a `try:` block that holds `CACHE = {}`, or
  `CACHE, SEEN = {}, set()` appended to `checkedtables/words.py`,
  `test_pure_packages_have_no_effects` passed. An `if` opens no scope, so each makes mutable
  module state. The scan now reads every assignment at module scope, inside any nesting of `if`,
  `try`, `with`, `for`, `while` and `match` blocks but not in a function or class body, and it
  counts a tuple that holds a mutable display or call. Each of the three forms now fails the
  test, and a list assigned inside a function passes. Design section 11.1.
- **Step 1: an audit hook refuses socket events, and each core test module starts in an empty
  folder** (November 22, 2026, S1-D, found in the Codex review of the stack). pytest-socket
  replaces only the names `socket.socket`, `socket.getaddrinfo` and `socket.gethostbyname`, and
  its teardown hook lifts the block before fixture finalizers run. In
  `packages/datadesk/tests/core`, a test that called `socket.SocketType()` passed, and so did one
  that called `_socket.socket()` and a module-scoped fixture that called `socket.socket()` after
  its `yield`. A module-scoped fixture there also found `pyproject.toml` in the working
  directory, because `_empty_working_directory` has function scope. The root `conftest.py` now
  installs an audit hook that raises `SocketBlockedError` for `socket.__new__`,
  `socket.getaddrinfo`, `socket.gethostbyname`, `socket.gethostbyaddr` and `socket.getnameinfo`
  unless the running test carries the `enable_socket` marker. Both package `conftest.py` files add
  a module-scoped fixture that moves each test module into an empty folder. The three plants now
  fail with `SocketBlockedError`, and the fixture finds no `pyproject.toml`. Design section 11.1.

## Notes for later sessions

Things learned while building: surprises in the PDFs, commands that matter, traps.

- **Formal verification skill, deferred to step 6** (November 22, 2026). The repo had no product
  code and no git history when `/pstack:setup-pstack` offered one, so there was nothing to
  verify against. Run `/pstack:create-formal-verification-skill` once `run_release` lands.
  - Target: the release protocol in design section 4.5. The promise is that `latest.json` never
    names a release whose files are not all written, and that a slower run cannot undo a newer
    release. Racing runs and retries suit a TLA+ model.
  - Open question for the model, not verified: `created_at` goes into the manifest (section 10).
    If the manifest is one of the create-only files, a retry with the same release id and a new
    `now` may fail in `put_immutable` instead of resuming.
- **`RawRow.bold` and the pinned `bool` fields, a finding for the step 2 plan** (November 22,
  2026). Design section 11.4 pins the kit's `bool` fields to `Word.bold` and `Column.printed`.
  `RawRow.bold` in `checkedtables/rows.py` is also `bool | None` (section 2.1), the same
  annotation as `Word.bold`. The design does not define `bool_fields` or `kit_dataclasses`, so
  it does not say whether `RawRow` counts. Read from the design, not run. Step 1 is unaffected,
  because its expected set is empty. The owner decides whether `RawRow.bold` joins the pinned
  set or `RawRow` stays out of `kit_dataclasses`.
- **`uv.lock` and `exclude-newer`** (November 22, 2026, step 1). The owner's uv config and
  `UV_EXCLUDE_NEWER` set `exclude-newer = "1 week"`, and `uv lock` records that span in
  `uv.lock`. A machine without the setting, such as a CI runner, rejects the lock: `uv lock
  --check` exits 1 with "removal of global exclude newer". The root `pyproject.toml` sets the
  same span under `[tool.uv]`, so the lock checks the same everywhere. Change both together.
  `UV_NO_CONFIG=1` and `UV_CONFIG_FILE` also drop that `[tool.uv]` table. Under either,
  `uv lock --check` fails when `UV_EXCLUDE_NEWER` is not set in the environment, and exits 0
  when it is. To test the lock without the owner's config, read the CI run's `uv sync --locked`
  step.
- **46 empty modules** (November 22, 2026, step 1, S1-B). import-linter refuses a contract that
  names a module that does not exist (`Module 'checkedtables.checks' does not exist.`, exit 1),
  and a wildcard that matches nothing keeps its contract with no warning. So the modules that the
  eight contracts name exist as empty files: 14 in `checkedtables`, 6 in `phillyledger` and 26 in
  `datadesk.core.tables`. Later steps fill them. Deleting one breaks `uv run lint-imports`.
- **ruff skips Markdown** (November 22, 2026, step 1). ruff 0.17 includes `*.md` by default and
  formats the Python blocks in it. `uv run ruff format --check .` failed on `docs/design.md`,
  whose code blocks align their comments on purpose. The root `pyproject.toml` excludes `*.md`.
- **`ci.yml` is pinned** (November 22, 2026, step 1). `test_ci_runs_every_gate` in
  `tests/test_gates.py` fails unless `.github/workflows/ci.yml` equals, byte for byte, a header
  constant plus one step per member of `GATES`. A workflow change edits both files in the same
  pull request. A new gate joins `GATES` and gets its step at the end of `ci.yml`. A scan for
  forbidden strings, tried first, let eight broken workflows pass. The `Kit size report` step is
  not a gate, so it sits in the pinned header, after `Python version`.
- **The shape pins start empty** (November 22, 2026, step 1, S1-C). In
  `packages/checkedtables/tests/test_library_shape.py`, `FIELD_SNAPSHOT` is `{}` and
  `test_bool_fields_are_page_facts_only` expects `set()`. The pull request that adds a kit
  dataclass adds its fields to `FIELD_SNAPSHOT`. The ones that create `Word` and `Column` add
  `("Word", "bold")` and `("Column", "printed")`. `kit_dataclasses` counts every dataclass of
  `checkedtables` that a public name in a public module reaches, so `RawRow` counts when step 2
  creates it. The `RawRow.bold` note above is still the owner's call.
- **Kit types imported only under `TYPE_CHECKING`** (November 22, 2026, step 1, S1-C). The shape
  test evaluates a parameter's annotation with each name that does not resolve at run time
  standing for an unknown type. So `amount: "Decimal"`, with `Decimal` imported only under
  `TYPE_CHECKING`, neither raises nor counts, `flag: "bool | Decimal"` still counts as a `bool`
  parameter, and the return type is never read. Dataclass fields still go through
  `typing.get_type_hints`. A kit dataclass with the field `amount: "Decimal"` and that import
  fails `test_bool_fields_are_page_facts_only` with `NameError`, so import a field's type at run
  time.
- **`test_closed_lists_are_pinned` is not written yet** (November 22, 2026, step 1, S1-C). None
  of the lists it pins exists at step 1. Each list's pin lands in the pull request that creates
  the list, in the same test file (`CLAUDE.md`, hard rule 6).
- **Every test runs with sockets blocked** (November 22, 2026, step 1, S1-D). `--disable-socket`
  and the audit hook in the root `conftest.py` apply to every test, so a later adapter contract
  test that needs the network opts in with the `enable_socket` marker of pytest-socket. The
  marker reopens calls to `socket.socket()`, and an unmarked test after a marked one is blocked
  again. The marker is the only way in. The audit hook reads the marker alone, so a test that
  asks for pytest-socket's `socket_enabled` fixture still fails with `SocketBlockedError`. A name
  that a module binds with `from socket import socket` stays blocked under the marker, because
  the root `conftest.py` installs pytest-socket's block before that import runs. Probed at S1-D,
  under the marker `socket.socket().close()` passes and the early-bound `socket().close()` fails
  with `SocketBlockedError`.
  - pytest-socket 0.8.1 replaces only the names `socket.socket`, `socket.getaddrinfo` and
    `socket.gethostbyname`, and lifts its block before fixture finalizers run. The audit hook
    covers the rest. In a core test, `socket.SocketType()`, `_socket.socket()`,
    `pytest_socket._true_socket()`, a reloaded `socket` module, `_socket.getaddrinfo`,
    `_socket.gethostbyname`, `socket.gethostbyname_ex`, `socket.getnameinfo`, the
    `socket.gethostbyaddr` audit event, and a socket opened after the `yield` of a function- or
    module-scoped fixture each fail with `SocketBlockedError`. `socket.gethostname()` and
    `platform.node()` still work. The probes used unconnected sockets, numeric loopback input
    with numeric flags, and `sys.audit` for `gethostbyaddr`.
  - Two routes still pass. CPython raises no audit event for `_socket.socketpair()`, which makes
    a pair of local sockets, and a subprocess that a test starts opens sockets freely.
  - pytest runs a session-scoped fixture's finalizer inside the last test's protocol, so when
    that test carries `enable_socket`, the finalizer can open a socket even though an unmarked
    test requested the fixture. Probed at S1-D on an unconnected socket, the finalizer opened it
    and the run ended `5 passed`, and with the marker removed it failed with
    `SocketBlockedError` at teardown.
  - A class that a module defines on `socket.socket` keeps the block for the whole session when
    the module is first imported after the root `conftest.py` blocks sockets. `ssl` is one.
    `ssl.SSLSocket` subclasses pytest-socket's guard, so under the marker
    `ssl.create_default_context().wrap_socket(...)` fails with `SocketBlockedError`. With
    `import ssl` at the top of the root `conftest.py`, the same probe passes and the isolation
    tests still pass. Probed at S1-D with the audit hook in place, on an unconnected socket. The
    first contract test that needs TLS makes that change.
  - Each blocked call also prints the `UserWarning` that `SocketBlockedError` issues when it is
    created, so `uv run pytest` reports six warnings, one per blocked call in the isolation
    tests.
- **A core test's package- or session-scoped fixture sees the checkout** (November 22, 2026,
  step 1, S1-D). `_empty_module_working_directory` gives each core test module an empty folder,
  but pytest sets up a package- or session-scoped fixture first, so one that a core test requests
  still runs in the checkout. Probed at S1-D, fixtures of session and package scope found
  `pyproject.toml` in the working directory, and one of module scope did not.
- **The pure packages can still reach effects the gates do not name** (November 22, 2026, step
  1, S1-D, found in the Codex review of the stack and the build). Planted one at a time in
  `datadesk/core/tables/birt.py`, each of these passes every gate: `from io import FileIO`
  reading a file, `sys.stdout.write("x")`, `uuid.uuid4()`, `write = print` then `write(1)`,
  `exec("print(1)")`, `sys.modules["os"].getcwd()`, `import posix` with `posix.getcwd()`,
  `import _socket` with `_socket.socket()`, `defaultdict(list)` assigned at module level, and a
  mutable class attribute. A core test that starts a subprocess, which opens a socket, also
  passes every gate. The forbidden lists and the purity scan name specific modules and calls,
  and every review finds more, so naming more modules does not converge. An allow-list of the
  modules the pure packages may import would close the import forms. That is a new closed list
  in the design, so it is an open decision for the owner.
