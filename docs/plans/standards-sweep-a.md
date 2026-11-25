# Standards sweep A

On November 25, 2026 the owner asked for typer on the command line, docstrings on the code, and
the type rules of the book Robust Python. Pull request 39 wrote those rules into `CLAUDE.md`
(Code) and section 8 of `docs/principles.md`. The code built in steps 1 to 3 does not meet them
yet. This sweep brings it to the typer and docstring rules without changing a signature. Sweep
B, a later pull request, gives values such as a sha256 their own types and changes the design.

## Track

Light track. The owner chose it on November 25, 2026, with the words "Light track". A docstring
changes no value, label, period or release step. The kit's public shape is its names, signatures
and fields, and a docstring changes none of them. The command line keeps its one command, its
source argument and its `--saved` option. It loses `-h` and the abbreviations of `--saved` that
`argparse` took, such as `--sav`, which are now usage errors. Some stops print or exit
differently. Design section 9 says what each exit code means, and the "Standards sweep A"
section of `docs/deviations/step-03.md` says what changed.

## The pull request

One pull request on the branch `standards/sweep-a`, based on `docs/code-standards` at `36807de`.
It is not part of step 3's GitHub stack, as pull request 39 is not. It needs no call to R2 and no
request to the City. It changes neither `index.jsonl` nor the inventory, and it changes no test
of a step 3 clause. Its one changed test assertion is in `test_main_requires_a_saved_folder`,
which `docs/plans/step-03.md` does not name.

## What it does, and the test or run that proves each part

| Part | What changes | Proof |
| --- | --- | --- |
| Size report | `source_lines` in `packages/checkedtables/tests/test_library_shape.py` leaves out the lines of each module, class and function docstring, found with `ast`. | A test counts a short module with and without its docstrings. The report line before and after, in the pull request. |
| ruff | `D` applies to `packages/*/src/**` in all three packages, and `ignore` drops `D100` and `D104`. Tests stay exempt. | At `36807de`, ruff with these settings reports 160 findings: 65 `D100`, 42 `D101`, 24 `D103`, 16 `D102`, 9 `D104` and 4 `D105`. The count falls to zero at the head. |
| Docstrings | A numpy docstring on every module and package of the three packages, and on the 82 public classes, functions and methods of `datadesk` and its 4 magic methods. A private helper gets one when its name and types do not say why it exists. The 45 files with no code at `36807de`, 36 modules and 9 package `__init__.py` files, get the job that design section 12 gives them. The 75 docstrings of `checkedtables`, on 54 public names and 21 magic methods, stay. | `uv run ruff check .` passes. Removing one module docstring and one package docstring each fails it. |
| typer | `cli.py` builds the command line with typer. `fetch` is a typer command that does what `main` does now: reads the clock, loads settings, builds `Deps`, calls `fetch_command` and prints through `hide_keys`. Its `try` covers everything after the settings load, the print of the plan included, so nothing it prints from then on skips `hide_keys`. A refusal prints its message and raises `typer.Exit(1)`. `main(argv) -> int` runs the app and returns the code of the `SystemExit` it raises. | The `main` tests of `test_fetch_command.py` pass, `test_main_prints_neither_r2_key_when_the_plan_it_prints_holds_both` among them. `test_main_requires_a_saved_folder` asserts that `main` returns 2 where it asserted a raised `SystemExit`. The runs of the real script below. |
| Only `cli.py` imports typer | A ninth import-linter contract forbids `typer` in all three packages, with `datadesk.shell.cli -> typer` ignored. Design section 12.5 gains it. | `uv run lint-imports` passes, and fails with `import typer` planted in `datadesk.shell.run_fetch`. |
| Design | Section 9, the prose on `main` in section 4.2, the `cli.py` excerpts of sections 4.2, 4.3 and 4.5, and the `cli.py` row of section 12.3 with the totals it feeds say what the runs show. | The runs below, quoted in the pull request. |
| Deviation | A "Standards sweep A" section at the end of `docs/deviations/step-03.md`, since the sweep changes code that step 3 built. | |
| Cleanup | The note "The code standards changed" in `docs/progress.md` and the dated bullet at the end of the Code section of `CLAUDE.md` shrink to what sweep B still owes. The two progress notes on kit sizes say what the report prints at the head. | |

## Choices made from runs

All runs are from November 25, 2026, in a scratch script that imitates `cli.py`.

- **Version.** `typer>=0.28,<0.29`. PyPI lists `pydantic>=2.5.3` among the dependencies of
  typer 0.29.0, released November 9, 2026, and none for 0.28.0. typer 0.28.0 and 0.29.2 gave
  the same output and exit code for every case below. The owner was shown this recommendation:
  keep the cap for sweep A, and decide pydantic when a step builds the big TOML loaders, most
  likely step 5, with a run that compares a hand-written loader to a strict pydantic loader on
  the same input. He answered "Keep the cap" on November 25, 2026. Asked "Should section 8.7 say
  pydantic is undecided for datadesk until step 5?", he answered "Yes, update 8.7", and section
  8.7 of `docs/principles.md` now says so.
- **A callback.** typer runs an app with one command as that command. Without a callback the
  usage line read `datadesk [OPTIONS] {source}`, and `datadesk fetch qcmr --saved x` stopped with
  `Error: Got unexpected extra argument(s) (qcmr)`, because `fetch` was read as the source. With
  `@app.callback()` it reads `datadesk fetch [OPTIONS] {source}`.
- **`rich_markup_mode=None`.** typer prints help and usage errors through rich when rich is
  installed, and typer depends on rich. The usage error then sat in a box drawn with box
  characters. With `None`, click's plain lines print: `Error: Missing option '--saved'.`
- **`add_completion=False`.** `--install-completion` writes `~/.bashrc` or `~/.zshrc`
  (`typer/_completion_shared.py`), an effect outside the checkout that no design section lists.
  The tool has one user and one command.
- **`pretty_exceptions_enable=False`.** `CLAUDE.md` asks for it. `Typer.__call__` sets
  `sys.excepthook` to typer's hook on every call, and with this off the hook prints Python's
  standard traceback.

## The stops

Design section 9 says what each exit code means, and the "Standards sweep A" section of
`docs/deviations/step-03.md` says which stops changed and the runs that show it. The build runs
the real `datadesk` script for each stop and records the command, the output and the exit code
in the pull request. No run may call R2.

- A refused input runs with placeholder `DATADESK_R2_*` values and a saved folder with no
  `responses.tsv`. `MissingSettings` runs with no values set.
- A failed effect runs against the held saved folder, in a scratch copy of the checkout, with
  the endpoint set to a closed port on `127.0.0.1`.
- A bug and each Ctrl-C come from a `raise` planted in a scratch copy, and a Ctrl-C during the
  fetch also comes from a SIGINT sent to the run of a failed effect.

## Files

- `docs/plans/standards-sweep-a.md`, this plan, as the first commit.
- `pyproject.toml`, `packages/datadesk/pyproject.toml` and `uv.lock`.
- `packages/datadesk/src/datadesk/shell/cli.py`.
- Docstrings, and no code, in every other module under `packages/*/src`.
- `packages/checkedtables/tests/test_library_shape.py` and
  `packages/datadesk/tests/shell/test_fetch_command.py`.
- `docs/design.md`, `docs/deviations/step-03.md`, `docs/progress.md`, `docs/principles.md`
  and `CLAUDE.md`.

## Verification

- `just gates` at the head, and the CI run of the pull request.
- The runs of the real script above, and each planted failure.
- Codex verifies and reviews the pull request once (`codex-review pr 3 docs/code-standards`).
  Step 3 is the step whose code changes, so the review also runs step 3's check at the head.
