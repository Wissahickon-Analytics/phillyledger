"""The one static list of tables (design section 2.2, change 14).

`TABLES` is a tuple literal, so importing the module runs no code beyond building it, and no
code finds a table by the text of a module name. Each table module joins with one entry.
"""

from collections.abc import Callable
from dataclasses import dataclass

from checkedtables.columns import Era
from checkedtables.words import Document
from datadesk.core.context import ParseContext, ParseResult
from datadesk.core.measures import MeasureSet, Scope
from datadesk.core.tables import qcmr_positions


@dataclass(frozen=True, slots=True)
class TableEntry:
    """One table that the parsers read and the release publishes.

    Attributes
    ----------
    name : str
        The table's name, which its `TableId`, its row schema and its records use.
    dataset : str
        The release dataset the table feeds.
    series : str
        The `EditionKey.series` of the files that print the table.
    parse : Callable[[Document, ParseContext], ParseResult]
        Reads the table from the words of one whole file.
    eras : tuple[Era, ...]
        The table's printed formats.
    measures : Callable[[Era, Scope], MeasureSet]
        Describes each column of an era, for one edition and one table instance.
    """

    name: str
    dataset: str
    series: str
    parse: Callable[[Document, ParseContext], ParseResult]
    eras: tuple[Era, ...]
    measures: Callable[[Era, Scope], MeasureSet]


TABLES: tuple[TableEntry, ...] = (
    TableEntry(
        qcmr_positions.TABLE,
        "qcmr_positions",
        "qcmr",
        qcmr_positions.parse,
        qcmr_positions.ERAS,
        qcmr_positions.measures,
    ),
)


def entry(name: str) -> TableEntry:
    """Return the entry of the table called `name`.

    Raises
    ------
    KeyError
        When no entry has the name.
    """
    for table in TABLES:
        if table.name == name:
            return table
    raise KeyError(name)
