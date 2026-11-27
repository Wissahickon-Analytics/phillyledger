import os
import shutil
from collections import defaultdict
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from types import ModuleType

import pytest
from packages.datadesk.tests.fixtures.p1 import RUNS
from packages.datadesk.tests.shell.fakes import DictCache, DictStore

from checkedtables.refs import Sha256
from datadesk.core.codec import render_fixture
from datadesk.core.fetch import INDEX_PATH, pdf_key
from datadesk.core.index import parse_index
from datadesk.shell.adapters.pdf_pdfplumber import PdfPlumberReader
from datadesk.shell.cli import FIXTURE_FOLDER, fixture_command
from datadesk.shell.gather import CATALOG_PATH

REPO = Path(__file__).parents[1]
FIXTURES = REPO / FIXTURE_FOLDER
HELD_PDFS = "DATADESK_HELD_PDFS"


def fixture(stem: str) -> ModuleType:
    return import_module(f"{FIXTURE_FOLDER.replace('/', '.')}.{stem}")


def held_fixtures() -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(FIXTURES.glob("*.py"))}


def stem(edition: str, page: int) -> str:
    series, end, stage = edition.split(":")
    edition_part = "_".join([series, end.replace("-", "_"), *([] if stage == "none" else [stage])])
    return f"{edition_part}_p{page}"


def p1_pages() -> list[tuple[str, int, int]]:
    commentary = [(run.edition, run.commentary, 0) for run in RUNS if run.commentary is not None]
    grid = [(run.edition, page, 90) for run in RUNS for page in run.grid]
    return commentary + grid


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


def test_each_word_fixture_is_the_text_render_fixture_writes_of_its_page() -> None:
    held = held_fixtures()
    assert len(held) == 56
    for name, data in held.items():
        module = fixture(name.removesuffix(".py"))
        assert render_fixture(module.PAGE).encode("utf-8") == data, name


def test_each_p1_page_has_a_fixture_of_its_indexed_sha() -> None:
    index = parse_index((REPO / INDEX_PATH).read_text(encoding="utf-8"))
    pages = p1_pages()
    assert (len(pages), sum(rotation == 90 for _, _, rotation in pages)) == (56, 40)
    assert sorted(f"{stem(edition, page)}.py" for edition, page, _ in pages) == sorted(
        held_fixtures()
    )
    for edition, page, rotation in pages:
        module = fixture(stem(edition, page))
        version = index.by_sha(module.SHA)
        assert version is not None, stem(edition, page)
        assert version.edition.id() == edition, stem(edition, page)
        assert module.PAGE.number == page
        assert module.PAGE.rotation == rotation, stem(edition, page)
        assert [word.text for word in module.PAGE.words[:2]] == ["TABLE", "P-1"]


def test_no_word_of_the_p1_pages_holds_a_font_code() -> None:
    for edition, page, _ in p1_pages():
        words = fixture(stem(edition, page)).PAGE.words
        assert [word.text for word in words if "(cid:" in word.text] == [], stem(edition, page)
