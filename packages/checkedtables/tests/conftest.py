from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _empty_working_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
