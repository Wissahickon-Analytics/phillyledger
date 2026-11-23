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
PURITY_TEST = "tests/test_purity.py"
PLANTED_IMPORT = "from io import FileIO"
PLANTED_HYPOTHESIS_TEST = "packages/checkedtables/tests/test_planted_hypothesis.py"
PROPERTY_AND_EMPTY_FOLDER_TEST = """\
from pathlib import Path

import pytest
from hypothesis import given, strategies


@given(strategies.integers())
def test_planted_property(number):
    assert isinstance(number, int)


@pytest.fixture(scope="module")
def module_setup_listing():
    return list(Path.cwd().iterdir())


def test_working_directory_is_empty(module_setup_listing):
    assert list(Path.cwd().iterdir()) == []
    assert module_setup_listing == []
"""
DATADESK_CORE_TESTS = "packages/datadesk/tests/core"
PLANTED_SOCKET_TEST = f"{DATADESK_CORE_TESTS}/test_planted_socket.py"
PLANTED_SOCKET_SUMMARY = (f"FAILED {PLANTED_SOCKET_TEST}::", f"ERROR {PLANTED_SOCKET_TEST}::")
SOCKET_IN_TEST = "import socket\n\n\ndef test_planted():\n    {}\n"
EARLY_BOUND_SOCKET_IN_TEST = "from socket import socket\n\n\ndef test_planted():\n    {}\n"
SOCKET_AFTER_MODULE_FIXTURE_YIELD = """\
import socket

import pytest


@pytest.fixture(scope="module", autouse=True)
def planted_fixture():
    yield
    {}


def test_planted():
    pass
"""


def run_gate(
    workspace: Path, plants: Mapping[str, str], gate: str, extra: tuple[str, ...]
) -> subprocess.CompletedProcess[str]:
    assert gate in GATES, f"{gate!r} is not a gate that CI runs"
    shutil.copytree(REPO / "packages", workspace / "packages")
    shutil.copy(REPO / "pyproject.toml", workspace / "pyproject.toml")
    shutil.copy(REPO / "conftest.py", workspace / "conftest.py")
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
        env={
            **os.environ,
            "PYTHONPATH": pythonpath,
            "COLUMNS": "200",
            "NO_COLOR": "1",
            "PY_COLORS": "0",
            "TERM": "dumb",
        },
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


def folders_missing_init(source_root: Path) -> list[Path]:
    folders = {
        source_root / folder
        for module in source_root.rglob("*.py")
        for folder in module.relative_to(source_root).parents
        if folder != Path()
    }
    return sorted(folder for folder in folders if not (folder / "__init__.py").is_file())


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


def test_source_folders_are_packages(tmp_path: Path) -> None:
    module = "import subprocess\n"
    probes = {
        "plain": ({"pkg/sneaky/mod.py": module}, ["pkg/sneaky"]),
        "shebang": ({"pkg/sneaky/mod.py": f"#!/usr/bin/env python3\n{module}"}, ["pkg/sneaky"]),
        "venv": ({"pkg/venv/mod.py": module}, ["pkg/venv"]),
        "parent": (
            {"pkg/outer/inner/__init__.py": "", "pkg/outer/inner/mod.py": module},
            ["pkg/outer"],
        ),
        "packages": ({"top.py": module, "pkg/sub/__init__.py": "", "pkg/sub/mod.py": module}, []),
    }
    for name, (files, expected) in probes.items():
        root = tmp_path / name
        for path, text in {"pkg/__init__.py": "", **files}.items():
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_text(text)
        assert folders_missing_init(root) == [root / folder for folder in expected], name

    missing = [folder for src in SRC_FOLDERS for folder in folders_missing_init(REPO / src)]
    assert missing == [], f"import-linter skips these folders, add __init__.py: {missing}"


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


def test_planted_import_fails_purity_test(tmp_path: Path) -> None:
    purity_test = {PURITY_TEST: (REPO / PURITY_TEST).read_text()}
    result = clean_then_planted(
        tmp_path,
        purity_test,
        {**purity_test, "packages/datadesk/src/datadesk/core/tables/birt.py": PLANTED_IMPORT},
        "uv run pytest",
        ("-p", "no:cacheprovider", PURITY_TEST),
    )
    assert result.returncode == 1, result.stdout
    lines = result.stdout.splitlines()
    assert any("birt.py:" in line and PLANTED_IMPORT in line for line in lines), result.stdout


def test_hypothesis_writes_nothing_in_the_workspace(tmp_path: Path) -> None:
    result = run_gate(
        tmp_path,
        {PLANTED_HYPOTHESIS_TEST: PROPERTY_AND_EMPTY_FOLDER_TEST},
        "uv run pytest",
        ("-p", "no:cacheprovider", PLANTED_HYPOTHESIS_TEST),
    )
    assert result.returncode == 0, result.stdout
    assert "2 passed" in result.stdout, result.stdout
    assert sorted(tmp_path.rglob(".hypothesis")) == []


def run_socket_plant(
    tmp_path: Path, module: str, constructor: str
) -> subprocess.CompletedProcess[str]:
    return clean_then_planted(
        tmp_path,
        {PLANTED_SOCKET_TEST: module.format(f"assert {constructor}")},
        {PLANTED_SOCKET_TEST: module.format(f"{constructor}()")},
        "uv run pytest",
        ("-p", "no:cacheprovider", DATADESK_CORE_TESTS),
    )


def planted_socket_summary(result: subprocess.CompletedProcess[str]) -> list[str]:
    lines = result.stdout.splitlines()
    return [line for line in lines if line.startswith(PLANTED_SOCKET_SUMMARY)]


def test_planted_socket_call_fails_pytest(tmp_path: Path) -> None:
    plants = (
        (SOCKET_IN_TEST, "socket.socket"),
        (SOCKET_IN_TEST, "socket.SocketType"),
        (SOCKET_AFTER_MODULE_FIXTURE_YIELD, "socket.socket"),
    )
    for number, (module, constructor) in enumerate(plants):
        result = run_socket_plant(tmp_path / str(number), module, constructor)
        assert result.returncode == 1, result.stdout
        summary = planted_socket_summary(result)
        assert any("SocketBlockedError" in line for line in summary), result.stdout


def test_planted_early_bound_socket_fails_pytest(tmp_path: Path) -> None:
    result = run_socket_plant(tmp_path, EARLY_BOUND_SOCKET_IN_TEST, "socket")
    assert result.returncode == 1, result.stdout
    summary = planted_socket_summary(result)
    assert any("SocketBlockedError" in line for line in summary), result.stdout
