import re

from packages.datadesk.tests.fixtures.p1 import RUNS
from tests.test_p1_pages import grid_of

from checkedtables.assemble import assemble
from checkedtables.records import CellRecords
from checkedtables.table import TableId
from datadesk.core.tables.qcmr_positions import TABLE

GROUPS = ("YEAR END ACTUAL", "ADOPTED BUDGET", "MONTH END ACTUAL")
FUNDS = ("General", "Other", "Total")
PRINTED = (
    *((group, fund) for group in GROUPS for fund in FUNDS),
    ("", "ACTUAL (OVER) UNDER BUDGET"),
)


def test_each_p1_caption_is_printed_over_its_column_and_holds_no_title_or_fiscal_year() -> None:
    for run in RUNS:
        _, cut = grid_of(run)
        table = assemble(TableId(TABLE), cut, (), CellRecords((), (), 95.0)).table
        assert table is not None, run.edition
        header = cut.pages[0].header
        assert header[0].text == "TABLE P-1", run.edition
        assert header[4].text.startswith("FOR THE PERIOD ENDING"), run.edition
        assert re.fullmatch(r"FISCAL YEAR \d{4} FISCAL YEAR \d{4}", header[5].text), run.edition
        title = {word.text for line in header[:5] for word in line.words}
        fiscal = {"FISCAL", *re.findall(r"\d{4}", header[5].text)}
        bound = zip(cut.binding.columns, PRINTED, table.columns, strict=True)
        for (spec, lane), (group, own), column in bound:
            where = f"{run.edition} {spec.name}: {column.caption!r}"
            assert lane is not None, where
            assert column.caption == f"{group} {own}".strip(), where
            assert lane.caption.endswith(own), where
            assert not (title | fiscal).intersection(column.caption.split()), where
            assert re.search(spec.caption, column.caption), where
