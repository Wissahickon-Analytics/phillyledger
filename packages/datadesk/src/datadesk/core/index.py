from collections.abc import Sequence
from dataclasses import asdict, replace
from datetime import date
from json import dumps, loads
from re import compile
from typing import Any

from checkedtables.table import Finding
from datadesk.core.domain import (
    ArchiveIndex,
    DocumentVersion,
    EditionKey,
    Holding,
    Period,
    Stage,
    Via,
    index_problem,
    sort_versions,
)

SHA256 = compile(r"[0-9a-f]{64}")


def parse_index(jsonl: str) -> ArchiveIndex:
    return ArchiveIndex(sort_versions(_version(loads(line)) for line in jsonl.split("\n") if line))


def render_index(index: ArchiveIndex) -> str:
    return "".join(
        f"{dumps(asdict(version), ensure_ascii=False, sort_keys=True, default=date.isoformat)}\n"
        for version in index.versions
    )


def add_versions(index: ArchiveIndex, new: Sequence[DocumentVersion]) -> ArchiveIndex | Finding:
    lines = {(version.sha256, version.edition): version for version in index.versions}
    for version in new:
        key = (version.sha256, version.edition)
        held = lines.get(key)
        if held is None:
            lines[key] = replace(version, urls=tuple(dict.fromkeys(version.urls)))
        elif any(url not in held.urls for url in version.urls):
            urls = tuple(dict.fromkeys(held.urls + version.urls))
            lines[key] = replace(held, urls=urls, listed_at=max(held.listed_at, version.listed_at))
    versions = sort_versions(lines.values())
    return index_problem(versions) or ArchiveIndex(versions)


def _version(line: dict[str, Any]) -> DocumentVersion:
    edition = line["edition"]
    printed = line["printed_period"]
    sha256 = line["sha256"]
    urls = line["urls"]
    if not SHA256.fullmatch(sha256):
        raise ValueError(f"sha256 {sha256!r} is not 64 lowercase hex characters")
    if not isinstance(urls, list):
        raise ValueError(f"urls {urls!r} is not a list")
    return DocumentVersion(
        sha256=sha256,
        edition=EditionKey(edition["series"], _period(edition["period"]), Stage(edition["stage"])),
        listed_at=line["listed_at"],
        urls=tuple(urls),
        title=line["title"],
        printed_period=None if printed is None else _period(printed),
        supersedes=line["supersedes"],
        via=Via(line["via"]),
        holding=Holding(line["holding"]),
    )


def _period(fields: dict[str, str]) -> Period:
    return Period(date.fromisoformat(fields["start"]), date.fromisoformat(fields["end"]))
