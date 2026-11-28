"""The QCMR positions table, P-1 (design section 5.1).

The table prints ten count columns: General, Other and Total under each of three group
captions, then the variance (QPOS-Q01). The captions are written as the archived reports of
FY2022 to FY2026 print them, in capitals. Each fund column binds by its own caption inside the
rule band of its group, never by its place in the row (QPOS-Q02). The tenth column prints
"MONTH END", "ACTUAL (OVER)" and "UNDER BUDGET" on three header lines and has no group, so its
caption regex starts at "MONTH" to caption the column with all three.
"""

from datetime import date

from checkedtables.columns import ColumnSpec, Era, NumberFormat
from checkedtables.kinds import ValueKind

TABLE = "qcmr_positions"
_COUNT = NumberFormat(decimals=0)
_GROUPS = (
    ("prior", r"YEAR\s+END\s+ACTUAL"),
    ("adopted", r"ADOPTED\s+BUDGET"),
    ("actual", r"MONTH\s+END\s+ACTUAL"),
)
_FUNDS = (("general", "General"), ("other", "Other"), ("total", "Total"))
_OVER = r"\(OVER\)"

COLUMNS: tuple[ColumnSpec, ...] = (
    *(
        ColumnSpec(f"{group}_{fund}", caption, ValueKind.COUNT, _COUNT, group=printed)
        for group, printed in _GROUPS
        for fund, caption in _FUNDS
    ),
    ColumnSpec("over_under", rf"MONTH\s+END\s+ACTUAL\s+{_OVER}\s*UNDER", ValueKind.COUNT, _COUNT),
)
ERAS = (
    Era(
        "p1_ten_columns",
        signature=(*(printed for _, printed in _GROUPS), _OVER),
        columns=COLUMNS,
        expected=(date(2007, 7, 1), None),
    ),
)
