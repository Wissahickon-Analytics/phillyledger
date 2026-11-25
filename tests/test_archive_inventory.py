from collections import Counter
from datetime import date
from pathlib import Path

from datadesk.core.domain import DocumentVersion, EditionKey, Period
from datadesk.core.fetch import INDEX_PATH
from datadesk.core.index import parse_index

REPO = Path(__file__).parents[1]
INVENTORY = REPO / "docs" / "evidence" / "inventory" / "qcmr.tsv"
INDEX = REPO / INDEX_PATH

EDITIONS = {
    "qcmr:2021-09-30:none": EditionKey("qcmr", Period(date(2021, 7, 1), date(2021, 9, 30))),
    "qcmr:2021-12-31:none": EditionKey("qcmr", Period(date(2021, 10, 1), date(2021, 12, 31))),
    "qcmr:2022-03-31:none": EditionKey("qcmr", Period(date(2022, 1, 1), date(2022, 3, 31))),
    "qcmr:2022-06-30:none": EditionKey("qcmr", Period(date(2022, 4, 1), date(2022, 6, 30))),
    "qcmr:2022-09-30:none": EditionKey("qcmr", Period(date(2022, 7, 1), date(2022, 9, 30))),
    "qcmr:2022-12-31:none": EditionKey("qcmr", Period(date(2022, 10, 1), date(2022, 12, 31))),
    "qcmr:2023-03-31:none": EditionKey("qcmr", Period(date(2023, 1, 1), date(2023, 3, 31))),
    "qcmr:2023-06-30:none": EditionKey("qcmr", Period(date(2023, 4, 1), date(2023, 6, 30))),
    "qcmr:2023-09-30:none": EditionKey("qcmr", Period(date(2023, 7, 1), date(2023, 9, 30))),
    "qcmr:2023-12-31:none": EditionKey("qcmr", Period(date(2023, 10, 1), date(2023, 12, 31))),
    "qcmr:2024-03-31:none": EditionKey("qcmr", Period(date(2024, 1, 1), date(2024, 3, 31))),
    "qcmr:2024-06-30:none": EditionKey("qcmr", Period(date(2024, 4, 1), date(2024, 6, 30))),
    "qcmr:2024-09-30:none": EditionKey("qcmr", Period(date(2024, 7, 1), date(2024, 9, 30))),
    "qcmr:2024-12-31:none": EditionKey("qcmr", Period(date(2024, 10, 1), date(2024, 12, 31))),
    "qcmr:2025-03-31:none": EditionKey("qcmr", Period(date(2025, 1, 1), date(2025, 3, 31))),
    "qcmr:2025-06-30:none": EditionKey("qcmr", Period(date(2025, 4, 1), date(2025, 6, 30))),
    "qcmr:2025-09-30:none": EditionKey("qcmr", Period(date(2025, 7, 1), date(2025, 9, 30))),
    "qcmr:2025-12-31:none": EditionKey("qcmr", Period(date(2025, 10, 1), date(2025, 12, 31))),
    "qcmr:2026-03-31:none": EditionKey("qcmr", Period(date(2026, 1, 1), date(2026, 3, 31))),
    "qcmr:2026-06-30:none": EditionKey("qcmr", Period(date(2026, 4, 1), date(2026, 6, 30))),
}


def inventory() -> list[dict[str, str]]:
    header, *lines = INVENTORY.read_text(encoding="utf-8").splitlines()
    names = header.split("\t")
    return [dict(zip(names, line.split("\t"), strict=True)) for line in lines]


def indexed() -> tuple[DocumentVersion, ...]:
    return parse_index(INDEX.read_text(encoding="utf-8")).versions


def is_iso_date(text: str) -> bool:
    try:
        return date.fromisoformat(text).isoformat() == text
    except ValueError:
        return False


def test_each_expected_edition_has_a_row_and_an_indexed_version() -> None:
    assert sorted(row["edition"] for row in inventory()) == sorted(EDITIONS)
    editions = {version.edition for version in indexed()}
    assert [name for name, edition in EDITIONS.items() if edition not in editions] == []


def test_each_inventory_pair_is_indexed_once() -> None:
    pairs = [(EDITIONS[row["edition"]], row["sha256"]) for row in inventory()]
    lines = Counter((version.edition, version.sha256) for version in indexed())
    assert len(pairs) == len(EDITIONS)
    assert {pair: lines[pair] for pair in pairs} == dict.fromkeys(pairs, 1)


def test_each_edition_is_indexed_under_its_inventory_sha() -> None:
    rows = inventory()
    filed = {version.sha256: version.edition for version in indexed()}
    assert len(rows) == len(EDITIONS)
    assert [(row["sha256"], filed.get(row["sha256"])) for row in rows] == [
        (row["sha256"], EDITIONS[row["edition"]]) for row in rows
    ]


def test_every_inventory_row_is_checked() -> None:
    rows = inventory()
    assert len(rows) == len(EDITIONS)
    assert [row["edition"] for row in rows if not is_iso_date(row["checked"])] == []
