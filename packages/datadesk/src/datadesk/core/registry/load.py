"""Read the registry's TOML files, with the record readers that the row schemas share.

The shell reads each file's text and passes it in, so nothing here opens a file. A file holds
arrays of tables: one array for each `EntityKind`, named by its value, such as
``[[department]]``, then ``[[alias]]`` and ``[[relation]]``. A name, code or parent is an inline
table, as ``{ value = "Fleet Services", first_fy = 2022 }``.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from tomllib import TOMLDecodeError, loads
from typing import Any

from checkedtables.refs import Sha256
from checkedtables.table import Finding, Severity
from datadesk.core.registry.model import (
    Alias,
    Dated,
    Entity,
    EntityKind,
    Registry,
    Relation,
    RelationKind,
    Residual,
)


@dataclass(frozen=True, slots=True)
class Refused:
    """TOML text that a loader refuses, with each problem in it as a BLOCK finding.

    Raises
    ------
    ValueError
        When there is no finding.
    """

    findings: tuple[Finding, ...]

    def __post_init__(self) -> None:
        """Refuse a refusal with no finding."""
        if not self.findings:
            raise ValueError("a refusal needs a finding")


class RecordError(ValueError):
    """A TOML record whose shape breaks its loader's rule, with the code of its finding.

    A loader catches it, and every `ValueError` that a value's builder raises, at the record,
    and returns the finding that `refusal` makes, so none leaves the loader.

    Parameters
    ----------
    code : str
        The finding code without the loader's prefix, such as "missing_field".
    message : str
        The problem in words.
    """

    def __init__(self, code: str, message: str) -> None:
        """Keep the code beside the message."""
        super().__init__(message)
        self.code = code


def load_registry(texts: Sequence[tuple[str, str]]) -> Registry | Refused:
    """Read the registry from the text of each of its files.

    Parameters
    ----------
    texts : Sequence[tuple[str, str]]
        Each file's path, which the findings name, and its text, in the order to read them.

    Returns
    -------
    Registry or Refused
        The entities, relations and aliases in file order. Or every problem as a BLOCK finding:
        registry_not_toml and registry_unknown_field for a file, with the path as subject; for
        a record, with the subject ``"<path>:<array> <n>"`` and the first problem of the record,
        registry_unknown_field, registry_missing_field, registry_wrong_type (an integer is not
        a bool) or registry_bad_value, such as a sha that is not one, an alias with no table
        or a kind that is not a member; and registry_duplicate_id, with the id as subject.
    """
    entities: list[Entity] = []
    aliases: list[Alias] = []
    relations: list[Relation] = []
    findings: list[Finding] = []
    for path, text in texts:
        try:
            arrays = loads(text)
        except TOMLDecodeError as error:
            findings.append(_block("registry_not_toml", path, str(error)))
            continue
        for name, records in arrays.items():
            if name not in (*EntityKind, "alias", "relation"):
                findings.append(_block("registry_unknown_field", path, f"unknown array {name}"))
                continue
            if not isinstance(records, list):
                findings.append(_block("registry_wrong_type", f"{path}:{name}", "not an array"))
                continue
            for number, record in enumerate(records, 1):
                try:
                    match name:
                        case "alias":
                            aliases.append(_alias(record))
                        case "relation":
                            relations.append(_relation(record))
                        case _:
                            entities.append(_entity(EntityKind(name), record))
                except ValueError as error:
                    findings.append(refusal("registry", f"{path}:{name} {number}", error))
    counts = Counter(entity.id for entity in entities)
    findings += [
        _block("registry_duplicate_id", id, f"{count} entities have the id {id}")
        for id, count in counts.items()
        if count > 1
    ]
    if findings:
        return Refused(tuple(findings))
    return Registry(tuple(entities), tuple(relations), tuple(aliases))


def fields_of(record: object, allowed: Sequence[str]) -> dict[str, Any]:
    """Return the fields of a TOML record.

    Raises
    ------
    RecordError
        wrong_type when the record is not a table, and unknown_field when it has a field that
        is not in `allowed`.
    """
    if not isinstance(record, dict):
        raise RecordError("wrong_type", "a record is not a table")
    if unknown := [name for name in record if name not in allowed]:
        raise RecordError("unknown_field", f"unknown field {unknown[0]}")
    return record


def optional[T](fields: dict[str, Any], name: str, kind: type[T]) -> T | None:
    """Return a field of exactly the type `kind`, or None when the record lacks it.

    Raises
    ------
    RecordError
        wrong_type when the value is of another type. A bool is not an int.
    """
    if name not in fields:
        return None
    value = fields[name]
    if type(value) is not kind:
        raise RecordError("wrong_type", f"{name} is not a {kind.__name__}")
    return value


def required[T](fields: dict[str, Any], name: str, kind: type[T]) -> T:
    """Return a field of exactly the type `kind`.

    Raises
    ------
    RecordError
        missing_field when the record lacks it, and wrong_type as `optional` raises it.
    """
    value = optional(fields, name, kind)
    if value is None:
        raise RecordError("missing_field", f"no {name}")
    return value


def items_of(fields: dict[str, Any], name: str) -> list[Any]:
    """Return a field that holds an array, or an empty one when the record lacks it.

    Raises
    ------
    RecordError
        wrong_type when the value is not an array.
    """
    value = fields.get(name, [])
    if not isinstance(value, list):
        raise RecordError("wrong_type", f"{name} is not an array")
    return value


def texts_of(fields: dict[str, Any], name: str) -> tuple[str, ...]:
    """Return a field that holds an array of strings, or none when the record lacks it.

    Raises
    ------
    RecordError
        wrong_type when the value is not an array or an item is not a string.
    """
    value = items_of(fields, name)
    if not all(type(item) is str for item in value):
        raise RecordError("wrong_type", f"{name} holds an item that is not a string")
    return tuple(value)


def shas_of(fields: dict[str, Any], name: str) -> tuple[Sha256, ...]:
    """Return a field that holds an array of file shas, or none when the record lacks it.

    Raises
    ------
    ValueError
        From `Sha256`, for an item that is not 64 lowercase hex characters, and as `texts_of`
        raises it.
    """
    return tuple(Sha256(text) for text in texts_of(fields, name))


def member_of[E: StrEnum](kind: type[E], fields: dict[str, Any], name: str, default: E) -> E:
    """Return the member of `kind` that a field names, or `default` when the record lacks it.

    Raises
    ------
    ValueError
        From `kind`, for a value that names no member, and as `optional` raises it.
    """
    value = optional(fields, name, str)
    return default if value is None else kind(value)


def refusal(prefix: str, subject: str, error: ValueError) -> Finding:
    """Return the BLOCK finding for a record that a loader refuses.

    Parameters
    ----------
    prefix : str
        The loader's prefix of finding codes, such as "registry".
    subject : str
        The record, as ``"<path>:<array> <n>"``.
    error : ValueError
        A `RecordError`, whose code the finding takes, or the error of a value's builder,
        which gives bad_value.
    """
    match error:
        case RecordError(code=code):
            pass
        case _:
            code = "bad_value"
    return _block(f"{prefix}_{code}", subject, str(error))


def _entity(kind: EntityKind, record: object) -> Entity:
    fields = fields_of(record, ("id", "names", "codes", "parents", "members", "residual"))
    return Entity(
        id=required(fields, "id", str),
        kind=kind,
        names=_dated(fields, "names"),
        codes=_dated(fields, "codes"),
        parents=_dated(fields, "parents"),
        members=texts_of(fields, "members"),
        residual=member_of(Residual, fields, "residual", Residual.NO),
    )


def _dated(fields: dict[str, Any], name: str) -> tuple[Dated, ...]:
    dated = [fields_of(item, ("value", "first_fy", "last_fy")) for item in items_of(fields, name)]
    return tuple(
        Dated(
            required(item, "value", str),
            optional(item, "first_fy", int),
            optional(item, "last_fy", int),
        )
        for item in dated
    )


def _alias(record: object) -> Alias:
    fields = fields_of(record, ("entity", "label", "tables", "first_fy", "last_fy", "editions"))
    return Alias(
        entity=required(fields, "entity", str),
        label=required(fields, "label", str),
        tables=texts_of(fields, "tables"),
        first_fy=optional(fields, "first_fy", int),
        last_fy=optional(fields, "last_fy", int),
        editions=shas_of(fields, "editions"),
    )


def _relation(record: object) -> Relation:
    names = ("kind", "source", "target", "first_fy", "last_fy", "fund", "evidence")
    fields = fields_of(record, names)
    return Relation(
        kind=RelationKind(required(fields, "kind", str)),
        source=required(fields, "source", str),
        target=required(fields, "target", str),
        first_fy=required(fields, "first_fy", int),
        last_fy=optional(fields, "last_fy", int),
        fund=optional(fields, "fund", str),
        evidence=required(fields, "evidence", str),
    )


def _block(code: str, subject: str, message: str) -> Finding:
    return Finding(Severity.BLOCK, code, subject, message)
