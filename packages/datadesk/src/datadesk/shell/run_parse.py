"""The words executor: read the pages that word jobs name into the word cache, and join them.

These are the word lines of `run_parse` in design section 4.4. The caller reads
`LocalCache.keys` once and passes only the jobs whose keys are missing, so `extract_words`
never reads the cache to decide again.
"""

from collections.abc import Sequence

from checkedtables.kinds import SourceKind
from checkedtables.words import Document
from datadesk.core.codec import decode_document, encode_document
from datadesk.core.fetch import pdf_key
from datadesk.core.parse_plan import WordJob, WordKey
from datadesk.shell.ports import LocalCache, ObjectStore, PdfReader


def extract_words(
    store: ObjectStore, pdf: PdfReader, cache: LocalCache, jobs: Sequence[WordJob]
) -> None:
    """Read each job's pages from its archived PDF, and cache them under the job's key.

    Each job is read and put, in place of any entry its key has, whether or not the cache
    holds the key. A job's `compare` source is for the planner to schedule as a job of its own.

    Raises
    ------
    ValueError
        When a job's source is not the text layer, before any job is read, since the PDF reader
        reads the text layer alone.
    KeyError
        When the archive holds no PDF of a job's sha.
    EffectError
        When the store, the reader or the cache fails.
    """
    if refused := [job for job in jobs if job.source is not SourceKind.TEXT_LAYER]:
        raise ValueError(
            f"the PDF reader reads the text layer alone, and these jobs ask for another: {refused}"
        )
    for job in jobs:
        document = pdf.words(store.get(pdf_key(job.doc_sha256)), job.doc_sha256, job.pages)
        cache.put(job.cache_key, encode_document(document))


def merged_document(cache: LocalCache, keys: Sequence[WordKey]) -> Document:
    """Return one document that holds the pages of every document cached under `keys`.

    The pages come back ascending, whatever the order of `keys`.

    Raises
    ------
    KeyError
        When the cache holds no entry for a key.
    ValueError
        When `keys` is empty, since no document then names its file, when the entries are of
        two files, when a page is in two entries, or when an entry does not decode.
    EffectError
        When the cache fails.
    """
    if not keys:
        raise ValueError("no word key to merge")
    documents = [decode_document(_entry(cache, key)) for key in keys]
    if len(files := {document.sha256 for document in documents}) > 1:
        raise ValueError(f"the word keys hold pages of {len(files)} files: {sorted(files)}")
    pages = sorted(
        (page for document in documents for page in document.pages), key=lambda page: page.number
    )
    return Document(documents[0].sha256, tuple(pages))


def _entry(cache: LocalCache, key: WordKey) -> bytes:
    if (data := cache.get(key)) is None:
        raise KeyError(f"the word cache holds no entry {key}")
    return data
