import pytest

from checkedtables.columns import ColumnSpec
from checkedtables.kinds import ValueKind


def test_column_spec_needs_a_name_and_a_caption() -> None:
    for name, caption, message in (("", "Budget", "empty name"), ("budget", "", "empty caption")):
        with pytest.raises(ValueError, match=message):
            ColumnSpec(name, caption, ValueKind.MONEY)
    assert ColumnSpec("b", "B", ValueKind.MONEY).caption == "B"
