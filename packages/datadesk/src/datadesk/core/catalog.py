"""The catalog of sources: each publisher listing that the archive reads."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from tomllib import TOMLDecodeError, loads
from types import MappingProxyType
from typing import Any

from checkedtables.table import Finding, Severity


class ListingShape(StrEnum):
    """The layout of a publisher's listing page, which picks the parser that reads it."""

    DOCUMENT_FINDER = "document_finder"
    PHILA_DOCUMENTS = "phila_documents"
    MANUAL = "manual"


@dataclass(frozen=True, slots=True)
class SourceEntry:
    """One publisher listing that the archive reads, from one `[[source]]` table.

    Attributes
    ----------
    series
        The series of its editions, and the key of its title rule.
    category
        For a document-finder listing, the category whose documents are read.
    first_period_end
        An edition that ends before this date is never fetched.
    """

    id: str
    series: str
    shape: ListingShape
    listing_url: str
    category: str
    first_period_end: date


@dataclass(frozen=True, slots=True)
class SourceCatalog:
    """Every source that catalog.toml lists, each id once."""

    entries: tuple[SourceEntry, ...]

    def __post_init__(self) -> None:
        """Raise ValueError when an id is listed more than once."""
        if repeated := _repeated(entry.id for entry in self.entries):
            raise ValueError(f"the catalog lists {', '.join(repeated)} more than once")

    def entry(self, id: str) -> SourceEntry:
        """Return the source with this id.

        Raises
        ------
        KeyError
            When the catalog has no source with this id.
        """
        for entry in self.entries:
            if entry.id == id:
                return entry
        raise KeyError(id)


FIELDS: MappingProxyType[str, type] = MappingProxyType(
    {
        "id": str,
        "series": str,
        "shape": str,
        "listing_url": str,
        "category": str,
        "first_period_end": date,
    }
)


def load_catalog(text: str) -> SourceCatalog | tuple[Finding, ...]:
    """Read the text of catalog.toml, or return every problem in it as a BLOCK finding.

    The file holds one `[[source]]` table for each listing, with the six fields of `SourceEntry`.
    The codes are catalog_not_toml, catalog_unknown_field for a key other than `source` or a field
    that `SourceEntry` lacks, catalog_missing_field, catalog_wrong_type (a date and time is not a
    date), catalog_unknown_shape and catalog_duplicate_id.
    """
    try:
        tables = loads(text)
    except TOMLDecodeError as error:
        return (_block("catalog_not_toml", "catalog", str(error)),)
    findings = [
        _block("catalog_unknown_field", "catalog", f"unknown key {key}")
        for key in tables
        if key != "source"
    ]
    sources = tables.get("source", [])
    if not isinstance(sources, list) or not all(isinstance(fields, dict) for fields in sources):
        return (*findings, _block("catalog_wrong_type", "source", "not an array of tables"))
    entries: list[SourceEntry] = []
    for number, fields in enumerate(sources, 1):
        read = _entry(number, fields)
        if isinstance(read, SourceEntry):
            entries.append(read)
        else:
            findings.extend(read)
    ids = (fields["id"] for fields in sources if type(fields.get("id")) is str)
    findings += [
        _block("catalog_duplicate_id", id, f"{id} names more than one source")
        for id in _repeated(ids)
    ]
    return tuple(findings) or SourceCatalog(tuple(entries))


def _entry(number: int, fields: dict[str, Any]) -> SourceEntry | list[Finding]:
    subject = fields["id"] if type(fields.get("id")) is str else f"source {number}"
    findings = [
        *(
            _block("catalog_missing_field", subject, f"no {name}")
            for name in FIELDS
            if name not in fields
        ),
        *(
            _block("catalog_unknown_field", subject, f"unknown field {name}")
            for name in fields
            if name not in FIELDS
        ),
        *(
            _block("catalog_wrong_type", subject, f"{name} is not a {kind.__name__}")
            for name, kind in FIELDS.items()
            if name in fields and type(fields[name]) is not kind
        ),
    ]
    shape = fields.get("shape")
    if type(shape) is str and shape not in ListingShape:
        findings.append(_block("catalog_unknown_shape", subject, f"{shape} is not a shape"))
    if findings:
        return findings
    return SourceEntry(
        id=fields["id"],
        series=fields["series"],
        shape=ListingShape(fields["shape"]),
        listing_url=fields["listing_url"],
        category=fields["category"],
        first_period_end=fields["first_period_end"],
    )


def _repeated(ids: Iterable[str]) -> list[str]:
    return [id for id, count in Counter(ids).items() if count > 1]


def _block(code: str, subject: str, message: str) -> Finding:
    return Finding(Severity.BLOCK, code, subject, message)
