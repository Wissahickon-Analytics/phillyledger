from collections.abc import Iterator, Mapping
from hashlib import sha256
from io import BytesIO
from typing import Any

from botocore.awsrequest import AWSPreparedRequest, AWSResponse

from datadesk.core.parse_plan import WordKey
from datadesk.shell.adapters.s3 import S3Store
from datadesk.shell.ports import (
    Condition,
    CreateOnly,
    EffectError,
    Http,
    HttpResponse,
    IfMatch,
    ObjectStore,
    PreconditionFailed,
)


class FakeHttp:
    def __init__(self, bodies: Mapping[str, bytes]) -> None:
        self.bodies = dict(bodies)
        self.calls: list[str] = []

    def get(self, url: str) -> HttpResponse:
        self.calls.append(url)
        body = self.bodies.get(url)
        return HttpResponse(404, b"") if body is None else HttpResponse(200, body)


class DictStore:
    def __init__(self, objects: Mapping[str, bytes] | None = None) -> None:
        self.objects = dict(objects or {})
        self.puts: list[str] = []

    def put(self, key: str, data: bytes, condition: Condition) -> str:
        self.puts.append(key)
        held = self.objects.get(key)
        match condition:
            case CreateOnly() | IfMatch(None):
                if held is not None:
                    raise PreconditionFailed(key)
            case IfMatch(etag):
                if held is None or etag != _etag(held):
                    raise PreconditionFailed(key)
        self.objects[key] = data
        return _etag(data)

    def head(self, key: str) -> str | None:
        held = self.objects.get(key)
        return None if held is None else _etag(held)

    def get(self, key: str) -> bytes:
        return self.objects[key]


class DictCache:
    def __init__(self, entries: Mapping[WordKey, bytes] | None = None) -> None:
        self.entries = dict(entries or {})

    def get(self, key: WordKey) -> bytes | None:
        return self.entries.get(key)

    def put(self, key: WordKey, data: bytes) -> None:
        self.entries[key] = data

    def keys(self) -> frozenset[WordKey]:
        return frozenset(self.entries)


class FakePdf:
    def __init__(self, texts: Mapping[bytes, str]) -> None:
        self.texts = dict(texts)

    def page1_text(self, pdf: bytes) -> str:
        return self.texts[pdf]


class FlakyHttp:
    def __init__(self, inner: Http, url: str, failures: int) -> None:
        self.inner = inner
        self.url = url
        self.failures = failures

    def get(self, url: str) -> HttpResponse:
        if url == self.url and self.failures:
            self.failures -= 1
            raise EffectError(f"planted failure for {url}")
        return self.inner.get(url)


class FlakyStore:
    def __init__(self, inner: ObjectStore, failures: int) -> None:
        self.inner = inner
        self.failures = failures

    def put(self, key: str, data: bytes, condition: Condition) -> str:
        if self.failures:
            self.failures -= 1
            raise EffectError(f"planted failure for {key}")
        return self.inner.put(key, data, condition)

    def head(self, key: str) -> str | None:
        return self.inner.head(key)

    def get(self, key: str) -> bytes:
        return self.inner.get(key)


class LostReplyStore(FlakyStore):
    def put(self, key: str, data: bytes, condition: Condition) -> str:
        if self.failures:
            self.failures -= 1
            self.inner.put(key, data, condition)
            raise EffectError(f"planted lost reply for {key}")
        return self.inner.put(key, data, condition)


class Body(BytesIO):
    def stream(self, **_: Any) -> Iterator[bytes]:
        yield self.getvalue()


def answer(
    store: S3Store,
    status: int,
    headers: dict[str, str],
    body: bytes = b"",
    method: str | None = None,
) -> list[AWSPreparedRequest]:
    sent: list[AWSPreparedRequest] = []

    def send(request: AWSPreparedRequest, **_: Any) -> AWSResponse | None:
        if method not in (None, request.method):
            return None
        sent.append(request)
        return AWSResponse(request.url, status, headers, Body(body))

    store.client.meta.events.register("before-send.s3", send)
    return sent


def _etag(data: bytes) -> str:
    return f'"{sha256(data).hexdigest()}"'
