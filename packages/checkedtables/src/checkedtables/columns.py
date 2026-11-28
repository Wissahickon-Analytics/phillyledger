"""The columns a table declares, how each one prints its numbers, and the lanes that hold them."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import date
from re import compile
from statistics import median

from checkedtables.kinds import DashMeaning, PercentSign, Presence, ValueKind
from checkedtables.lines import Line, _is_raised_digit, _value_words
from checkedtables.refs import Box
from checkedtables.rows import RawRow
from checkedtables.table import Finding, Severity
from checkedtables.text import normalize_space
from checkedtables.words import Rule, Word

_VERTICAL = 1.0


@dataclass(frozen=True, slots=True)
class NumberFormat:
    """How a column prints its numbers.

    Attributes
    ----------
    decimals : int or None
        The printed decimals. None means as printed.
    percent : PercentSign
        Whether a cell prints a ``%`` sign.
    """

    decimals: int | None = 0
    percent: PercentSign = PercentSign.ABSENT


@dataclass(frozen=True, slots=True)
class ColumnSpec:
    """One column that a table declares.

    Attributes
    ----------
    name : str
        The stable name that checks and keys use. Never empty.
    caption : str
        A regex searched in the lane's stacked caption. Never empty, since the empty regex
        matches every caption.
    kind : ValueKind
        What the column holds.
    fmt : NumberFormat
        How the column prints its numbers.
    presence : Presence
        Whether the column must be printed.
    dash : DashMeaning
        What a dash in the column means.
    group : str or None
        A regex for the caption that a page prints once over a group of columns, between two
        vertical rules, such as "YEAR END ACTUAL" over three fund columns. The column binds only
        to a lane whose band prints it (`bind_columns`). None for a column with no group.
        Never empty.

    Raises
    ------
    ValueError
        When `name`, `caption` or `group` is empty.
    """

    name: str
    caption: str
    kind: ValueKind
    fmt: NumberFormat = NumberFormat()
    presence: Presence = Presence.REQUIRED
    dash: DashMeaning = DashMeaning.NO_VALUE
    group: str | None = None

    def __post_init__(self) -> None:
        """Refuse a column with an empty name, caption or group."""
        if not self.name:
            raise ValueError(f"a column has an empty name: {self}")
        if not self.caption:
            raise ValueError(f"column {self.name} has an empty caption")
        if self.group == "":
            raise ValueError(f"column {self.name} has an empty group")


@dataclass(frozen=True, slots=True)
class Era:
    """One printed format of a table: the captions that name it and the columns it prints.

    Attributes
    ----------
    name : str
        The era's name, which each `Binding` repeats.
    signature : tuple[str, ...]
        Caption regexes that a page's header must print, all of them. A page that prints none
        of any era's signature is commentary (`cut_pages`), so it is never empty.
    columns : tuple[ColumnSpec, ...]
        The columns, left to right as the page prints them.
    expected : tuple[date, date | None]
        The first and the last date that the era covers, both included, or None for no last
        date. A cross-check only: `choose_era` gives a finding for a date outside it.
    excludes : tuple[str, ...]
        Caption regexes that the header must not print.

    Raises
    ------
    ValueError
        When the signature is empty, two columns share a name, or no column is required.
    """

    name: str
    signature: tuple[str, ...]
    columns: tuple[ColumnSpec, ...]
    expected: tuple[date, date | None]
    excludes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Refuse an era with no signature, two columns of one name, or no required column."""
        if not self.signature:
            raise ValueError(f"era {self.name} has no signature")
        names = [column.name for column in self.columns]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate column names in era {self.name}")
        if all(column.presence is Presence.OPTIONAL for column in self.columns):
            raise ValueError(f"era {self.name} has no required column")


@dataclass(frozen=True, slots=True)
class Lane:
    """A strip of a page between two x positions, which holds one column or one band of them.

    Attributes
    ----------
    x0, x1 : float
        The left and right edges. A word is in the lane when its right edge is after `x0` and
        at or before `x1`, since numbers print right-aligned.
    caption : str
        The header words over the lane, top to bottom. Empty until `bind_columns` reads them.
    """

    x0: float
    x1: float
    caption: str


@dataclass(frozen=True, slots=True)
class Binding:
    """Which lane of a page holds each column of an era.

    Attributes
    ----------
    era : str
        The era's name.
    columns : tuple[tuple[ColumnSpec, Lane | None], ...]
        Each column of the era, in its declared order, with its lane. None for an optional
        column that the page does not print.
    label_right : float
        The x where the label area ends: the left edge of the first lane.
    captions : tuple[tuple[str, str], ...]
        Each column that `bind_columns` bound by caption, in declared order, with the words that
        bound it: the words its group regex found in its band's caption, then the words its
        caption regex found in its lane's caption. Empty from `bind_by_position`.
    """

    era: str
    columns: tuple[tuple[ColumnSpec, Lane | None], ...]
    label_right: float
    captions: tuple[tuple[str, str], ...] = ()


def choose_era(eras: Sequence[Era], header_text: str, on: date) -> Era | Finding:
    """Return the one era whose signature a page's header prints, for a table dated `on`.

    Parameters
    ----------
    eras : Sequence[Era]
        The table's eras.
    header_text : str
        The text of the page's header lines.
    on : date
        The date the table is for, such as the end of its period.

    Returns
    -------
    Era | Finding
        The era whose signature regexes are all found in the header and whose excludes are not.
        Otherwise a BLOCK finding: ``era_not_found`` when no era is, ``several_eras`` when two
        or more are, and ``era_out_of_range`` when `on` is outside the era's `expected` dates.
        A finding's subject is the eras' names.
    """
    found = [
        era
        for era in eras
        if all(compile(caption).search(header_text) for caption in era.signature)
        and not any(compile(caption).search(header_text) for caption in era.excludes)
    ]
    subject = "|".join(era.name for era in eras)
    match found:
        case []:
            return _block("era_not_found", subject, "the header prints no era's whole signature")
        case [era]:
            first, last = era.expected
            if first <= on and (last is None or on <= last):
                return era
            message = f"era {era.name} covers {first} to {last or 'now'}, not {on}"
            return _block("era_out_of_range", subject, message)
        case _:
            names = ", ".join(era.name for era in found)
            return _block("several_eras", subject, f"the header prints the signatures of {names}")


def lanes_from_values(body: Sequence[Line]) -> tuple[Lane, ...]:
    """Return the lanes that the right edges of the cells of a page's value words make.

    A value word is a number, a dash placeholder or N/A with no word right of it on its line
    but other value words and mark words, so "Class 100 Total" seeds no lane. A cell is a run
    of words, each closer than its line's median word height to the word on its left, that
    holds a value word and no other word with a letter. A value word opens a new run when the
    open run holds one, unless it is a raised digit after the word before it, which `lex_cell`
    reads as a mark. So two amounts that stand close are two cells, and "$ 2.8 1" with a raised
    mark is one (VAL-Q28). A mark beside a label, such as the "(1)" about 2 points after "Human
    Services", is in the label's run and seeds no lane (QPOS-Q11). Sorted, a right edge joins
    the open lane when it is within the median height of the cells of the lane's first edge,
    so lanes never chain.

    Parameters
    ----------
    body : Sequence[Line]
        The body lines, with their line number prefixes split off.

    Returns
    -------
    tuple[Lane, ...]
        The lanes, left to right, each with an empty caption. A lane runs from the right edge
        of the lane before it to the rightmost edge of its own cells, so the lanes meet. The
        first lane starts at the leftmost left edge of its cells, so a "$" that opens a cell is
        in it. Empty when no cell seeds one.
    """
    seeds = [box for line in body for box in _seeds(line)]
    if not seeds:
        return ()
    tolerance = median(box.bottom - box.top for box in seeds)
    clusters: list[list[float]] = []
    for edge in sorted(box.x1 for box in seeds):
        if clusters and edge - clusters[-1][0] <= tolerance:
            clusters[-1].append(edge)
        else:
            clusters.append([edge])
    left = min(box.x0 for box in seeds if box.x1 <= clusters[0][-1])
    lanes: list[Lane] = []
    for cluster in clusters:
        lanes.append(Lane(left, cluster[-1], ""))
        left = cluster[-1]
    return tuple(lanes)


def lanes_from_rules(rules: Sequence[Rule], region: Box) -> tuple[Lane, ...]:
    """Return the lanes between the vertical rules that cross a region from top to bottom.

    A rule is vertical when its box is under 1 point wide, and it sits at the middle of its
    box. Pieces of one rule join first: two pieces under 1 point apart across, whose spans meet
    or come under 1 point apart, are one rule, as a page may draw one rule in several pieces.

    Parameters
    ----------
    rules : Sequence[Rule]
        The page's rules.
    region : Box
        The rows that a rule must cross: it counts when it runs from the region's top or above
        to its bottom or below. The region's `x0` and `x1` are not read.

    Returns
    -------
    tuple[Lane, ...]
        One lane between each two neighbouring rules that cross the region, left to right, each
        with an empty caption.
    """
    xs = sorted(
        x for x, top, bottom in _joined(rules) if top <= region.top <= region.bottom <= bottom
    )
    return tuple(Lane(xs[index], xs[index + 1], "") for index in range(len(xs) - 1))


def bind_columns(
    era: Era, header: Sequence[Line], lanes: Sequence[Lane], bands: Sequence[Lane]
) -> Binding | Finding:
    """Bind each lane of a page to the column of an era whose caption it prints.

    A lane's caption is the header words that overlap it, top to bottom. A band's caption is the
    header words whose horizontal middle is in it, top to bottom, so a group caption centered
    over three lanes, and over none of them whole, is whole in its band. A column is a
    candidate for a lane when its caption regex is found in the lane's caption and, when it has
    a group, its group regex is found in the caption of the band that holds the lane's right
    edge. Lanes take their columns left to right. Each takes the candidate not yet bound with
    the longest match, and of candidates with the same caption and group the first declared,
    so "Prior Year Actual" never binds to "Actual". Binding three equal fund captions by order
    would pass a page that swaps two groups (QPOS-Q02).

    Parameters
    ----------
    era : Era
        The era that the page's header names.
    header : Sequence[Line]
        The page's header lines, top to bottom.
    lanes : Sequence[Lane]
        The lanes of the page's values, left to right, as `lanes_from_values` gives them.
    bands : Sequence[Lane]
        The bands of the page's group captions, as `lanes_from_rules` gives them. Empty when
        the page draws no rules, and then no column with a group binds.

    Returns
    -------
    Binding | Finding
        The binding, whose lanes hold their captions and whose `captions` hold the words that
        bound each column. Otherwise a BLOCK finding whose subject is the era's name, the first
        of: ``columns_tie`` when two candidates of different captions or groups match a lane
        equally long, ``column_unbound`` when a required column has no lane, ``lane_unclaimed``
        when a lane has no candidate, and ``columns_out_of_order`` when the bound columns are
        not in their declared order left to right.
    """
    named = [replace(lane, caption=_caption(header, _over(lane))) for lane in lanes]
    groups = [replace(band, caption=_caption(header, _centered(band))) for band in bands]
    bound: dict[str, Lane] = {}
    bound_by: dict[str, str] = {}
    unclaimed: list[Lane] = []
    ties: list[str] = []
    for lane in named:
        group = next((band.caption for band in groups if band.x0 < lane.x1 <= band.x1), None)
        scored = [
            (len(found.group()), column)
            for column in era.columns
            if column.name not in bound
            and (found := compile(column.caption).search(lane.caption))
            and _in_group(column, group)
        ]
        if not scored:
            unclaimed.append(lane)
            continue
        best = max(length for length, _ in scored)
        top = [column for length, column in scored if length == best]
        if len({(column.caption, column.group) for column in top}) > 1:
            ties.append(f"{', '.join(column.name for column in top)} over {lane.caption!r}")
            continue
        bound[top[0].name] = lane
        bound_by[top[0].name] = _bound_caption(top[0], group, lane.caption)
    missing = [
        column.name
        for column in era.columns
        if column.presence is Presence.REQUIRED and column.name not in bound
    ]
    order = [bound[column.name].x1 for column in era.columns if column.name in bound]
    if ties:
        return _block("columns_tie", era.name, f"columns match one lane equally: {ties}")
    if missing:
        return _block("column_unbound", era.name, f"no lane prints {', '.join(missing)}")
    if unclaimed:
        captions = ", ".join(repr(lane.caption) for lane in unclaimed)
        return _block("lane_unclaimed", era.name, f"no column's caption is over {captions}")
    if order != sorted(order):
        printed = sorted(bound, key=lambda name: bound[name].x1)
        message = f"the page prints {', '.join(printed)} left to right"
        return _block("columns_out_of_order", era.name, message)
    columns = tuple((column, bound.get(column.name)) for column in era.columns)
    captioned = tuple((column.name, bound_by[column.name]) for column, lane in columns if lane)
    return Binding(era.name, columns, min(lane.x0 for lane in bound.values()), captioned)


def bind_by_position(era: Era, lanes: Sequence[Lane]) -> Binding | Finding:
    """Bind an era's columns to a page's lanes in order, reading no caption.

    Only for a page whose header a person found illegible and recorded so, since nothing on the
    page then shows which column a lane holds.

    Parameters
    ----------
    era : Era
        The era of the table's other pages.
    lanes : Sequence[Lane]
        The lanes of the page's values, left to right.

    Returns
    -------
    Binding | Finding
        Each column with the lane in its place, the lanes' captions left empty. Otherwise a
        BLOCK finding ``lane_count_differs``, whose subject is the era's name, when the page has
        not one lane for each column.
    """
    if len(lanes) != len(era.columns):
        message = f"{len(lanes)} lanes for the {len(era.columns)} columns of the era"
        return _block("lane_count_differs", era.name, message)
    return Binding(era.name, tuple(zip(era.columns, lanes, strict=True)), lanes[0].x0)


def cut_line(line: Line, binding: Binding, prefix: tuple[Word, ...]) -> RawRow:
    """Cut one body line into its label, the words of each column's lane, and stray words.

    Parameters
    ----------
    line : Line
        The body line, with its line number prefix split off.
    binding : Binding
        The page's binding.
    prefix : tuple[Word, ...]
        The words that `split_line_prefix` took off the line.

    Returns
    -------
    RawRow
        The row. A word whose right edge is at or left of ``binding.label_right`` is a label
        word. Any other word goes to the first bound lane that holds its right edge, or is
        stray. So every word of the line is in exactly one place.
    """
    label: list[Word] = []
    stray: list[Word] = []
    cells: dict[str, list[Word]] = {column.name: [] for column, _ in binding.columns}
    for word in line.words:
        if word.box.x1 <= binding.label_right:
            label.append(word)
            continue
        name = next(
            (
                column.name
                for column, lane in binding.columns
                if lane is not None and lane.x0 < word.box.x1 <= lane.x1
            ),
            None,
        )
        if name is None:
            stray.append(word)
        else:
            cells[name].append(word)
    styles = [word.bold for word in label]
    bold = None if not styles or None in styles else all(styles)
    return RawRow(
        page=line.page,
        prefix=prefix,
        label_words=tuple(label),
        cells=tuple((name, tuple(words)) for name, words in cells.items()),
        stray=tuple(stray),
        bold=bold,
        x0=min((word.box.x0 for word in line.words), default=line.box.x0),
    )


def _block(code: str, subject: str, message: str) -> Finding:
    return Finding(Severity.BLOCK, code, subject, message)


def _height(word: Word) -> float:
    return word.box.bottom - word.box.top


def _seeds(line: Line) -> list[Box]:
    """Return the box of each cell of a line that seeds a lane, leaving out a label's mark."""
    values = _value_words(line.words)
    if not values:
        return []
    height = median(_height(word) for word in line.words)
    runs: list[list[Word]] = []
    for word in line.words:
        joins = bool(runs) and word.box.x0 - runs[-1][-1].box.x1 < height
        if joins and word in values and any(other in values for other in runs[-1]):
            joins = _is_raised_digit((runs[-1][-1], word))
        if joins:
            runs[-1].append(word)
        else:
            runs.append([word])
    return [
        Box.around(word.box for word in run)
        for run in runs
        if any(word in values for word in run)
        and not any(
            word not in values and any(glyph.isalpha() for glyph in word.text) for word in run
        )
    ]


def _joined(rules: Sequence[Rule]) -> list[tuple[float, float, float]]:
    """Return each vertical rule as its x, top and bottom, with touching pieces joined."""
    pieces = sorted(
        ((rule.box.x0 + rule.box.x1) / 2, rule.box.top, rule.box.bottom)
        for rule in rules
        if rule.box.x1 - rule.box.x0 < _VERTICAL
    )
    columns: list[list[tuple[float, float, float]]] = []
    for piece in pieces:
        if columns and piece[0] - columns[-1][0][0] < _VERTICAL:
            columns[-1].append(piece)
        else:
            columns.append([piece])
    joined: list[tuple[float, float, float]] = []
    for column in columns:
        x = column[0][0]
        for _, top, bottom in sorted(column, key=lambda piece: piece[1]):
            if joined and joined[-1][0] == x and top - joined[-1][2] < _VERTICAL:
                joined[-1] = (x, joined[-1][1], max(joined[-1][2], bottom))
            else:
                joined.append((x, top, bottom))
    return joined


def _over(lane: Lane) -> Callable[[Word], bool]:
    return lambda word: word.box.x0 < lane.x1 and word.box.x1 > lane.x0


def _centered(band: Lane) -> Callable[[Word], bool]:
    return lambda word: band.x0 <= (word.box.x0 + word.box.x1) / 2 < band.x1


def _caption(header: Sequence[Line], holds: Callable[[Word], bool]) -> str:
    """Return the header words that `holds` takes, top to bottom and left to right."""
    return normalize_space(
        " ".join(word.text for line in header for word in line.words if holds(word))
    )


def _bound_caption(column: ColumnSpec, group: str | None, caption: str) -> str:
    """Return the words that bind a column: its group's in the band's caption, then its own."""
    grouped = "" if column.group is None or group is None else _touched(column.group, group)
    return " ".join(part for part in (grouped, _touched(column.caption, caption)) if part)


def _touched(regex: str, caption: str) -> str:
    """Return each whole word of a caption that the regex's first match touches.

    A match inside a word gives the whole word, and no match gives the empty string.
    """
    found = compile(regex).search(caption)
    if found is None:
        return ""
    touched: list[str] = []
    start = 0
    for word in caption.split(" "):
        if start < found.end() and found.start() < start + len(word):
            touched.append(word)
        start += len(word) + 1
    return " ".join(touched)


def _in_group(column: ColumnSpec, group: str | None) -> bool:
    """Return whether a column may bind under a band that prints `group`, or under no band."""
    if column.group is None:
        return True
    return group is not None and compile(column.group).search(group) is not None
