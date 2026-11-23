import importlib.util
from itertools import takewhile
from pathlib import Path

REPO = Path(__file__).parents[1]
PROBE_TESTS = REPO / "packages" / "checkedtables" / "tests" / "test_val_probe.py"
VAL_DOSSIER = REPO / "docs" / "evidence" / "dossiers" / "VAL.md"
SECTION = "#### 3.2.1 Acceptance inputs for the new lexer"
HEADER = "| # | Input | Old `parse_amount` | Old `parse_decimal` | Column | New result |"


def probes() -> tuple[tuple[str, str, str, str, str], ...]:
    spec = importlib.util.spec_from_file_location("val_probe", PROBE_TESTS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PROBES


def code(text: str) -> str:
    return f"`` {text} ``" if "`" in text else f"`{text}`"


def table_row(number: int, probe: tuple[str, str, str, str, str]) -> str:
    text, key, old_amount, old_decimal, new = probe
    cells = (str(number), code(text), code(old_amount), code(old_decimal), key, code(new))
    return f"| {' | '.join(cells)} |"


def dossier_rows() -> list[str]:
    _, section = VAL_DOSSIER.read_text().split(f"\n{SECTION}\n", 1)
    lines = section.splitlines()
    start = lines.index(HEADER) + 2
    return list(takewhile(lambda line: line.startswith("|"), lines[start:]))


def test_val_probe_table_is_the_dossier_table() -> None:
    expected = [table_row(number, probe) for number, probe in enumerate(probes(), 1)]
    assert len(expected) == 55
    assert dossier_rows() == expected
