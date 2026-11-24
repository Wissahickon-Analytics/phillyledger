from datetime import date

import pytest

from checkedtables.table import Finding, Severity
from datadesk.core.catalog import ListingShape, SourceCatalog, SourceEntry, load_catalog

QCMR = SourceEntry(
    id="qcmr",
    series="qcmr",
    shape=ListingShape.DOCUMENT_FINDER,
    listing_url="https://api.phila.gov/phila/document-finder/v1/151831",
    category="Quarterly City Managers Report",
    first_period_end=date(2021, 9, 30),
)
QCMR_TEXT = """
[[source]]
id = "qcmr"
series = "qcmr"
shape = "document_finder"
listing_url = "https://api.phila.gov/phila/document-finder/v1/151831"
category = "Quarterly City Managers Report"
first_period_end = 2021-09-30
"""


def codes(loaded: SourceCatalog | tuple[Finding, ...]) -> list[tuple[str, str]]:
    assert isinstance(loaded, tuple), loaded
    assert {finding.severity for finding in loaded} == {Severity.BLOCK}
    return [(finding.code, finding.subject) for finding in loaded]


def test_load_catalog_reads_each_source_entry() -> None:
    loaded = load_catalog(QCMR_TEXT)
    assert loaded == SourceCatalog((QCMR,))
    assert isinstance(loaded, SourceCatalog)
    assert loaded.entry("qcmr") == QCMR


def test_the_empty_text_is_the_empty_catalog() -> None:
    assert load_catalog("") == SourceCatalog(())


def test_entry_refuses_an_id_the_catalog_lacks() -> None:
    with pytest.raises(KeyError, match="collections_city"):
        SourceCatalog((QCMR,)).entry("collections_city")


def test_catalog_refuses_one_id_twice() -> None:
    with pytest.raises(ValueError, match="qcmr"):
        SourceCatalog((QCMR, QCMR))


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("[[source]\n", [("catalog_not_toml", "catalog")], id="not_toml"),
        pytest.param(
            QCMR_TEXT.replace('category = "Quarterly City Managers Report"\n', ""),
            [("catalog_missing_field", "qcmr")],
            id="missing_field",
        ),
        pytest.param(
            QCMR_TEXT + 'lag_days = "45"\n',
            [("catalog_unknown_field", "qcmr")],
            id="unknown_field",
        ),
        pytest.param(
            f'title = "Sources"\n{QCMR_TEXT}',
            [("catalog_unknown_field", "catalog")],
            id="unknown_top_level_key",
        ),
        pytest.param(
            QCMR_TEXT.replace("2021-09-30", '"2021-09-30"'),
            [("catalog_wrong_type", "qcmr")],
            id="a_date_written_as_a_string",
        ),
        pytest.param(
            QCMR_TEXT.replace("2021-09-30", "2021-09-30T00:00:00"),
            [("catalog_wrong_type", "qcmr")],
            id="a_date_and_time",
        ),
        pytest.param(
            QCMR_TEXT.replace('id = "qcmr"', "id = 7"),
            [("catalog_wrong_type", "source 1")],
            id="an_id_that_is_not_a_string",
        ),
        pytest.param(
            QCMR_TEXT.replace('"document_finder"', '"rss"'),
            [("catalog_unknown_shape", "qcmr")],
            id="unknown_shape",
        ),
        pytest.param(
            QCMR_TEXT + QCMR_TEXT,
            [("catalog_duplicate_id", "qcmr")],
            id="duplicate_id",
        ),
        pytest.param(
            'source = "qcmr"\n',
            [("catalog_wrong_type", "source")],
            id="source_is_not_an_array_of_tables",
        ),
    ],
)
def test_load_catalog_returns_a_finding_for_each_problem(
    text: str, expected: list[tuple[str, str]]
) -> None:
    assert codes(load_catalog(text)) == expected


def test_load_catalog_returns_every_problem_it_finds() -> None:
    text = QCMR_TEXT.replace('series = "qcmr"\n', "") + QCMR_TEXT.replace(
        'id = "qcmr"', 'id = "qcmr_again"'
    ).replace('"document_finder"', '"rss"')
    assert codes(load_catalog(text)) == [
        ("catalog_missing_field", "qcmr"),
        ("catalog_unknown_shape", "qcmr_again"),
    ]


def test_an_entry_s_field_shape_and_repeated_id_are_each_a_finding() -> None:
    text = QCMR_TEXT + QCMR_TEXT.replace("document_finder", "rss") + "extra=1\n"
    assert codes(load_catalog(text)) == [
        ("catalog_unknown_field", "qcmr"),
        ("catalog_unknown_shape", "qcmr"),
        ("catalog_duplicate_id", "qcmr"),
    ]
