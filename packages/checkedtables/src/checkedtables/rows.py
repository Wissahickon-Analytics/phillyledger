"""Match a table's rows to its declared row schema, and report stray words."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import assert_never

from checkedtables.kinds import Presence
from checkedtables.labels import Label
from checkedtables.lines import Line, _value_words
from checkedtables.table import Finding, RowKey, RowKind, Severity
from checkedtables.text import normalize_label, parse_label, squash
from checkedtables.words import Word


@dataclass(frozen=True, slots=True)
class RawRow:
    """One body line of a page, cut into its label, its cells and the words in neither.

    `cut_line` builds it. Every word of the line is in exactly one of `prefix`, `label_words`,
    `cells` and `stray`.

    Attributes
    ----------
    page : int
        The 1-based page number.
    prefix : tuple[Word, ...]
        The leading words that ``BodyRule.prefix`` split off, such as a printed line number.
    label_words : tuple[Word, ...]
        The words left of the binding's ``label_right``, a mark beside the label included.
    cells : tuple[tuple[str, tuple[Word, ...]], ...]
        Each column of the binding, in its declared order, with the words whose right edge is
        in its lane. A column that the page does not print has no words.
    stray : tuple[Word, ...]
        The words right of the label area that are in no lane.
    bold : bool or None
        Whether every label word is bold. None when a label word carries no style, as on an
        OCR page, or when the row has no label word.
    x0 : float
        The left edge of the row's first word after its prefix.
    """

    page: int
    prefix: tuple[Word, ...]
    label_words: tuple[Word, ...]
    cells: tuple[tuple[str, tuple[Word, ...]], ...]
    stray: tuple[Word, ...]
    bold: bool | None
    x0: float

    def has_values(self) -> bool:
        """Return whether a lane holds a word of the row."""
        return any(words for _, words in self.cells)


class Truncation(StrEnum):
    """Whether a printed label may match a schema label it is only the start of.

    Attributes
    ----------
    NONE
        A label matches only by its normalized or squashed form.
    UNIQUE_PREFIX
        A label that matches no form may also match the one schema label it is the start of,
        for pages that cut labels at the column's width (MCITY-Q21).
    """

    NONE = "none"
    UNIQUE_PREFIX = "unique_prefix"


@dataclass(frozen=True, slots=True)
class RowDef:
    """One row that a closed table declares.

    Attributes
    ----------
    key : RowKey
        The key that a matched row gets.
    kind : RowKind
        What the row is in the table.
    labels : tuple[str, ...]
        The labels the row prints under. ``schema_for`` fills them from the schema's labels or
        from the registry's names. ``("",)`` is a row that prints no label.
    parent : RowKey or None
        The key of the row it adds into. None hangs it under the schema's root.
    within : RowKey or None
        The block that must be open for the row to match: the row of that key has matched and
        no row outside its block has matched since.
    follows : RowKey or None
        For a row with no label alone: it matches only the line right after the row of this
        key.
    presence : Presence
        Whether a page of the table must print it.
    entity : str or None
        The registry entity it names. Such a row's labels come from the registry.
    unit : str or None
        A unit that holds for this row alone, such as the positions rows of O-3.

    Raises
    ------
    ValueError
        When `follows` is set on a row that prints a label.
    """

    key: RowKey
    kind: RowKind
    labels: tuple[str, ...]
    parent: RowKey | None = None
    within: RowKey | None = None
    follows: RowKey | None = None
    presence: Presence = Presence.REQUIRED
    entity: str | None = None
    unit: str | None = None

    def __post_init__(self) -> None:
        """Refuse `follows` on a row that prints a label."""
        if self.follows is not None and self.labels != ("",):
            raise ValueError(f"{self.key}: only an unlabeled row may use follows")


@dataclass(frozen=True, slots=True)
class RowSchema:
    """The rows a closed table prints in one edition.

    Attributes
    ----------
    table : str
        The table's name, which the findings of `match_rows` name.
    rows : tuple[RowDef, ...]
        The rows, already narrowed to one edition.
    root : RowKey or None
        The key of the grand total, which every row with no parent hangs under. None for a
        table with no root.
    drop : tuple[str, ...]
        Regexes for the body lines that are furniture, for the table's ``BodyRule.drop``.
    truncation : Truncation
        Whether a printed label may match a schema label it is the start of.

    Raises
    ------
    ValueError
        When two rows share a key.
    """

    table: str
    rows: tuple[RowDef, ...]
    root: RowKey | None = None
    drop: tuple[str, ...] = ()
    truncation: Truncation = Truncation.NONE

    def __post_init__(self) -> None:
        """Refuse two rows of one key."""
        keys = [row.key for row in self.rows]
        if len(keys) != len(set(keys)):
            raise ValueError(f"duplicate RowDef key in {self.table}")


@dataclass(frozen=True, slots=True)
class KeyedRow:
    """A raw row with the key, kind and parent that its match gave it.

    Attributes
    ----------
    raw : RawRow
        The row as cut, or two rows joined when a label wraps onto the next line.
    label : Label
        The label as printed, read from the row's prefix and label words.
    key : RowKey
        The key of the row definition it matched.
    kind : RowKind
        What the row is in the table.
    parent : RowKey or None
        The key of the row it adds into, or None for the root.
    entity : str or None
        The registry entity of the row definition.
    unit : str or None
        The unit of the row definition.
    """

    raw: RawRow
    label: Label
    key: RowKey
    kind: RowKind
    parent: RowKey | None
    entity: str | None = None
    unit: str | None = None


@dataclass(frozen=True, slots=True)
class RowMatch:
    """The rows of a table that matched a definition, and the findings of the match.

    Attributes
    ----------
    rows : tuple[KeyedRow, ...]
        The matched rows, in print order. Two rows of one key both stay, with a finding.
    findings : tuple[Finding, ...]
        The findings, as `match_rows` gives them.
    """

    rows: tuple[KeyedRow, ...]
    findings: tuple[Finding, ...]


def join_rows(upper: RawRow, lower: RawRow) -> RawRow:
    """Join a row whose label wraps onto the next line with that line.

    Parameters
    ----------
    upper, lower : RawRow
        The two rows, top first, cut against one binding.

    Returns
    -------
    RawRow
        One row on the page of `upper`, with the prefix, label, cell and stray words of
        `upper` and then of `lower`. It is bold when every label word of both is, and its
        `x0` is the smaller of the two.
    """
    label = (*upper.label_words, *lower.label_words)
    styles = [word.bold for word in label]
    return RawRow(
        page=upper.page,
        prefix=(*upper.prefix, *lower.prefix),
        label_words=label,
        cells=tuple(
            (name, (*above, *below))
            for (name, above), (_, below) in zip(upper.cells, lower.cells, strict=True)
        ),
        stray=(*upper.stray, *lower.stray),
        bold=None if not styles or None in styles else all(styles),
        x0=min(upper.x0, lower.x0),
    )


def starts_known_row(schema: RowSchema) -> Callable[[Line], bool]:
    """Return a test for the first body line of a page: one that opens with a known label.

    Parameters
    ----------
    schema : RowSchema
        The table's rows.

    Returns
    -------
    Callable[[Line], bool]
        True for a line whose normalized text is a label of the schema, normalized, or starts
        with one and a space. So "Parks 12" opens with "Parks", and "Parkside 12" does not. The
        empty label of a row that prints none starts no line.
    """
    labels = tuple(
        sorted({normalize_label(text) for row in schema.rows for text in row.labels} - {""})
    )

    def starts(line: Line) -> bool:
        text = normalize_label(line.text)
        return any(text == label or text.startswith(f"{label} ") for label in labels)

    return starts


def match_rows(raws: Sequence[RawRow], schema: RowSchema) -> RowMatch:
    """Give each raw row of a closed table the key of the one row definition it matches.

    Rows are read in print order across pages, with a stack of open blocks. A row whose key a
    definition names as its `parent` or `within` opens a block when it matches. A matched row
    closes the blocks above its home, its `within` or else its `parent`, and closes them all
    when its home is not open. A row that matches nothing leaves the blocks as they are.

    A definition is a candidate when its `within` is open and its `follows` is the key of the
    row just before, and one of its labels matches. A label matches in three stages, and the
    first stage with a candidate decides, so an exact match always beats a prefix: by
    normalized form, then by squashed form, then, under ``Truncation.UNIQUE_PREFIX`` and for a
    label that is not empty, as the start of a normalized label. A row with no value and no
    candidate joins the next row of its page when the joined label has exactly one candidate,
    as a label that wraps. No row is ever guessed.

    Parameters
    ----------
    raws : Sequence[RawRow]
        The table's raw rows, in print order.
    schema : RowSchema
        The table's rows in this edition.

    Returns
    -------
    RowMatch
        The matched rows. A row's parent is its definition's parent, else the schema's root,
        and the root row itself has none. The findings, whose subject is
        ``"<doc sha8>:<table>:<label or row key>"``, with the sha from the rows' words: BLOCK
        ``unknown_row`` for a row with no candidate and ``ambiguous_row`` for one with two or
        more, both on the row's page and named by its printed label; WARN ``truncated_label``
        for a prefix match, named by the key and quoting the full label; then, after the walk,
        BLOCK ``duplicate_row`` for each key that two or more rows got, on the page of the
        second, and BLOCK ``missing_row`` for each required definition that no row matched,
        on no page.
    """
    subject = f"{_sha8(raws)}:{schema.table}"
    forms = {row.key: tuple(normalize_label(text) for text in row.labels) for row in schema.rows}
    opens = {key for row in schema.rows for key in (row.parent, row.within) if key is not None}
    keyed: list[KeyedRow] = []
    findings: list[Finding] = []
    blocks: list[RowKey] = []
    previous: RowKey | None = None
    index = 0
    while index < len(raws):
        raw = raws[index]
        label = parse_label(raw.prefix, raw.label_words)
        found, truncated = _candidates(label, schema, forms, blocks, previous)
        after = raws[index + 1] if index + 1 < len(raws) else None
        if not found and not raw.has_values() and after is not None and after.page == raw.page:
            joined = join_rows(raw, after)
            joined_label = parse_label(joined.prefix, joined.label_words)
            joined_found = _candidates(joined_label, schema, forms, blocks, previous)
            if len(joined_found[0]) == 1:
                raw, label, (found, truncated) = joined, joined_label, joined_found
                index += 1
        index += 1
        match found:
            case []:
                message = f"no row of the schema prints {label.text!r}"
                findings.append(_block("unknown_row", f"{subject}:{label.printed}", message, raw))
                previous = None
            case [row]:
                keyed.append(_keyed(raw, label, row, schema.root))
                if truncated:
                    findings.append(_truncated(label, row, f"{subject}:{row.key}", raw.page))
                home = row.within if row.within is not None else row.parent
                while blocks and blocks[-1] != home:
                    blocks.pop()
                if row.key in opens:
                    blocks.append(row.key)
                previous = row.key
            case _:
                names = ", ".join(str(row.key) for row in found)
                message = f"{label.text!r} is a label of {names}"
                findings.append(_block("ambiguous_row", f"{subject}:{label.printed}", message, raw))
                previous = None
    for key in dict.fromkeys(row.key for row in keyed):
        repeats = [row for row in keyed if row.key == key]
        if len(repeats) > 1:
            pages = ", ".join(str(row.raw.page) for row in repeats)
            message = f"{len(repeats)} rows get this key, on pages {pages}"
            findings.append(_block("duplicate_row", f"{subject}:{key}", message, repeats[1].raw))
    matched = {row.key for row in keyed}
    for row in schema.rows:
        if row.presence is Presence.REQUIRED and row.key not in matched:
            message = f"no row prints {' or '.join(repr(text) for text in row.labels)}"
            findings.append(Finding(Severity.BLOCK, "missing_row", f"{subject}:{row.key}", message))
    return RowMatch(tuple(keyed), tuple(findings))


def stray_findings(raws: Sequence[RawRow]) -> tuple[Finding, ...]:
    """Report each word that a row prints right of its label area and in no lane.

    Parameters
    ----------
    raws : Sequence[RawRow]
        The table's raw rows.

    Returns
    -------
    tuple[Finding, ...]
        One finding for each stray word, in print order, on the row's page, with the subject
        ``"<doc sha8>:stray:<printed label>"`` and a message that quotes the word. A value word,
        as `has_values` reads one, is BLOCK ``stray_value``, since it is a value outside every
        lane. Any other word is WARN ``stray_word``. The kit's findings take the form of
        ``Finding.subject`` where they know the table, and a raw row does not.
    """
    sha8 = _sha8(raws)
    found: list[Finding] = []
    for raw in raws:
        subject = f"{sha8}:stray:{parse_label(raw.prefix, raw.label_words).printed}"
        for word in raw.stray:
            if _value_words((word,)):
                message = f"{word.text!r} is a value in no lane"
                found.append(_block("stray_value", subject, message, raw))
            else:
                message = f"{word.text!r} is in no lane"
                found.append(Finding(Severity.WARN, "stray_word", subject, message, raw.page))
    return tuple(found)


def _candidates(
    label: Label,
    schema: RowSchema,
    forms: dict[RowKey, tuple[str, ...]],
    blocks: Sequence[RowKey],
    previous: RowKey | None,
) -> tuple[tuple[RowDef, ...], bool]:
    """Return the candidates of the first stage that has any, and whether it is the prefix."""
    allowed = [
        row
        for row in schema.rows
        if (row.within is None or row.within in blocks)
        and (row.follows is None or row.follows == previous)
    ]
    stages: list[tuple[Callable[[str], bool], bool]] = [
        (lambda norm: norm == label.norm, False),
        (lambda norm: squash(norm) == label.squash, False),
    ]
    match schema.truncation:
        case Truncation.NONE:
            pass
        case Truncation.UNIQUE_PREFIX:
            if label.norm:
                stages.append((lambda norm: norm.startswith(label.norm), True))
        case _:
            assert_never(schema.truncation)
    for holds, truncated in stages:
        found = tuple(row for row in allowed if any(holds(norm) for norm in forms[row.key]))
        if found:
            return found, truncated
    return (), False


def _keyed(raw: RawRow, label: Label, row: RowDef, root: RowKey | None) -> KeyedRow:
    """Return a matched row under its definition's parent, else the root, which has none."""
    parent = row.parent if row.parent is not None else root
    if row.key == root:
        parent = None
    return KeyedRow(raw, label, row.key, row.kind, parent, row.entity, row.unit)


def _truncated(label: Label, row: RowDef, subject: str, page: int) -> Finding:
    """Return the warning that a printed label is only the start of the label it matched."""
    full = next(text for text in row.labels if normalize_label(text).startswith(label.norm))
    message = f"{label.text!r} is printed for the label {full!r}"
    return Finding(Severity.WARN, "truncated_label", subject, message, page)


def _sha8(raws: Sequence[RawRow]) -> str:
    words = (word for raw in raws for word in _words(raw))
    return next((word.ref.doc_sha256[:8] for word in words), "")


def _words(raw: RawRow) -> tuple[Word, ...]:
    """Return every word of a raw row: its prefix, label, cell and stray words."""
    cells = (word for _, words in raw.cells for word in words)
    return (*raw.prefix, *raw.label_words, *cells, *raw.stray)


def _block(code: str, subject: str, message: str, raw: RawRow) -> Finding:
    return Finding(Severity.BLOCK, code, subject, message, raw.page)
