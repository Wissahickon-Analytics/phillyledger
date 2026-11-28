import os
from hashlib import sha256
from pathlib import Path

import pytest
from packages.datadesk.tests.fixtures.p1 import RUNS
from tests.test_qcmr_positions import BY_EDITION, checked_table, context
from tests.test_registry_data import versions

from checkedtables.refs import Sha256
from datadesk.core.tables.qcmr_positions import parse
from datadesk.shell.adapters.pdf_pdfplumber import PdfPlumberReader

HELD_PDFS = "DATADESK_HELD_PDFS"


def test_each_held_report_parses_whole() -> None:
    folder = os.environ.get(HELD_PDFS)
    if not folder:
        pytest.skip(f"set {HELD_PDFS} to a folder that holds the archived QCMR reports")
    indexed = {
        name: version for name, version in versions().items() if version.edition.series == "qcmr"
    }
    assert sorted(indexed) == sorted(run.edition for run in RUNS)
    held = {
        Sha256(sha256(path.read_bytes()).hexdigest()): path for path in Path(folder).glob("*.pdf")
    }
    missing = sorted(name for name, version in indexed.items() if version.sha256 not in held)
    assert missing == [], f"{HELD_PDFS} holds no file of these editions: {missing}"
    reader = PdfPlumberReader()
    for name, version in sorted(indexed.items()):
        run = BY_EDITION[name]
        doc = reader.words(held[version.sha256].read_bytes(), version.sha256, ())
        result = parse(doc, context(name))
        checked_table(result, run)
        commentary = [
            finding.page for finding in result.findings if finding.code == "commentary_page"
        ]
        assert commentary == ([] if run.commentary is None else [run.commentary]), name
