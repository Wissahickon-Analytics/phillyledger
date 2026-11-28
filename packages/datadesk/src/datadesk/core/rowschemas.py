"""A closed table's row schema, read from TOML and narrowed to the rows of one edition.

A row that names a registry entity carries no labels, so each department spelling has one home,
the registry (design section 7.2, change 11). `schema_for` fills such a row's labels from
`labels_for` and the row's `forms`. The shell reads ``datadesk/data/rows/<table>.toml`` and
passes its text in, so nothing here opens a file.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import date
from re import compile
from tomllib import TOMLDecodeError, loads
from typing import Any, assert_never

from checkedtables.kinds import Presence
from checkedtables.refs import Sha256
from checkedtables.rows import RowDef, RowSchema, Truncation
from checkedtables.table import Finding, RowKey, RowKind, Severity
from datadesk.core.domain import DocumentVersion, Period
from datadesk.core.periods import fiscal_year_of
from datadesk.core.registry.load import (
    RecordError,
    Refused,
    fields_of,
    items_of,
    member_of,
    optional,
    refusal,
    required,
    shas_of,
    texts_of,
)
from datadesk.core.registry.model import LookupScope, Registry
from datadesk.core.registry.resolve import labels_for

_NAME = "{name}"
_FORM = compile(r"[^{}]*\{name\}[^{}]*")
_ROW_FIELDS = (
    "key",
    "kind",
    "entity",
    "forms",
    "labels",
    "parent",
    "within",
    "follows",
    "presence",
    "unit",
    "periods",
    "absent_editions",
)


@dataclass(frozen=True, slots=True)
class RegistryLabels:
    """The labels of a row that names an entity, which only the registry spells.

    Attributes
    ----------
    entity : str
        The entity's id.
    forms : tuple[str, ...]
        Templates of the printed label, each with ``{name}`` once and no other field, such as
        "{name} - Total" for the parent of Civilian and Uniform rows (QPOS-Q37). A row with no
        `forms` in its file has ``("{name}",)``, the name alone.
    """

    entity: str
    forms: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SchemaLabels:
    """The labels of a row that belongs to one table, such as Civilian or TOTAL ALL FUNDS.

    Attributes
    ----------
    labels : tuple[str, ...]
        The labels as the table prints them. ``("",)`` is a row that prints no label.
    """

    labels: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RowSource:
    """One ``[[row]]`` of a row schema file, before it is narrowed to an edition.

    The other fields are those of `RowDef`.

    Attributes
    ----------
    labels : RegistryLabels or SchemaLabels
        Where the row's labels come from: the registry or the schema, never both.
    periods : tuple[Period, ...]
        The spans whose editions print the row. An edition is in a span when the span holds
        the edition's period end. Empty for a row that every edition prints. An open end is
        `date.min` or `date.max`.
    absent_editions : tuple[Sha256, ...]
        The files that do not print the row although a period holds them (MSCH-Q23).
    """

    key: RowKey
    kind: RowKind
    labels: RegistryLabels | SchemaLabels
    parent: RowKey | None = None
    within: RowKey | None = None
    follows: RowKey | None = None
    presence: Presence = Presence.REQUIRED
    unit: str | None = None
    periods: tuple[Period, ...] = ()
    absent_editions: tuple[Sha256, ...] = ()


@dataclass(frozen=True, slots=True)
class RowSchemaSource:
    """A table's row schema file: every row of every edition, with the fields of `RowSchema`."""

    table: str
    rows: tuple[RowSource, ...]
    root: RowKey | None = None
    drop: tuple[str, ...] = ()
    truncation: Truncation = Truncation.NONE


def load_row_schema(table: str, toml_text: str) -> RowSchemaSource | Refused:
    """Read a table's row schema file.

    The file holds ``table``, which must be `table`, then ``root``, ``drop`` and
    ``truncation`` as `RowSchema` has them, and one ``[[row]]`` for each row. A row holds
    ``key`` and ``kind``, then either ``entity`` with optional ``forms`` or ``labels``. It may
    hold ``parent``, ``within`` and ``follows`` as row keys, ``presence``, ``unit``,
    ``periods`` as an array of ``[start, end]`` ISO dates with ``""`` for an open end, and
    ``absent_editions`` as file shas.

    Parameters
    ----------
    table : str
        The table whose file this is, which the findings name.
    toml_text : str
        The file's text.

    Returns
    -------
    RowSchemaSource or Refused
        The rows in file order. Or every problem as a BLOCK finding: for the file, with
        `table` as subject, rowschema_not_toml, rowschema_wrong_table, or the first problem of
        its top-level keys; for a row, with the subject ``"<table>:row <n>"`` and the row's
        first problem, rowschema_entity_with_labels for a row that names an entity and has
        labels (change 11), rowschema_unknown_field, rowschema_missing_field,
        rowschema_wrong_type or rowschema_bad_value, such as a key that is not one, a form
        without ``{name}``, a date that is not one, a sha that is not one, or `follows` on a
        row that prints a label; and rowschema_duplicate_key, with ``"<table>:<key>"``.
    """
    try:
        top = fields_of(loads(toml_text), ("table", "root", "drop", "truncation", "row"))
        named = required(top, "table", str)
        if named != table:
            raise RecordError("wrong_table", f"the file is the row schema of {named}")
        root = _key(top, "root")
        drop = texts_of(top, "drop")
        truncation = member_of(Truncation, top, "truncation", Truncation.NONE)
        records = items_of(top, "row")
    except TOMLDecodeError as error:
        return Refused((Finding(Severity.BLOCK, "rowschema_not_toml", table, str(error)),))
    except ValueError as error:
        return Refused((refusal("rowschema", table, error),))
    rows: list[RowSource] = []
    findings: list[Finding] = []
    for number, record in enumerate(records, 1):
        try:
            rows.append(_row(record))
        except ValueError as error:
            findings.append(refusal("rowschema", f"{table}:row {number}", error))
    findings += [
        Finding(Severity.BLOCK, "rowschema_duplicate_key", f"{table}:{key}", f"{count} rows")
        for key, count in Counter(row.key for row in rows).items()
        if count > 1
    ]
    if findings:
        return Refused(tuple(findings))
    return RowSchemaSource(table, tuple(rows), root, drop, truncation)


def schema_for(source: RowSchemaSource, version: DocumentVersion, reg: Registry) -> RowSchema:
    """Narrow a row schema to the rows and labels of one edition.

    Parameters
    ----------
    source : RowSchemaSource
        The table's row schema file.
    version : DocumentVersion
        The edition's file. Its period end chooses the rows and the fiscal year of the
        labels, and its sha is the file that an alias or `absent_editions` names.
    reg : Registry
        The registry, which spells every row that names an entity.

    Returns
    -------
    RowSchema
        The rows that have no periods or a period that holds the period end, and whose
        `absent_editions` do not name the sha, in file order. A row that names an entity takes
        each spelling of `labels_for` in the table, year and file, put through each of its
        forms, each label once. An entity with no spelling there gives a row with no label,
        which `match_rows` reports as missing_row when the row is required.
    """
    day = version.edition.period.end
    scope = LookupScope(source.table, fiscal_year_of(day), version.sha256)
    rows = tuple(
        _row_def(row, reg, scope)
        for row in source.rows
        if (not row.periods or any(period.holds(day) for period in row.periods))
        and version.sha256 not in row.absent_editions
    )
    return RowSchema(source.table, rows, source.root, source.drop, source.truncation)


def _row(record: object) -> RowSource:
    fields = fields_of(record, _ROW_FIELDS)
    labels = _labels(fields)
    follows = _key(fields, "follows")
    if follows is not None and labels != SchemaLabels(("",)):
        raise RecordError("bad_value", "only a row that prints no label may use follows")
    return RowSource(
        key=RowKey.parse(required(fields, "key", str)),
        kind=RowKind(required(fields, "kind", str)),
        labels=labels,
        parent=_key(fields, "parent"),
        within=_key(fields, "within"),
        follows=follows,
        presence=member_of(Presence, fields, "presence", Presence.REQUIRED),
        unit=optional(fields, "unit", str),
        periods=tuple(_period(item) for item in items_of(fields, "periods")),
        absent_editions=shas_of(fields, "absent_editions"),
    )


def _labels(fields: dict[str, Any]) -> RegistryLabels | SchemaLabels:
    """Return the home of a row's labels, refusing a row that has two homes or none."""
    entity = optional(fields, "entity", str)
    if entity is None:
        if "forms" in fields:
            raise RecordError("bad_value", "forms belong to a row that names an entity")
        if "labels" not in fields:
            raise RecordError("missing_field", "no entity and no labels")
        return SchemaLabels(texts_of(fields, "labels"))
    if "labels" in fields:
        message = f"the row names {entity}, whose labels come from the registry alone"
        raise RecordError("entity_with_labels", message)
    forms = texts_of(fields, "forms") or (_NAME,)
    if bad := [form for form in forms if not _FORM.fullmatch(form)]:
        raise RecordError("bad_value", f"the form {bad[0]!r} needs {_NAME} once and no other field")
    return RegistryLabels(entity, forms)


def _key(fields: dict[str, Any], name: str) -> RowKey | None:
    text = optional(fields, name, str)
    return None if text is None else RowKey.parse(text)


def _period(item: object) -> Period:
    """Read ``[start, end]``, with ``""`` for an open end, as a `Period` to `date.min` or `max`."""
    if not isinstance(item, list) or len(item) != 2 or not all(type(end) is str for end in item):
        raise RecordError("wrong_type", "a period is not an array of two date strings")
    start, end = item
    return Period(
        date.fromisoformat(start) if start else date.min,
        date.fromisoformat(end) if end else date.max,
    )


def _row_def(row: RowSource, reg: Registry, scope: LookupScope) -> RowDef:
    match row.labels:
        case RegistryLabels(entity=entity, forms=forms):
            names = labels_for(reg, entity, scope)
            labels = tuple(dict.fromkeys(form.replace(_NAME, n) for n in names for form in forms))
        case SchemaLabels(labels=labels):
            entity = None
        case _:
            assert_never(row.labels)
    return RowDef(
        key=row.key,
        kind=row.kind,
        labels=labels,
        parent=row.parent,
        within=row.within,
        follows=row.follows,
        presence=row.presence,
        entity=entity,
        unit=row.unit,
    )
