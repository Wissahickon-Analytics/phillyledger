import importlib

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
