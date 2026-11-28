from enum import StrEnum

from datadesk.core.vocab import (
    ALL,
    DEFINITIONS,
    DIM_VALUES,
    Dim,
    How,
    Kind,
    Quantity,
    Version,
    Window,
)

LISTS: tuple[tuple[str, type[StrEnum]], ...] = (
    ("kind", Kind),
    ("version", Version),
    ("window", Window),
    ("how", How),
    ("dim", Dim),
    ("quantity", Quantity),
)


def test_every_member_of_the_six_lists_has_a_definition_and_nothing_else_has_one() -> None:
    members = {f"{name}.{member}" for name, enum in LISTS for member in enum}
    assert len(members) == 37
    assert set(DEFINITIONS) == members


def test_each_definition_is_one_sentence_on_one_line() -> None:
    for key, line in DEFINITIONS.items():
        assert line == line.strip(), key
        assert "\n" not in line, key
        assert line[0].isupper() and line.endswith("."), key


def test_residency_and_tax_base_hold_all_and_the_fund_values_come_from_the_registry() -> None:
    assert dict(DIM_VALUES) == {
        Dim.RESIDENCY: ("resident", "nonresident", ALL),
        Dim.TAX_BASE: ("net_income", "gross_receipts", ALL),
    }
