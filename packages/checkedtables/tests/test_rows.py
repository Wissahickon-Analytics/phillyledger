from checkedtables.lines import group_lines
from checkedtables.refs import Sha256
from checkedtables.rows import RawRow
from checkedtables.testing import page_from_text

SHA = Sha256("a" * 64)


def test_a_raw_row_has_values_when_a_lane_holds_a_word() -> None:
    (label, value) = group_lines(page_from_text("Taxes 12", SHA, 1))[0].words
    with_value = RawRow(1, (), (label,), (("budget", (value,)), ("actual", ())), (), False, 0.0)
    assert with_value.has_values()
    heading = RawRow(1, (), (label,), (("budget", ()), ("actual", ())), (value,), False, 0.0)
    assert not heading.has_values()
