import importlib


def test_workspace_packages_import() -> None:
    for name in ("checkedtables", "phillyledger", "datadesk.core", "datadesk.shell"):
        importlib.import_module(name)
