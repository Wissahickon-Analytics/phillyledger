import re

from packages.datadesk.tests.fixtures.p1 import RUNS
from tests.test_p1_pages import grid_of

from checkedtables.assemble import assemble
from checkedtables.records import CellRecords
from checkedtables.table import TableId
from datadesk.core.tables.qcmr_positions import COLUMNS, TABLE

PRINTED = (
    *(
        f"{group} {fund}"
        for group in ("YEAR END ACTUAL", "ADOPTED BUDGET", "MONTH END ACTUAL")
        for fund in ("General", "Other", "Total")
    ),
    "(OVER) UNDER",
)


def test_each_p1_caption_is_the_words_that_bound_its_column_and_no_title_word() -> None:
    for run in RUNS:
        _, cut = grid_of(run)
        table = assemble(TableId(TABLE), cut, (), CellRecords((), (), 95.0)).table
        assert table is not None, run.edition
        title = cut.pages[0].header[:5]
        assert title[0].text == "TABLE P-1", run.edition
        assert title[-1].text.startswith("FOR THE PERIOD ENDING"), run.edition
        title_words = {word.text for line in title for word in line.words}
        captions = tuple(column.caption for column in table.columns)
        assert captions == PRINTED, run.edition
        for spec, caption in zip(COLUMNS, captions, strict=True):
            where = f"{run.edition} {spec.name}: {caption!r}"
            assert not title_words.intersection(caption.split()), where
            assert re.search(spec.caption, caption), where
