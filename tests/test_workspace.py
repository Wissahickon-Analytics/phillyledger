import importlib
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from hypothesis import settings

ROOT_CONFTEST = Path(__file__).parents[1] / "conftest.py"


def test_workspace_packages_import() -> None:
    for name in ("checkedtables", "phillyledger", "datadesk.core", "datadesk.shell"):
        importlib.import_module(name)


def test_hypothesis_profile_is_derandomized() -> None:
    assert settings.get_current_profile_name() == "phillyledger"
    loaded = settings.default
    assert loaded is not None
    assert loaded.derandomize
    assert loaded.database is None
    assert loaded.deadline is None


def test_teardown_removes_only_the_hypothesis_home_setup_made(
    pytestconfig: pytest.Config, tmp_path: Path
) -> None:
    conftest = pytestconfig.pluginmanager.get_plugin(str(ROOT_CONFTEST))
    assert isinstance(conftest, ModuleType)
    conftest.pytest_unconfigure(SimpleNamespace(stash=pytest.Stash()))
    home = tmp_path / "hypothesis-home"
    home.mkdir()
    stash = pytest.Stash()
    stash[conftest.HYPOTHESIS_HOME] = home
    conftest.pytest_unconfigure(SimpleNamespace(stash=stash))
    assert not home.exists()
