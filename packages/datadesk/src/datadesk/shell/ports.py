from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8")


class Http(Protocol):
    def get(self, url: str) -> HttpResponse: ...


@dataclass(frozen=True, slots=True)
class CreateOnly:
    pass


@dataclass(frozen=True, slots=True)
class IfMatch:
    etag: str | None


type Condition = CreateOnly | IfMatch


class PreconditionFailed(Exception):
    pass


class EffectError(Exception):
    pass


class ObjectStore(Protocol):
    def put(self, key: str, data: bytes, condition: Condition) -> str: ...

    def head(self, key: str) -> str | None: ...

    def get(self, key: str) -> bytes: ...


class PdfReader(Protocol):
    def page1_text(self, pdf: bytes) -> str: ...


@dataclass(frozen=True, slots=True)
class Deps:
    http: Http
    store: ObjectStore
    pdf: PdfReader
