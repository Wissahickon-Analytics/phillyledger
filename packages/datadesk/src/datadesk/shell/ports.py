"""The ports through which the shell reaches the outside, and the errors they raise."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from checkedtables.refs import Sha256
from checkedtables.words import Document
from datadesk.core.parse_plan import WordKey


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """The status and body of one HTTP response."""

    status: int
    body: bytes

    @property
    def text(self) -> str:
        """The body decoded as UTF-8.

        Raises
        ------
        UnicodeDecodeError
            When the body is not UTF-8.
        """
        return self.body.decode("utf-8")


class Http(Protocol):
    """Answer GET requests by URL, from the web or from a folder that a browser saved."""

    def get(self, url: str) -> HttpResponse:
        """Return the status and body that `url` answers with.

        A failure to get any answer raises EffectError.
        """
        ...


@dataclass(frozen=True, slots=True)
class CreateOnly:
    """Write only when the key holds no object."""


@dataclass(frozen=True, slots=True)
class IfMatch:
    """Write only when the key's ETag is `etag`, or, when `etag` is None, when it holds none."""

    etag: str | None


type Condition = CreateOnly | IfMatch


class PreconditionFailed(Exception):
    """A conditional write found its key in a state the condition refuses.

    The message is the key. It is not an EffectError, so nothing tries the write again.
    """


class EffectError(Exception):
    """An effect failed, and trying it again may succeed."""


class ObjectStore(Protocol):
    """Objects stored by key in one bucket."""

    def put(self, key: str, data: bytes, condition: Condition) -> str:
        """Write `data` under `key` when `condition` holds, and return the new ETag.

        Raises
        ------
        PreconditionFailed
            When the condition does not hold.
        EffectError
            When the write fails for another reason.
        """
        ...

    def head(self, key: str) -> str | None:
        """Return the ETag of the object under `key`, or None when there is none.

        Raises
        ------
        EffectError
            When the request fails.
        """
        ...

    def get(self, key: str) -> bytes:
        """Return the bytes stored under `key`.

        Raises
        ------
        KeyError
            When no object has that key.
        EffectError
            When the read fails for another reason.
        """
        ...


class PdfReader(Protocol):
    """Read the text, words and drawn rules a PDF prints, and draw its pages."""

    def page1_text(self, pdf: bytes) -> str:
        """Return the text of the PDF's first page.

        Raises
        ------
        EffectError
            When the reader cannot read the file.
        """
        ...

    def words(self, pdf: bytes, sha256: Sha256, pages: Sequence[int]) -> Document:
        """Return the words and rules of the 1-based `pages`, ascending, or of every page.

        Empty `pages` means every page. `sha256` is the sha of `pdf`, which each page and word
        names. Each page's source is the text layer, with `tool` as its tool string.

        Raises
        ------
        EffectError
            When the file lacks a page in `pages`, or the reader cannot read one.
        """
        ...

    def render(self, pdf: bytes, page: int, dpi: int) -> bytes:
        """Return the whole 1-based `page` as a PNG at `dpi`, for OCR and review images.

        Raises
        ------
        EffectError
            When the file lacks the page, or the reader cannot draw it.
        """
        ...

    def tool(self) -> str:
        """Return the tool string of the pages `words` reads, so a caller can key them first."""
        ...


class LocalCache(Protocol):
    """Bytes kept on this machine under word keys, such as encoded documents."""

    def get(self, key: WordKey) -> bytes | None:
        """Return the bytes stored under `key`, or None when there are none.

        Raises
        ------
        EffectError
            When the read fails.
        """
        ...

    def put(self, key: WordKey, data: bytes) -> None:
        """Store `data` under `key`, in place of any bytes stored there.

        Raises
        ------
        EffectError
            When the write fails.
        """
        ...

    def keys(self) -> frozenset[WordKey]:
        """Return every key that holds bytes.

        Raises
        ------
        EffectError
            When the listing fails.
        """
        ...


@dataclass(frozen=True, slots=True)
class Deps:
    """The adapters a command runs with."""

    http: Http
    store: ObjectStore
    pdf: PdfReader
