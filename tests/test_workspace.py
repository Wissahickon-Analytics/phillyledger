import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from hypothesis import settings


def test_workspace_packages_import() -> None:
    for name in ("checkedtables", "phillyledger", "datadesk.core", "datadesk.shell"):
        importlib.import_module(name)


def test_hypothesis_profile_is_derandomized() -> None:
    loaded = settings.default
    assert loaded is not None
    assert loaded.derandomize
    assert loaded.database is None
    assert loaded.deadline is None


def test_teardown_removes_only_the_hypothesis_home_setup_made(tmp_path: Path) -> None:
    conftest = importlib.import_module("conftest")
    conftest.pytest_unconfigure(SimpleNamespace(stash=pytest.Stash()))
    home = tmp_path / "hypothesis-home"
    home.mkdir()
    stash = pytest.Stash()
    stash[conftest.HYPOTHESIS_HOME] = home
    conftest.pytest_unconfigure(SimpleNamespace(stash=stash))
    assert not home.exists()
