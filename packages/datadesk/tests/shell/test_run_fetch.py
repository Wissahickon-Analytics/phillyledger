from hashlib import sha256

import pytest
from packages.datadesk.tests.shell.fakes import DictStore

from checkedtables.refs import Sha256
from datadesk.shell.ports import PreconditionFailed
from datadesk.shell.run_fetch import put_immutable

REPORT = b"%PDF-1.4 the report\n"
SHA = Sha256(sha256(REPORT).hexdigest())
KEY = f"pdf/{SHA[:2]}/{SHA}.pdf"


def test_put_immutable_stores_the_bytes_under_an_absent_key() -> None:
    store = DictStore()
    put_immutable(store, KEY, REPORT, SHA)
    assert store.objects == {KEY: REPORT}


def test_put_immutable_completes_when_the_store_holds_the_same_bytes() -> None:
    store = DictStore({KEY: REPORT})
    put_immutable(store, KEY, REPORT, SHA)
    assert store.objects == {KEY: REPORT}
    assert store.puts == [KEY]


def test_put_immutable_raises_when_the_store_holds_other_bytes() -> None:
    store = DictStore({KEY: b"other bytes"})
    with pytest.raises(PreconditionFailed):
        put_immutable(store, KEY, REPORT, SHA)
    assert store.objects == {KEY: b"other bytes"}
