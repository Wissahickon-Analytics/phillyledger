import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

GATES = (
    "uv run ruff check .",
    "uv run ruff format --check .",
    "uv run ty check",
    "uv run prek run --all-files",
    "uv run pytest",
    "uv run lint-imports",
)

REPO = Path(__file__).parents[1]
CI_WORKFLOW = REPO / ".github" / "workflows" / "ci.yml"
CI_HEADER = """\
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  gates:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.14"]
    steps:
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6.1.0
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2
        with:
          python-version: ${{ matrix.python-version }}
      - run: uv sync --locked
      - name: Python version
        run: |
          version=$(uv run python -c 'import sys; print(*sys.version_info[:2], sep=".")')
          echo "$version"
          test "$version" = "${{ matrix.python-version }}"
      - name: Kit size report
        run: uv run python packages/checkedtables/tests/test_library_shape.py
"""
ALWAYS = "${{ !cancelled() }}"
SRC_FOLDERS = (
    "packages/checkedtables/src",
    "packages/phillyledger/src",
    "packages/datadesk/src",
)
SHAPE_TEST = "packages/checkedtables/tests/test_library_shape.py"
PLANTED_BOOL_PARAMETER = "def planted(flag: bool) -> None: ...\n"


def run_gate(
    workspace: Path, plants: Mapping[str, str], gate: str, extra: tuple[str, ...]
) -> subprocess.CompletedProcess[str]:
    assert gate in GATES, f"{gate!r} is not a gate that CI runs"
    shutil.copytree(REPO / "packages", workspace / "packages")
    shutil.copy(REPO / "pyproject.toml", workspace / "pyproject.toml")
    for path, text in plants.items():
        planted_path = workspace / path
        planted_path.parent.mkdir(parents=True, exist_ok=True)
        with planted_path.open("a") as planted:
            planted.write(text)
    executable, *args = gate.removeprefix("uv run ").split()
    command = [str(Path(sys.executable).parent / executable), *args, *extra]
    pythonpath = os.pathsep.join(str(workspace / folder) for folder in SRC_FOLDERS)
    return subprocess.run(
        command,
        cwd=workspace,
        env={**os.environ, "PYTHONPATH": pythonpath, "COLUMNS": "200"},
        capture_output=True,
        text=True,
        check=False,
    )


def clean_then_planted(
    tmp_path: Path,
    clean: Mapping[str, str],
    planted: Mapping[str, str],
    gate: str,
    extra: tuple[str, ...],
) -> subprocess.CompletedProcess[str]:
    before = run_gate(tmp_path / "clean", clean, gate, extra)
    assert before.returncode == 0, f"clean copy fails {gate}:\n{before.stdout}{before.stderr}"
    return run_gate(tmp_path / "planted", planted, gate, extra)


def test_ci_runs_every_gate() -> None:
    steps = "".join(f"      - if: {ALWAYS}\n        run: {gate}\n" for gate in GATES)
    assert CI_WORKFLOW.read_bytes().decode() == CI_HEADER + steps


def test_planted_boto3_import_fails_lint_imports(tmp_path: Path) -> None:
    core = "packages/datadesk/src/datadesk/core"
    plants = (
        (f"{core}/__init__.py", "import boto3\n"),
        (f"{core}/tables/birt.py", "import boto3\n"),
        (f"{core}/tables/birt.py", "from importlib import import_module\n"),
    )
    for number, (path, text) in enumerate(plants):
        result = clean_then_planted(
            tmp_path / str(number),
            {},
            {path: text},
            "uv run lint-imports",
            ("--no-cache",),
        )
        assert result.returncode != 0, f"{path}: {text}{result.stdout}"
        assert "datadesk core is pure BROKEN" in result.stdout, f"{path}: {text}{result.stdout}"


def test_planted_namespace_folder_fails_ruff_check(tmp_path: Path) -> None:
    folder = "packages/datadesk/src/datadesk/core/planted"
    result = clean_then_planted(
        tmp_path,
        {f"{folder}/__init__.py": "", f"{folder}/module.py": "X = 1\n"},
        {f"{folder}/module.py": "X = 1\n"},
        "uv run ruff check .",
        (),
    )
    assert result.returncode != 0, result.stdout
    assert "INP001" in result.stdout, result.stdout


def test_planted_bool_parameter_fails_shape_test(tmp_path: Path) -> None:
    result = clean_then_planted(
        tmp_path,
        {},
        {"packages/checkedtables/src/checkedtables/__init__.py": PLANTED_BOOL_PARAMETER},
        "uv run pytest",
        ("-p", "no:cacheprovider", SHAPE_TEST),
    )
    assert result.returncode == 1, result.stdout
    assert "AssertionError: planted" in result.stdout, result.stdout


def test_planted_family_helper_parameter_fails_shape_test(tmp_path: Path) -> None:
    result = clean_then_planted(
        tmp_path,
        {},
        {"packages/datadesk/src/datadesk/core/tables/qcmr_common.py": PLANTED_BOOL_PARAMETER},
        "uv run pytest",
        ("-p", "no:cacheprovider", SHAPE_TEST),
    )
    assert result.returncode == 1, result.stdout
    assert "AssertionError: planted" in result.stdout, result.stdout
