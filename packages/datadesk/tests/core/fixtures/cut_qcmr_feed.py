import sys
from hashlib import sha256
from json import loads
from pathlib import Path
from pprint import pformat

QCMR = "Quarterly City Managers Report"
OTHER = "Overtime Spending Action Plan"
LAST_REPORT_BEFORE_THE_FLOOR = "Quarterly City Managers Report - June 30, 2021"
COMMAND = (
    "uv run python -I packages/datadesk/tests/core/fixtures/cut_qcmr_feed.py <recording>\n"
    "#   | uv run ruff format --stdin-filename qcmr_feed.py -\n"
    "#   > packages/datadesk/tests/core/fixtures/qcmr_feed.py"
)


def cut(recording: Path) -> str:
    data = recording.read_bytes()
    assert sha256(data).hexdigest() == recording.stem, "the recording's name is not its sha256"
    categories = loads(data)
    qcmr = next(category for category in categories if category["title"] == QCMR)
    other = next(category for category in categories if category["title"] == OTHER)
    titles = [document["title"] for document in qcmr["documents"]]
    assert titles.count(LAST_REPORT_BEFORE_THE_FLOOR) == 1
    kept = titles.index(LAST_REPORT_BEFORE_THE_FLOOR) + 1
    feed = [
        category if category is other else {**category, "documents": category["documents"][:kept]}
        for category in categories
        if category in (qcmr, other)
    ]
    header = f"""# ruff: noqa: E501
# The City's document-finder feed for post 151831, as the old repo recorded it on July 28, 2026.
# Recording: ../gov-budget-data/data/phila/catalog-snapshots/document-finder/151831/{recording.name}
# It holds {len(data):,} bytes, and its sha256 is its name.
# The cut keeps 2 of its {len(categories)} categories, in feed order, with every field.
# "{QCMR}" keeps its first {kept} of {len(titles)} documents, through the last
# report before September 30, 2021, "{LAST_REPORT_BEFORE_THE_FLOOR}".
# "{OTHER}" is whole.
# Written on purpose, never by hand, by:
#   {COMMAND}
from typing import Any

FEED: list[dict[str, Any]] = """
    return header + pformat(feed, width=100, sort_dicts=False) + "\n"


if __name__ == "__main__":
    sys.stdout.write(cut(Path(sys.argv[1])))
