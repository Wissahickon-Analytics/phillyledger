import os
from collections.abc import Callable
from uuid import uuid4

import pytest
from packages.datadesk.tests.shell.fakes import DictStore

from datadesk.shell.adapters.s3 import s3_store
from datadesk.shell.ports import CreateOnly, IfMatch, ObjectStore, PreconditionFailed
from datadesk.shell.settings import Settings

CONTRACT_VARIABLES = (
    "DATADESK_CONTRACT_S3_ENDPOINT_URL",
    "DATADESK_CONTRACT_S3_ACCESS_KEY_ID",
    "DATADESK_CONTRACT_S3_SECRET_ACCESS_KEY",
    "DATADESK_CONTRACT_S3_BUCKET",
)


def dict_store() -> ObjectStore:
    return DictStore()


def contract_s3_store() -> ObjectStore:
    values = [os.environ.get(name, "") for name in CONTRACT_VARIABLES]
    if not all(values):
        pytest.skip(f"set {', '.join(CONTRACT_VARIABLES)} to run the S3 half of the contract")
    return s3_store(Settings(*values))


@pytest.fixture(
    params=[
        pytest.param(dict_store, id="dict"),
        pytest.param(contract_s3_store, id="s3", marks=pytest.mark.enable_socket),
    ]
)
def store(request: pytest.FixtureRequest) -> ObjectStore:
    make: Callable[[], ObjectStore] = request.param
    return make()


@pytest.fixture
def key() -> str:
    return f"contract/{uuid4().hex}/object.pdf"


def test_a_create_on_an_absent_key_stores_the_bytes(store: ObjectStore, key: str) -> None:
    etag = store.put(key, b"first", CreateOnly())
    assert store.get(key) == b"first"
    assert store.head(key) == etag


def test_a_replacement_with_the_current_etag_stores_the_new_bytes(
    store: ObjectStore, key: str
) -> None:
    first = store.put(key, b"first", CreateOnly())
    second = store.put(key, b"second", IfMatch(first))
    assert second != first
    assert store.get(key) == b"second"
    assert store.head(key) == second


def test_a_stale_etag_is_refused_and_the_bytes_are_kept(store: ObjectStore, key: str) -> None:
    first = store.put(key, b"first", CreateOnly())
    second = store.put(key, b"second", IfMatch(first))
    with pytest.raises(PreconditionFailed):
        store.put(key, b"third", IfMatch(first))
    assert store.get(key) == b"second"
    assert store.head(key) == second


def test_create_only_on_a_key_that_exists_is_refused_and_the_bytes_are_kept(
    store: ObjectStore, key: str
) -> None:
    first = store.put(key, b"first", CreateOnly())
    with pytest.raises(PreconditionFailed):
        store.put(key, b"second", CreateOnly())
    assert store.get(key) == b"first"
    assert store.head(key) == first


def test_if_match_none_creates_an_absent_key(store: ObjectStore, key: str) -> None:
    etag = store.put(key, b"first", IfMatch(None))
    assert store.get(key) == b"first"
    assert store.head(key) == etag


def test_if_match_none_on_a_key_that_exists_is_refused_and_the_bytes_are_kept(
    store: ObjectStore, key: str
) -> None:
    first = store.put(key, b"first", CreateOnly())
    with pytest.raises(PreconditionFailed):
        store.put(key, b"second", IfMatch(None))
    assert store.get(key) == b"first"
    assert store.head(key) == first


def test_an_absent_key_has_no_etag_and_no_bytes(store: ObjectStore, key: str) -> None:
    assert store.head(key) is None
    with pytest.raises(KeyError):
        store.get(key)
