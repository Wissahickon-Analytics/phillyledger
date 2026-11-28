from dataclasses import replace
from datetime import date

from checkedtables.columns import ColumnSpec, Era
from checkedtables.kinds import Presence, ValueKind
from checkedtables.lines import PageLines, page_lines
from checkedtables.refs import Box, Sha256
from checkedtables.testing import page_from_text
from checkedtables.words import Rule

SHA = Sha256("a" * 64)
FIRST = r"FIRST\s+YEAR"
SECOND = r"SECOND\s+YEAR"
COLUMNS = (
    ColumnSpec("first_general", "General", ValueKind.COUNT, group=FIRST),
    ColumnSpec("first_other", "Other", ValueKind.COUNT, group=FIRST),
    ColumnSpec("second_general", "General", ValueKind.COUNT, group=SECOND),
    ColumnSpec("second_other", "Other", ValueKind.COUNT, group=SECOND),
    ColumnSpec("over_under", r"\(OVER\)\s*UNDER", ValueKind.COUNT),
)
NAMES = tuple(column.name for column in COLUMNS)
ERA = Era("x1_five", (FIRST, SECOND, r"\(OVER\)"), COLUMNS, (date(2020, 7, 1), None))
ON = date(2024, 6, 30)
OPTIONAL_OVER = replace(
    ERA, columns=(*COLUMNS[:4], replace(COLUMNS[4], presence=Presence.OPTIONAL))
)
RULE_XS = (0.0, 66.0, 204.0, 336.0, 396.0)
VALUE_ENDS = (22, 32, 44, 54, 64)


def at(*placed: tuple[int, str]) -> str:
    row = ""
    for column, text in placed:
        row = row.ljust(column) + text
    return row


def values(label: str, *numbers: str) -> str:
    cells = [(end - len(number), number) for end, number in zip(VALUE_ENDS, numbers, strict=False)]
    return at((0, label), *cells)


def header(groups: tuple[str, str] = ("FIRST YEAR", "SECOND YEAR"), other: str = "Other") -> str:
    return "\n".join(
        (
            "TABLE X-1",
            at((18, groups[0]), (39, groups[1])),
            at(
                (0, "Office"),
                (15, "General"),
                (27, other),
                (37, "General"),
                (49, "Other"),
                (58, "(OVER)"),
            ),
            at((59, "UNDER")),
        )
    )


BODY = "\n".join(
    (values("Parks", "12", "3", "14", "4", "2"), values("Roads", "120", "30", "140", "40", "20"))
)


def grid_page(number: int, text: str) -> PageLines:
    rows = text.count("\n") + 1
    rules = tuple(Rule(Box(x, 12.0, x, 12.0 * rows)) for x in RULE_XS)
    return page_lines(replace(page_from_text(text, SHA, number), rules=rules))
