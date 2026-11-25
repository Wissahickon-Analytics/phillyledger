"""Read and write index.jsonl, the archive index, one JSON line for each version."""

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
    """Read the text of index.jsonl into an index.

    Lines end at each line feed, empty lines are skipped, and the versions are sorted. The parser
    checks that each sha256 is a string of 64 lowercase hex characters, the form that
    `hexdigest()` writes, that `urls` is a JSON list, that the stage, via and holding name members
    of their enums, that each period holds two ISO dates and does not end before it starts, and
    that the versions pass `index_problem`. It does not check the series, `listed_at`, `title`
    or the items of `urls`.

    Raises
    ------
    ValueError
        For a line that is not JSON, and for each check above that fails.
    KeyError, TypeError
        For a line, an edition or a period that lacks a key or is not a JSON object, for a
        period date that is not a string, and for unchecked values that the sort cannot compare,
        such as a series that is a number.
    """
    return ArchiveIndex(sort_versions(_version(loads(line)) for line in jsonl.split("\n") if line))


def render_index(index: ArchiveIndex) -> str:
    """Write an index as the text of index.jsonl, one JSON object for each version.

    Keys are sorted at every level, dates are in ISO form, and every line ends in a newline, so
    the empty index is "".
    """
    return "".join(
        f"{dumps(asdict(version), ensure_ascii=False, sort_keys=True, default=date.isoformat)}\n"
        for version in index.versions
    )


def add_versions(index: ArchiveIndex, new: Sequence[DocumentVersion]) -> ArchiveIndex | Finding:
    """Add versions to an index, or return the BLOCK finding of a rule the result breaks.

    A version whose sha and edition are already indexed adds each URL that its line lacks, after
    the URLs the line holds, and the line takes the later of the two listed_at stamps. One with no
    URL the line lacks leaves the line as it was. The result must pass `index_problem`, so a sha
    indexed under another edition is a content_alias finding.
    """
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
    if not (isinstance(sha256, str) and SHA256.fullmatch(sha256)):
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
