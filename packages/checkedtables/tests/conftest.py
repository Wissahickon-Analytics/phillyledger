from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(scope="module", autouse=True)
def _empty_module_working_directory(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(tmp_path_factory.mktemp("module"))
        yield


@pytest.fixture(autouse=True)
def _empty_working_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
