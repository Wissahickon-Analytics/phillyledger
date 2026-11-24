from collections.abc import Callable, Iterator
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from botocore.awsrequest import AWSPreparedRequest, AWSResponse
from botocore.exceptions import EndpointConnectionError

from datadesk.shell.adapters.s3 import S3Store, s3_store
from datadesk.shell.ports import CreateOnly, EffectError, IfMatch, PreconditionFailed
from datadesk.shell.settings import Settings

SETTINGS = Settings(
    endpoint_url="http://store.invalid:9000",
    access_key_id="SETTINGSKEYPLANTED",
    secret_access_key="settings-secret-PLANTED",
    archive_bucket="archive",
)
AMBIENT_CONFIG = """\
[default]
aws_access_key_id = CONFIGKEYPLANTED
aws_secret_access_key = config-secret
region = us-west-2
s3 =
  addressing_style = virtual
"""
AMBIENT_CREDENTIALS = """\
[default]
aws_access_key_id = CREDENTIALSKEYPLANTED
aws_secret_access_key = credentials-secret
"""


class Body(BytesIO):
    def stream(self, **_: Any) -> Iterator[bytes]:
        yield self.getvalue()


def answer(
    store: S3Store, status: int, headers: dict[str, str], body: bytes = b""
) -> list[AWSPreparedRequest]:
    sent: list[AWSPreparedRequest] = []

    def send(request: AWSPreparedRequest, **_: Any) -> AWSResponse:
        sent.append(request)
        return AWSResponse(request.url, status, headers, Body(body))

    store.client.meta.events.register("before-send.s3", send)
    return sent


def header(request: AWSPreparedRequest, name: str) -> str:
    value = request.headers[name]
    return value.decode() if isinstance(value, bytes) else value


def error(code: str) -> bytes:
    return f"<Error><Code>{code}</Code><Message>planted</Message></Error>".encode()


def test_s3_client_ignores_the_ambient_aws_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "config").write_text(AMBIENT_CONFIG)
    (tmp_path / "credentials").write_text(AMBIENT_CREDENTIALS)
    monkeypatch.setenv("AWS_PROFILE", "a-profile-that-does-not-exist")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "config"))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "credentials"))
    store = s3_store(SETTINGS)
    sent = answer(store, 200, {"ETag": '"etag-1"'})
    assert store.put("pdf/7c/7c4a.pdf", b"report", CreateOnly()) == '"etag-1"'
    (request,) = sent
    authorization = header(request, "Authorization")
    assert "Credential=SETTINGSKEYPLANTED/" in authorization
    assert "/auto/s3/" in authorization
    assert request.url == "http://store.invalid:9000/archive/pdf/7c/7c4a.pdf"


@pytest.mark.parametrize(
    ("condition", "name", "value"),
    [
        pytest.param(CreateOnly(), "If-None-Match", "*", id="create_only"),
        pytest.param(IfMatch(None), "If-None-Match", "*", id="if_match_none"),
        pytest.param(IfMatch('"etag-0"'), "If-Match", '"etag-0"', id="if_match_an_etag"),
    ],
)
def test_each_condition_sends_its_header(
    condition: CreateOnly | IfMatch, name: str, value: str
) -> None:
    store = s3_store(SETTINGS)
    sent = answer(store, 200, {"ETag": '"etag-1"'})
    store.put("key", b"data", condition)
    (request,) = sent
    assert header(request, name) == value
    other = "If-Match" if name == "If-None-Match" else "If-None-Match"
    assert other not in request.headers


@pytest.mark.parametrize(
    ("call", "status", "body", "raised"),
    [
        pytest.param(
            lambda store: store.put("key", b"data", CreateOnly()),
            412,
            error("PreconditionFailed"),
            PreconditionFailed,
            id="a_put_refused_by_its_condition",
        ),
        pytest.param(
            lambda store: store.put("key", b"data", CreateOnly()),
            500,
            error("InternalError"),
            EffectError,
            id="a_put_the_server_fails",
        ),
        pytest.param(
            lambda store: store.put("key", b"data", CreateOnly()),
            403,
            error("AccessDenied"),
            EffectError,
            id="a_put_the_server_refuses",
        ),
        pytest.param(
            lambda store: store.get("key"), 404, error("NoSuchKey"), KeyError, id="a_get_of_no_key"
        ),
        pytest.param(
            lambda store: store.get("key"),
            503,
            error("SlowDown"),
            EffectError,
            id="a_get_that_fails",
        ),
        pytest.param(
            lambda store: store.head("key"), 403, b"", EffectError, id="a_head_that_fails"
        ),
    ],
)
def test_each_failure_becomes_the_port_s_error(
    call: Callable[[S3Store], object], status: int, body: bytes, raised: type[Exception]
) -> None:
    store = s3_store(SETTINGS)
    answer(store, status, {}, body)
    with pytest.raises(raised) as caught:
        call(store)
    assert caught.type is raised


def test_a_head_reads_the_etag_or_none_and_a_get_reads_the_bytes() -> None:
    absent, present, read = s3_store(SETTINGS), s3_store(SETTINGS), s3_store(SETTINGS)
    answer(absent, 404, {})
    answer(present, 200, {"ETag": '"etag-1"'})
    answer(read, 200, {"ETag": '"etag-1"'}, b"report bytes")
    assert absent.head("key") is None
    assert present.head("key") == '"etag-1"'
    assert read.get("key") == b"report bytes"


def test_a_failure_to_connect_is_an_effect_error() -> None:
    store = s3_store(SETTINGS)

    def refuse(**_: Any) -> None:
        raise EndpointConnectionError(endpoint_url=SETTINGS.endpoint_url)

    store.client.meta.events.register("before-send.s3", refuse)
    with pytest.raises(EffectError):
        store.put("key", b"data", CreateOnly())
