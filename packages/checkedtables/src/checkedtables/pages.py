"""Find the run of pages that holds a table, and split each page into header, body and furniture."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from re import compile

from checkedtables.lines import Line, PageLines, lines_text
from checkedtables.table import Finding, Severity
from checkedtables.text import split_line_prefix

_BAND = 2


@dataclass(frozen=True, slots=True)
class PageRun:
    """The pages from `first` to `last`, both included, that hold one table.

    Attributes
    ----------
    first, last : int
        The 1-based numbers of the first and last page in the publisher file.
    """

    first: int
    last: int

    @property
    def pages(self) -> range:
        """The page numbers of the run, in order."""
        return range(self.first, self.last + 1)

    def take(self, pages: Sequence[PageLines]) -> tuple[PageLines, ...]:
        """Return the pages of the run, in the order given.

        Parameters
        ----------
        pages : Sequence[PageLines]
            The pages of the document, such as every page that `page_lines` read.
        """
        return tuple(page for page in pages if page.number in self.pages)


@dataclass(frozen=True, slots=True)
class BodyRule:
    """Where a table's body starts and stops on a page, and which of its lines are furniture.

    Attributes
    ----------
    start : Callable[[Line], bool]
        True for the first body line. Every line above it is header.
    stop : Callable[[Line], bool] or None
        True for the last body line, which stays in the body. None runs the body to the end of
        the page.
    drop : tuple[str, ...]
        Regexes searched in each body line's text. A line that one finds is furniture.
    prefix : str or None
        A regex that a leading line number word fullmatches, such as ``"I|[0-9]{1,2}"`` (QPOS-Q08).
        A body line of only such words is furniture.
    """

    start: Callable[[Line], bool]
    stop: Callable[[Line], bool] | None
    drop: tuple[str, ...] = ()
    prefix: str | None = None


def header_band(lines: Sequence[Line], n: int) -> str:
    """Return the text of a page's first `n` lines, one per text line.

    Parameters
    ----------
    lines : Sequence[Line]
        The page's lines, top to bottom.
    n : int
        How many lines from the top make the band.
    """
    return lines_text(lines[:n])


def find_runs(pages: Sequence[PageLines], matches: Callable[[str], bool]) -> tuple[PageRun, ...]:
    """Return every longest run of consecutive pages whose two-line header band matches.

    A table of contents that names the table on its third line holds it outside its band, so it
    starts no run.

    Parameters
    ----------
    pages : Sequence[PageLines]
        The pages of one document, in ascending order. They need not be contiguous: a page
        that is missing ends a run.
    matches : Callable[[str], bool]
        True for the band text of a page of the table, as `header_band` gives it.

    Returns
    -------
    tuple[PageRun, ...]
        The runs, in page order. Empty when no band matches.
    """
    runs: list[PageRun] = []
    for page in pages:
        if not matches(header_band(page.lines, _BAND)):
            continue
        if runs and runs[-1].last == page.number - 1:
            runs[-1] = PageRun(runs[-1].first, page.number)
        else:
            runs.append(PageRun(page.number, page.number))
    return tuple(runs)


def only_run(runs: Sequence[PageRun], subject: str) -> PageRun | Finding:
    """Return the one run of a table, or a BLOCK finding when there is none or more than one.

    A table module that expects its table to break around an inserted page joins the runs with
    a rule of its own and says why.

    Parameters
    ----------
    runs : Sequence[PageRun]
        The runs that `find_runs` found.
    subject : str
        The subject of a finding, as ``"<doc sha8>:<table>"``.

    Returns
    -------
    PageRun | Finding
        The run, or a finding: ``table_not_found`` for no run, ``several_runs`` for two or
        more.
    """
    match runs:
        case [run]:
            return run
        case []:
            return Finding(Severity.BLOCK, "table_not_found", subject, "no page band names it")
        case _:
            spans = ", ".join(f"{run.first}-{run.last}" for run in runs)
            message = f"{len(runs)} runs of pages name it in their band: {spans}"
            return Finding(Severity.BLOCK, "several_runs", subject, message)


def slice_body(
    lines: Sequence[Line], body: BodyRule
) -> tuple[tuple[Line, ...], tuple[Line, ...], tuple[Line, ...]]:
    """Split a page's lines into its header, its body and its furniture.

    Parameters
    ----------
    lines : Sequence[Line]
        The page's lines, top to bottom.
    body : BodyRule
        The table's rule for its body.

    Returns
    -------
    tuple[tuple[Line, ...], tuple[Line, ...], tuple[Line, ...]]
        The header, the body and the furniture, each top to bottom, with every line in one of
        them. The header is the lines above the first line that ``body.start`` takes, or every
        line when it takes none. The body runs from that line to the first line at or after it
        that ``body.stop`` takes, or to the page end. Furniture is each body line that a
        ``body.drop`` regex finds or that holds only ``body.prefix`` words, such as a page
        number at the foot, and every line below the stop line, such as a notice.
    """
    start = next((index for index, line in enumerate(lines) if body.start(line)), len(lines))
    stop = body.stop
    last = next(
        (index for index in range(start, len(lines)) if stop is not None and stop(lines[index])),
        len(lines) - 1,
    )
    region = lines[start : last + 1]
    kept = tuple(line for line in region if not _furniture(line, body))
    dropped = tuple(line for line in region if _furniture(line, body))
    return tuple(lines[:start]), kept, (*dropped, *lines[last + 1 :])


def _furniture(line: Line, body: BodyRule) -> bool:
    if any(compile(pattern).search(line.text) for pattern in body.drop):
        return True
    return body.prefix is not None and not split_line_prefix(line, body.prefix)[1].words
