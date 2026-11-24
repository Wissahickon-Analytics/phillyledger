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
    DOCUMENT_FINDER = "document_finder"
    PHILA_DOCUMENTS = "phila_documents"
    MANUAL = "manual"


@dataclass(frozen=True, slots=True)
class SourceEntry:
    id: str
    series: str
    shape: ListingShape
    listing_url: str
    category: str
    first_period_end: date


@dataclass(frozen=True, slots=True)
class SourceCatalog:
    entries: tuple[SourceEntry, ...]

    def __post_init__(self) -> None:
        if repeated := _repeated_ids(self.entries):
            raise ValueError(f"the catalog lists {', '.join(repeated)} more than once")

    def entry(self, id: str) -> SourceEntry:
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
    findings += [
        _block("catalog_duplicate_id", id, f"{id} names more than one source")
        for id in _repeated_ids(entries)
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
    if findings:
        return findings
    if fields["shape"] not in ListingShape:
        return [_block("catalog_unknown_shape", subject, f"{fields['shape']} is not a shape")]
    return SourceEntry(
        id=fields["id"],
        series=fields["series"],
        shape=ListingShape(fields["shape"]),
        listing_url=fields["listing_url"],
        category=fields["category"],
        first_period_end=fields["first_period_end"],
    )


def _repeated_ids(entries: Iterable[SourceEntry]) -> list[str]:
    return [id for id, count in Counter(entry.id for entry in entries).items() if count > 1]


def _block(code: str, subject: str, message: str) -> Finding:
    return Finding(Severity.BLOCK, code, subject, message)
