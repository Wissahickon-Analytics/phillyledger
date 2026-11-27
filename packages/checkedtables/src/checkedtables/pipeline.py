"""Cut a table's pages into lines and lanes, and check that every page binds the same columns."""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date
from re import compile
from typing import assert_never

from checkedtables.columns import (
    Binding,
    Era,
    bind_by_position,
    bind_columns,
    choose_era,
    cut_line,
    lanes_from_rules,
    lanes_from_values,
)
from checkedtables.kinds import SourceKind
from checkedtables.lines import Line, PageLines, lines_text
from checkedtables.pages import BodyRule, slice_body
from checkedtables.rows import RawRow
from checkedtables.table import Finding, Severity
from checkedtables.text import split_line_prefix
from checkedtables.words import Word


@dataclass(frozen=True, slots=True)
class Layout:
    """How a table module cuts its pages.

    Attributes
    ----------
    table : str
        The table's name, which every finding of `cut_pages` names.
    eras : tuple[Era, ...]
        The table's printed formats.
    body : BodyRule
        Where the body starts and stops on each page, and which lines are furniture.
    """

    table: str
    eras: tuple[Era, ...]
    body: BodyRule


@dataclass(frozen=True, slots=True)
class CutPage:
    """One page of a table, cut into its header, its raw rows and its furniture.

    Attributes
    ----------
    number : int
        The 1-based page number.
    source : SourceKind
        The text layer or OCR.
    header : tuple[Line, ...]
        The lines above the body.
    binding : Binding
        The page's binding of lanes to columns.
    raws : tuple[RawRow, ...]
        One row for each body line that is not furniture, top to bottom.
    furniture : tuple[Line, ...]
        The lines that `slice_body` made furniture, kept so that every word has a place.
    """

    number: int
    source: SourceKind
    header: tuple[Line, ...]
    binding: Binding
    raws: tuple[RawRow, ...]
    furniture: tuple[Line, ...]


@dataclass(frozen=True, slots=True)
class CutPages:
    """A table's pages, cut under one era and one set of column names.

    Attributes
    ----------
    era : Era
        The era that the first grid page's header names.
    binding : Binding
        The first grid page's binding. Every page binds the same column names.
    pages : tuple[CutPage, ...]
        The grid pages, at least one, in order.
    findings : tuple[Finding, ...]
        The findings that do not stop the table, such as a ``commentary_page`` warning.
    """

    era: Era
    binding: Binding
    pages: tuple[CutPage, ...]
    findings: tuple[Finding, ...]

    @property
    def raws(self) -> tuple[RawRow, ...]:
        """The raw rows of every page, in page order."""
        return tuple(raw for page in self.pages for raw in page.raws)


def cut_pages(
    layout: Layout,
    pages: Sequence[PageLines],
    on: date,
    positional: frozenset[int] = frozenset(),
) -> CutPages | Finding:
    """Cut the pages of a table's run into raw rows, one binding of columns for all of them.

    A page is commentary when its text holds no signature regex of any era. A commentary page
    before the first grid page is not cut and gives a WARN finding. The era is the one that the
    first grid page's header names, and every later grid page must name it too. On each grid
    page, the line number prefix leaves every body line, lanes come from the values, the bands
    of group captions come from the vertical rules that cross the last header line, and each
    body line is cut against the binding. Lanes never come from the rules, since the rules of
    the positions table bound each group of three fund columns, not one column (QPOS-Q01).

    Parameters
    ----------
    layout : Layout
        The table's eras and body rule.
    pages : Sequence[PageLines]
        The pages of the table's run, in order.
    on : date
        The date the table is for, such as the end of its period.
    positional : frozenset[int]
        The pages whose header a person recorded as illegible. Each is a grid page bound by
        position (`bind_by_position`), whatever its text holds.

    Returns
    -------
    CutPages | Finding
        The cut pages. Otherwise the BLOCK finding that stops the table, on its page, with the
        subject ``"<doc sha8>:<table>"``: ``commentary_after_grid`` for a commentary page after
        a grid page, ``no_grid_page`` when no page that the caller did not name prints an
        era's caption, a finding of `choose_era` when a page's header names no one era in
        range, so a grid page that lost one signature caption stops the table,
        ``eras_differ_by_page`` when a page names another era than the first, a finding of
        `bind_columns` or `bind_by_position`, and ``columns_differ_by_page`` when a page binds
        other column names than the first.
    """
    subject = f"{_sha8(pages)}:{layout.table}"
    warnings: list[Finding] = []
    grid: list[PageLines] = []
    for page in pages:
        if page.number in positional or _prints_a_signature(layout.eras, page):
            grid.append(page)
        elif grid:
            message = "it prints no caption of any era's signature, after a page that does"
            return Finding(Severity.BLOCK, "commentary_after_grid", subject, message, page.number)
        else:
            message = "it prints no caption of any era's signature, so it is not cut"
            warnings.append(
                Finding(Severity.WARN, "commentary_page", subject, message, page.number)
            )
    sliced = [(page, *slice_body(page.lines, layout.body)) for page in grid]
    first = next((each for each in sliced if each[0].number not in positional), None)
    if first is None:
        message = "no page of the run that the caller did not name prints an era's caption"
        return Finding(Severity.BLOCK, "no_grid_page", subject, message)
    era = choose_era(layout.eras, lines_text(first[1]), on)
    match era:
        case Era():
            pass
        case Finding():
            return replace(era, subject=subject, page=first[0].number)
        case _:
            assert_never(era)
    cut: list[CutPage] = []
    for page, header, body, furniture in sliced:
        split = [_split(line, layout.body.prefix) for line in body]
        lanes = lanes_from_values([line for _, line in split])
        if page.number in positional:
            bound = bind_by_position(era, lanes)
        else:
            named = choose_era(layout.eras, lines_text(header), on)
            match named:
                case Era() if named.name == era.name:
                    pass
                case Era():
                    message = f"its header names era {named.name}, not {era.name}"
                    return Finding(
                        Severity.BLOCK, "eras_differ_by_page", subject, message, page.number
                    )
                case Finding():
                    return replace(named, subject=subject, page=page.number)
                case _:
                    assert_never(named)
            bands = lanes_from_rules(page.rules, header[-1].box) if header else ()
            bound = bind_columns(era, header, lanes, bands)
        match bound:
            case Binding():
                pass
            case Finding():
                return replace(bound, subject=subject, page=page.number)
            case _:
                assert_never(bound)
        if cut and _names(bound) != _names(cut[0].binding):
            message = f"it binds {_names(bound)}, and page {cut[0].number} {_names(cut[0].binding)}"
            return Finding(Severity.BLOCK, "columns_differ_by_page", subject, message, page.number)
        raws = tuple(cut_line(line, bound, prefix) for prefix, line in split)
        cut.append(CutPage(page.number, page.source, header, bound, raws, furniture))
    return CutPages(era, cut[0].binding, tuple(cut), tuple(warnings))


def _sha8(pages: Sequence[PageLines]) -> str:
    words = (word for page in pages for line in page.lines for word in line.words)
    return next((word.ref.doc_sha256[:8] for word in words), "")


def _prints_a_signature(eras: Sequence[Era], page: PageLines) -> bool:
    text = lines_text(page.lines)
    return any(compile(caption).search(text) for era in eras for caption in era.signature)


def _split(line: Line, prefix: str | None) -> tuple[tuple[Word, ...], Line]:
    return ((), line) if prefix is None else split_line_prefix(line, prefix)


def _names(binding: Binding) -> tuple[str, ...]:
    return tuple(column.name for column, lane in binding.columns if lane is not None)
