from datetime import date
from importlib.resources import files

from datadesk.core.catalog import ListingShape, SourceCatalog, SourceEntry, load_catalog

CATALOG = files("datadesk") / "data" / "catalog.toml"


def test_the_catalog_loads_with_its_qcmr_entry() -> None:
    catalog = load_catalog(CATALOG.read_text(encoding="utf-8"))
    assert isinstance(catalog, SourceCatalog), catalog
    assert catalog.entries == (
        SourceEntry(
            id="qcmr",
            series="qcmr",
            shape=ListingShape.DOCUMENT_FINDER,
            listing_url="https://api.phila.gov/phila/document-finder/v1/151831",
            category="Quarterly City Managers Report",
            first_period_end=date(2021, 9, 30),
        ),
    )
