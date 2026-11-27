# Build progress

The build order and each step's check are in `docs/design.md` section 15. Update this file in the
same branch as the work: status, the date the check passed, and what every later session needs.
Every session reads this file first, so it stays short.

| Step | What | Status | Branch | Check passed |
|---|---|---|---|---|
| 1 | Workspace, tooling, purity and shape tests | check passed | `step-01/a-workspace`, `step-01/b-import-contracts`, `step-01/c-kit-shape`, `step-01/d-test-isolation` | November 22, 2026, runs 45093444380, 45094817250, 45094829990 and 45092206629 |
| 2 | Kit, words to cells | check passed | `step-02/a-import-pin`, `step-02/b-value-types`, `step-02/c-words-to-lines`, `step-02/d-lexer`, `step-02/e-records` | November 23, 2026, head `73d428e2`, run 45130645501 |
| 3 | Archive for the QCMR from FY2022 | check passed | `step-03/a-index`, `step-03/b-listing`, `step-03/c-fetch-plan`, `step-03/d-shell`, `step-03/e-archive` | November 24, 2026, head `647b868b`, run 45538468977 |
| 4 | Words: PDF adapter, word cache, codec | check passed | `step-04/a-font-code-cells`, `step-04/b-codec-cache`, `step-04/c-words`, `step-04/d-fixtures`, `step-04/e-crops` | November 26, 2026, head `3c3d6df`, run 45927301261, and the owner's words on the row crops |
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
- C2: run 45094817250 at `57b19ab8a77c2756903ea7479706838000c477ce`, with `import boto3` planted
  in `datadesk.core`. The `uv run lint-imports` step failed with `datadesk core is pure BROKEN`.
- C3: run 45094829990 at `b843fa8f426df090c28213c6bf6898d5b83bb935`, with a `bool` parameter
  planted in `checkedtables`. The `uv run pytest` step failed with `AssertionError: planted`.
- C4: run 45092206629 at `71a76f3d16b74a8bb5c604dac03a3c170f7d8636`, with a `socket.socket()`
  call planted in a core test. The `uv run pytest` step failed with `SocketBlockedError`.

The three plant runs came from temporary pull requests 14, 15 and 13, which are closed. Each plant
is one commit on a stack head. C2 ran on `8979428`, the final head of
`step-01/b-import-contracts`, and C3 on `7189a67`, the final head of `step-01/c-kit-shape`. C4
ran on `b4eda02` of `step-01/d-test-isolation`, which has the same patch id as `d3a9477`, the
restacked S1-D head that the clean run used.

## Where the rest is

No session reads these by default. Open one when the work needs it.

- `docs/deviations/step-NN.md`: what each step changed in the design, and why.
- `docs/plan-notes.md`: notes that a step left for the plan of a later step, and gaps in the
  gates that review reads for. The Plan run of a step reads the ones that name it.
- `docs/followups.md`: confirmed findings that did not block their pull request, by step.

## Notes for every session

Commands that matter and traps in the tooling. A note belongs here only when every later
session needs it. A note for one later step goes in `docs/plan-notes.md`.

- **What the type rules leave for later steps** (November 25, 2026. Updated November 25, 2026,
  standards sweep B, and November 26, 2026, S4-B). The owner asked for typer, docstrings and the
  type rules of the book Robust Python. `CLAUDE.md` (Code) and section 8 of `docs/principles.md`
  hold them. Standards sweep A brought the code of steps 1 to 3 to the typer and docstring rules,
  and ruff checks docstrings in all three packages. Sweep B gave a sha256 the type `Sha256` and
  named the readers' refusals `PeriodRefusal` and `SkipReason`. New code follows the rules. No later
  sweep takes the rest. Asked whether each should wait for the step that next changes its file, the
  owner answered "Yes, wait per step", so each waits for the plan of that step:
  - `SourceCatalog | tuple[Finding, ...]` and the result of `gather_repo`, which sweep B kept;
  - `Rejection.reason`, which holds `http_<status>` and finding codes beside the period codes;
  - a URL, a store key, the parse cache key, a `listed_at` stamp and an edition id. The word
    cache key has its type, `WordKey` (S4-B);
  - the other callers in `datadesk` that tell a union apart with an early `isinstance` return,
    or with a `match` that has no `assert_never`, which
    `rg 'isinstance\(|^\s*match ' packages/datadesk/src` lists. S4-D turned the two in
    `fetch_command` into `match` statements that end in `assert_never`;
  - `phillyledger`, which may not import the kit, so step 13's plan decides how it types a sha.
  `checkedtables/__init__.py` exports nothing yet, so `Sha256` is imported from
  `checkedtables.refs`.
- **`uv.lock` and `exclude-newer`** (November 22, 2026, step 1). The owner's uv config and
  `UV_EXCLUDE_NEWER` set `exclude-newer = "1 week"`, and `uv lock` records that span in
  `uv.lock`. A machine without the setting, such as a CI runner, rejects the lock: `uv lock
  --check` exits 1 with "removal of global exclude newer". The root `pyproject.toml` sets the
  same span under `[tool.uv]`, so the lock checks the same everywhere. Change both together.
  `UV_NO_CONFIG=1` and `UV_CONFIG_FILE` also drop that `[tool.uv]` table. Under either,
  `uv lock --check` fails when `UV_EXCLUDE_NEWER` is not set in the environment, and exits 0
  when it is. To test the lock without the owner's config, read the CI run's `uv sync --locked`
  step.
- **Modules that hold only a docstring** (November 22, 2026, step 1, S1-B. Updated November
  25, 2026, standards sweep A). import-linter refuses a contract that names a module that does
  not exist (`Module 'checkedtables.checks' does not exist.`, exit 1), and a wildcard that
  matches nothing keeps its contract with no warning. So the modules that the contracts name
  exist before their code. At the head of sweep A, 36 modules hold only a docstring that gives
  the job design section 12 lists for them: 6 in `checkedtables`, 5 in `phillyledger` and 25 in
  `datadesk.core.tables`. Nine packages hold only a docstring in `__init__.py`. Later steps fill
  them. Deleting any of the 36 modules breaks `uv run lint-imports`, and so does deleting the
  `__init__.py` of `checkedtables.checks`, `datadesk.core`, `datadesk.core.tables`,
  `datadesk.shell` or `phillyledger._shell`. Deleting the `__init__.py` of `checkedtables`,
  `datadesk`, `datadesk.shell.adapters` or `phillyledger` leaves all nine contracts kept.
- **ruff skips Markdown and the word fixtures** (November 22, 2026, step 1. Updated November 26,
  2026, S4-D). ruff 0.17 includes `*.md` by default and formats the Python blocks in it.
  `uv run ruff format --check .` failed on `docs/design.md`, whose code blocks align their
  comments on purpose. The root `pyproject.toml` excludes `*.md`. It also excludes
  `packages/datadesk/tests/fixtures/words`, where ruff found 9,219 errors and 20 files to
  reformat, so no gate rewrites a word fixture. prek's ruff hooks pass `--force-exclude`, so they
  skip the folder too. ty still checks the fixtures: at S4-D, `uv run ty check` took a median of
  0.13 s with the 20 files and 0.11 s without them, over seven runs each.
- **`ci.yml` is pinned** (November 22, 2026, step 1). `test_ci_runs_every_gate` in
  `tests/test_gates.py` fails unless `.github/workflows/ci.yml` equals, byte for byte, a header
  constant plus one step per member of `GATES`. A workflow change edits both files in the same
  pull request. A new gate joins `GATES` and gets its step at the end of `ci.yml`. A scan for
  forbidden strings, tried first, let eight broken workflows pass. The `Kit size report` step is
  not a gate, so it sits in the pinned header, after `Python version`.
- **The shape pins grow with the kit** (November 22, 2026, step 1, S1-C. Updated November 23,
  2026, S2-B, and November 27, 2026, S5-B). In `packages/checkedtables/tests/test_library_shape.py`, `FIELD_SNAPSHOT` started
  as `{}` and `test_bool_fields_are_page_facts_only` expected `set()`. S2-B pins the fields of
  its 18 dataclasses, each in the commit that creates the class, and the bool test expected
  `{("Word", "bold")}`. The pull request that adds a kit dataclass adds its fields to
  `FIELD_SNAPSHOT`. The one that creates `Column` adds `("Column", "printed")`.
  `kit_dataclasses` counts every dataclass of `checkedtables` that a public name in a public
  module reaches. S5-B created `RawRow`, and the bool test expects `("RawRow", "bold")` beside
  `("Word", "bold")` (decision 20).
- **Kit types imported only under `TYPE_CHECKING`** (November 22, 2026, step 1, S1-C). The shape
  test evaluates a parameter's annotation with each name that does not resolve at run time
  standing for an unknown type. So `amount: "Decimal"`, with `Decimal` imported only under
  `TYPE_CHECKING`, neither raises nor counts, `flag: "bool | Decimal"` still counts as a `bool`
  parameter, and the return type is never read. Dataclass fields still go through
  `typing.get_type_hints`. A kit dataclass with the field `amount: "Decimal"` and that import
  fails `test_bool_fields_are_page_facts_only` with `NameError`, so import a field's type at run
  time.
- **`test_closed_lists_are_pinned` pins `NoteKind`, `PeriodRefusal`, `SkipReason` and
  `UnreadableReason`** (November 22, 2026, step 1, S1-C. Updated November 26, 2026, S4-A). Each
  list's pin lands in the pull request that creates the list, in
  `packages/checkedtables/tests/test_library_shape.py` (`CLAUDE.md`, hard rule 6). S3-C
  creates `NoteKind` and writes the test with its pin. Sweep B pins the readers' refusal codes,
  `PeriodRefusal` in `datadesk.core.fetch` and `SkipReason` in `datadesk.core.listings.titles`.
  S4-A pins `UnreadableReason`, the reasons a cell is `Unreadable`, in `checkedtables.kinds`.
  The other lists that design section 11.4
  pins (`Check`, `RowSel`, `Kind`, `Version`, `Window`, `How`, `Dim` and `Quantity`) do not exist
  yet. The `StrEnum` classes that S2-B created, such as `Severity`, are pinned nowhere, because
  section 11.4 does not list them.
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
    tests still pass. Probed at S1-D with the audit hook in place, on an unconnected socket. S3-D
    put `import ssl` at the top of the root `conftest.py` for the S3 contract suite. The probe
    under the marker failed before that line and passed after it (November 24, 2026).
  - Each blocked call also prints the `UserWarning` that `SocketBlockedError` issues when it is
    created, so `uv run pytest` reports seven warnings. Six are the blocked calls in the isolation
    tests. The seventh comes when a shell test imports urllib3 through boto3. urllib3 opens an
    IPv6 socket at import to set `HAS_IPV6`, the block refuses it, and urllib3 catches the error.
    So under pytest urllib3 runs with `HAS_IPV6` false and resolves IPv4 addresses alone
    (November 24, 2026, S3-D).
- **A core test's package- or session-scoped fixture sees the checkout** (November 22, 2026,
  step 1, S1-D). `_empty_module_working_directory` gives each core test module an empty folder,
  but pytest sets up a package- or session-scoped fixture first, so one that a core test requests
  still runs in the checkout. Probed at S1-D, fixtures of session and package scope found
  `pyproject.toml` in the working directory, and one of module scope did not.
- **How step 1 landed** (November 23, 2026). The owner told the agent to merge the four pull
  requests, and they landed in order as squash commits `fa0eb1d` (#1), `fe83e1e` (#6), `db9ccd6`
  (#8) and `c22c101` (#10). After each squash, `main` had the tree of the head that landed, which is
  the base the next pull request was built on. So a merge of `main` into the next branch with
  `-s ours` moved it onto `main` with no force-push and no change to its tree. Each landing checked
  that the branch was at its verified head, that its patch id was unchanged, and that CI passed on
  the head that landed. The push run of CI on `c22c101`, run 45096500670, passed on Python 3.12 and
  3.14. The owner also kept the build's other choices: the byte pin of `ci.yml`,
  `exclude-newer = "1 week"` and the ruff exclusion of `*.md`. Hard rule 9 in `CLAUDE.md` is
  unchanged. During step 1, fresh owner agents force-pushed, with a lease, branches that an earlier
  agent had created, which crosses the rule's letter. Any change to the rule is the owner's to make.
- **Hard rule 9 changed** (November 23, 2026). The rule said agents never merge. The owner told
  agents to merge the four step 1 pull requests, pull request 16 and pull request 12, then asked
  for the rule to match. An agent now merges a pull request only when the owner tells it to, in
  that session and for that pull request, at the verified head with CI passing. The clauses on
  pushing to `main` and on force-pushing are unchanged, so the force-pushes in the note above
  still cross the rule.
- **Hypothesis writes nothing in the checkout** (November 23, 2026, step 2, S2-B). The root
  `conftest.py` registers and loads one profile with `database=None`, `derandomize=True` and
  `deadline=None`, so every machine draws the same examples. A wider search is a command a person
  runs with another profile. Hypothesis 6.170.15 still writes `.hypothesis/constants` under the
  working directory it was imported in, and its pytest plugin starts the writes during
  collection, so `pytest_configure` points it at a temporary folder with
  `set_hypothesis_home_dir` and `pytest_unconfigure` removes the folder. When the folder could
  not be made, teardown has nothing to remove and leaves the first error to show.
  `test_hypothesis_writes_nothing_in_the_workspace` in `tests/test_gates.py` runs a property test
  in a workspace copy and fails when a `.hypothesis` folder appears there.
- **A test imports a fixture module by its path from the checkout root** (November 24, 2026,
  step 3, S3-B). Under `--import-mode=importlib`, pytest names a test module by its path, as
  `packages.datadesk.tests.core.test_watch`, and makes each folder above it a namespace module.
  So a test imports a fixture beside it as
  `from packages.datadesk.tests.core.fixtures.qcmr_feed import FEED`, with no `__init__.py`.
  ty resolves that name because `[tool.ty.environment] root` in the root `pyproject.toml` ends
  with `"."`. Without it, `uv run ty check` fails with `import-not-found`. A relative import
  passes pytest and fails ty the same way. ruff sorts the import with the outside packages. A
  test under the root `tests/` imports the same way, because `pythonpath = ["."]` in
  `[tool.pytest.ini_options]` puts the checkout on `sys.path` (S4-D). Without that line, the
  whole suite collected `tests/test_word_fixtures.py`, and `uv run pytest tests/` failed on it
  with `ModuleNotFoundError: No module named 'packages'`.
- **The archive bucket from a worktree** (November 24, 2026, step 3, S3-E). The archive bucket
  on R2 holds the 20 QCMR reports from FY2022 Q1 to FY2026 Q4, each under
  `pdf/<sha[:2]>/<sha>.pdf`, and `index.jsonl` lists them. git ignores `.env`, so a worktree has
  none, and a command that needs the bucket runs as
  `uv run --env-file /Users/nhand/DataProjects/phillyledger/.env ...` from the worktree's root.
  The `aws` CLI reads the bucket with the keys passed through the environment, as "Setting up
  R2" in `docs/plans/step-03.md` shows, and never through a profile (hard rule 8).
- **`shell/cli.py` runs past its estimate** (November 26, 2026, S4-E). Counted as design section
  12 counts, `shell/cli.py` holds 309 lines against an estimate of 246. It held 197 at the head
  of S4-D, and `crops_command` with the `crops` command added 112. `shell/report.py` holds 97
  lines against 140, all of them the crop work of step 4.
- **Kit modules against their estimates** (November 23, 2026, step 2. Updated November 25,
  2026, standards sweep B, and November 27, 2026, S5-B). The kit size report counts lines that
  are not blank, a comment or a docstring, as design section 12 counts. At the head of sweep B,
  `uv run python packages/checkedtables/tests/test_library_shape.py` prints
  `checkedtables: 753 lines (budget 3,800), 0 public names (budget 140)`. At the head of sweep A
  it printed 735. Against design section 12.1: `refs` 74 (estimate 60), `kinds` 21 (40),
  `words` 67 (90), `labels` 9 (30), `text` 52 (150), `lines` 52 (120), `cells` 50 (90), `lex`
  181 (230), `records` 119 (140) and `testing` 51 (90). `columns` holds 19 lines for two of its
  ten names (330). `table` holds 58 lines (190) for two of the eight names its row lists,
  `RowKey` and `Finding`, and for `Severity`, which the row does not list. `refs` runs 14 lines
  past its estimate. It writes four comparison methods for `WordRef`, and sweep B added `Sha256`
  with its check. Every other module is under its estimate. At the head of S5-B the report
  prints 1,202 lines: `lines` 76 (120), `pages` 61 (130), `columns` 230 (330), `pipeline` 123
  (130), and `rows` 13 for `RawRow` alone (290).
