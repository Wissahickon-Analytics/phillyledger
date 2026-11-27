import os
import shutil
from collections import defaultdict
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from types import ModuleType

import pytest
from packages.datadesk.tests.shell.fakes import DictCache, DictStore

from checkedtables.refs import Sha256
from datadesk.core.fetch import INDEX_PATH, pdf_key
from datadesk.core.index import parse_index
from datadesk.shell.adapters.pdf_pdfplumber import PdfPlumberReader
from datadesk.shell.cli import FIXTURE_FOLDER, fixture_command
from datadesk.shell.gather import CATALOG_PATH

REPO = Path(__file__).parents[1]
FIXTURES = REPO / FIXTURE_FOLDER
HELD_PDFS = "DATADESK_HELD_PDFS"
GRID_PAGES = {
    "qcmr:2022-09-30:none": (35, 36),
    "qcmr:2022-12-31:none": (35, 36),
    "qcmr:2023-03-31:none": (34, 35),
    "qcmr:2023-06-30:none": (32, 33),
    "qcmr:2023-09-30:none": (33, 34),
    "qcmr:2023-12-31:none": (32, 33),
    "qcmr:2024-03-31:none": (32, 33),
    "qcmr:2024-06-30:none": (32, 33),
    "qcmr:2024-09-30:none": (33, 34),
    "qcmr:2024-12-31:none": (34, 35),
}


def fixture(stem: str) -> ModuleType:
    return import_module(f"{FIXTURE_FOLDER.replace('/', '.')}.{stem}")


def held_fixtures() -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(FIXTURES.glob("*.py"))}


def grid_stem(edition: str, page: int) -> str:
    series, end, stage = edition.split(":")
    edition_part = "_".join([series, end.replace("-", "_"), *([] if stage == "none" else [stage])])
    return f"{edition_part}_p{page}"


def test_each_word_fixture_regenerates_byte_identical(tmp_path: Path) -> None:
    folder = os.environ.get(HELD_PDFS)
    if not folder:
        pytest.skip(f"set {HELD_PDFS} to a folder that holds the archived PDFs")
    held_bytes = [path.read_bytes() for path in sorted(Path(folder).glob("*.pdf"))]
    pdfs = {Sha256(sha256(data).hexdigest()): data for data in held_bytes}
    root = tmp_path / "checkout"
    for path in (CATALOG_PATH, INDEX_PATH):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / path, root / path)
    held = held_fixtures()
    pages: dict[Sha256, list[int]] = defaultdict(list)
    for name in held:
        module = fixture(name.removesuffix(".py"))
        pages[module.SHA].append(module.PAGE.number)
    unheld = sorted(sha for sha in pages if sha not in pdfs)
    assert unheld == [], f"{HELD_PDFS} holds no PDF with these shas: {unheld}"
    store = DictStore({pdf_key(sha): data for sha, data in pdfs.items()})
    for sha, numbers in sorted(pages.items()):
        pages_text = ",".join(str(number) for number in numbers)
        fixture_command(store, PdfPlumberReader(), DictCache(), root, sha=sha, pages=pages_text)
    written = {path.name: path.read_bytes() for path in sorted((root / FIXTURE_FOLDER).iterdir())}
    assert sorted(written) == sorted(held)
    assert [name for name in held if written[name] != held[name]] == []


def test_no_word_of_the_twenty_grid_pages_holds_a_font_code() -> None:
    index = parse_index((REPO / INDEX_PATH).read_text(encoding="utf-8"))
    current = {
        version.edition.id(): version.sha256
        for version in index.versions
        if index.current(version.edition) == version
    }
    wanted = [(edition, page) for edition, numbers in GRID_PAGES.items() for page in numbers]
    missing = [
        grid_stem(edition, page)
        for edition, page in wanted
        if not (FIXTURES / f"{grid_stem(edition, page)}.py").exists()
    ]
    assert missing == []
    for edition, page in wanted:
        module = fixture(grid_stem(edition, page))
        assert (edition, module.SHA) == (edition, current[edition])
        assert module.PAGE.number == page
        assert [word.text for word in module.PAGE.words[:2]] == ["TABLE", "P-1"]
        assert module.PAGE.rotation == 90
        assert [word.text for word in module.PAGE.words if "(cid:" in word.text] == []
