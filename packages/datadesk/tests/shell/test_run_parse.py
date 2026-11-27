from collections.abc import Callable, Sequence
from hashlib import sha256
from pathlib import Path

import pytest
from packages.datadesk.tests.shell.fakes import DictCache, DictStore
from packages.datadesk.tests.shell.pdfs import RULES, STYLED, drawn_pdf, text_pdf

from checkedtables.kinds import SourceKind
from checkedtables.refs import Sha256
from checkedtables.words import Document
from datadesk.core.codec import decode_document
from datadesk.core.fetch import pdf_key
from datadesk.core.parse_plan import WordJob, WordKey, word_key
from datadesk.shell.adapters.cache_dir import DirCache
from datadesk.shell.adapters.pdf_pdfplumber import PdfPlumberReader
from datadesk.shell.ports import LocalCache, PdfReader
from datadesk.shell.run_parse import extract_words, merged_document

STYLED_PDF = drawn_pdf(
    f"{STYLED} {RULES}",
    "BT /F1 12 Tf 72 680 Td (Revenue) Tj ET BT /F2 9 Tf 300 680 Td (5,678) Tj ET "
    "72 650 300 0.72 re f",
)
STYLED_SHA = Sha256(sha256(STYLED_PDF).hexdigest())
TWO_PAGES = text_pdf("ONE", "TWO")
TWO_PAGES_SHA = Sha256(sha256(TWO_PAGES).hexdigest())
TOOL = PdfPlumberReader().tool()

type Caches = Callable[[Path], tuple[LocalCache, LocalCache]]


class KeepingReader:
    def __init__(self, inner: PdfReader) -> None:
        self.inner = inner
        self.kept: list[Document] = []

    def page1_text(self, pdf: bytes) -> str:
        return self.inner.page1_text(pdf)

    def words(self, pdf: bytes, sha256: Sha256, pages: Sequence[int]) -> Document:
        document = self.inner.words(pdf, sha256, pages)
        self.kept.append(document)
        return document

    def render(self, pdf: bytes, page: int, dpi: int) -> bytes:
        return self.inner.render(pdf, page, dpi)

    def tool(self) -> str:
        return self.inner.tool()


def job(sha: Sha256, pages: tuple[int, ...], source: SourceKind = SourceKind.TEXT_LAYER) -> WordJob:
    return WordJob(sha, pages, source, None, word_key(sha, pages, TOOL))


def store() -> DictStore:
    return DictStore({pdf_key(STYLED_SHA): STYLED_PDF, pdf_key(TWO_PAGES_SHA): TWO_PAGES})


def one_dict_cache(_folder: Path) -> tuple[LocalCache, LocalCache]:
    cache = DictCache()
    return cache, cache


def two_dir_caches(folder: Path) -> tuple[LocalCache, LocalCache]:
    return DirCache(folder), DirCache(folder)


@pytest.mark.parametrize(
    "caches",
    [pytest.param(one_dict_cache, id="dict"), pytest.param(two_dir_caches, id="folder")],
)
def test_a_cache_hit_returns_an_equal_document(caches: Caches, tmp_path: Path) -> None:
    reader = KeepingReader(PdfPlumberReader())
    pages = (1, 2)
    wanted = WordJob(
        STYLED_SHA, pages, SourceKind.TEXT_LAYER, None, word_key(STYLED_SHA, pages, reader.tool())
    )

    def run(cache: LocalCache) -> Document:
        held = cache.keys()
        missing = [] if wanted.cache_key in held else [wanted]
        extract_words(store(), reader, cache, missing)
        return merged_document(cache, (wanted.cache_key,))

    first_cache, second_cache = caches(tmp_path / "words")
    first = run(first_cache)
    assert len(reader.kept) == 1
    second = run(second_cache)
    assert len(reader.kept) == 1
    (kept,) = reader.kept
    assert [page.number for page in kept.pages] == [1, 2]
    words = [word for page in kept.pages for word in page.words]
    assert {word.bold for word in words} == {True, False}
    assert {word.size for word in words} == {12.0, 9.0}
    assert all(page.rules for page in kept.pages)
    assert kept.pages[0].rules != kept.pages[1].rules
    assert first == kept
    assert second == kept


def test_extract_words_caches_each_jobs_pages_under_its_own_key() -> None:
    cache = DictCache()
    first, second = job(TWO_PAGES_SHA, (1,)), job(TWO_PAGES_SHA, (2,))
    extract_words(store(), PdfPlumberReader(), cache, [first, second])
    assert cache.keys() == {first.cache_key, second.cache_key}
    for each, number in ((first, 1), (second, 2)):
        document = decode_document(cache.entries[each.cache_key])
        assert [page.number for page in document.pages] == [number]


def test_extract_words_reads_a_job_whose_key_the_cache_holds() -> None:
    reader = KeepingReader(PdfPlumberReader())
    wanted = job(TWO_PAGES_SHA, ())
    cache = DictCache({wanted.cache_key: b"stale"})
    extract_words(store(), reader, cache, [wanted])
    assert len(reader.kept) == 1
    assert decode_document(cache.entries[wanted.cache_key]) == reader.kept[0]


def test_extract_words_refuses_a_job_of_another_source_before_reading_any() -> None:
    reader = KeepingReader(PdfPlumberReader())
    cache = DictCache()
    jobs = [job(TWO_PAGES_SHA, (1,)), job(TWO_PAGES_SHA, (2,), SourceKind.OCR)]
    with pytest.raises(ValueError, match="text layer"):
        extract_words(store(), reader, cache, jobs)
    assert reader.kept == []
    assert cache.keys() == frozenset()


def cached(*jobs: WordJob) -> DictCache:
    cache = DictCache()
    extract_words(store(), PdfPlumberReader(), cache, jobs)
    return cache


def test_merged_document_joins_the_pages_of_its_keys_ascending() -> None:
    first, second = job(TWO_PAGES_SHA, (1,)), job(TWO_PAGES_SHA, (2,))
    merged = merged_document(cached(first, second), (second.cache_key, first.cache_key))
    assert merged == PdfPlumberReader().words(TWO_PAGES, TWO_PAGES_SHA, ())


def test_merged_document_of_a_key_the_cache_lacks_is_a_key_error() -> None:
    held, absent = job(TWO_PAGES_SHA, (1,)), job(TWO_PAGES_SHA, (2,))
    with pytest.raises(KeyError, match=absent.cache_key):
        merged_document(cached(held), (held.cache_key, absent.cache_key))


@pytest.mark.parametrize(
    "jobs",
    [
        pytest.param((), id="no_key"),
        pytest.param(
            (job(TWO_PAGES_SHA, (1,)), job(TWO_PAGES_SHA, (1, 2))), id="a_page_in_two_entries"
        ),
        pytest.param((job(TWO_PAGES_SHA, (2,)), job(STYLED_SHA, (1,))), id="two_files"),
    ],
)
def test_merged_document_refuses_keys_that_make_no_one_document(jobs: tuple[WordJob, ...]) -> None:
    keys: tuple[WordKey, ...] = tuple(each.cache_key for each in jobs)
    with pytest.raises(ValueError):
        merged_document(cached(*jobs), keys)
