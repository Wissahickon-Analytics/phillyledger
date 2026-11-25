"""The fetch executor: download the planned reports, then store what `plan_fetch` decides."""

from collections.abc import Callable
from contextlib import suppress
from functools import partial
from hashlib import sha256

from checkedtables.refs import Sha256
from datadesk.core.fetch import Fetched, FetchPlan, plan_fetch
from datadesk.core.watch import WatchPlan
from datadesk.shell.gather import RepoSnapshot
from datadesk.shell.ports import CreateOnly, Deps, EffectError, ObjectStore, PreconditionFailed

TRIES = 3


def retried[T](effect: Callable[[], T]) -> T:
    """Run `effect` up to `TRIES` times while it raises EffectError. The last failure propagates."""
    for _ in range(TRIES - 1):
        with suppress(EffectError):
            return effect()
    return effect()


def put_immutable(store: ObjectStore, key: str, data: bytes, sha: Sha256) -> None:
    """Put bytes under a key whose object must never change.

    `sha` is the `Sha256` of `data`. A key that already holds bytes with that sha counts as
    written, since a retry or a racing run may have put them.

    Raises
    ------
    PreconditionFailed
        When the key holds other bytes.
    EffectError
        When the put fails for another reason, or the bytes under the key cannot be read back.
    KeyError
        When the key holds no object by the time its bytes are read back.
    """
    try:
        store.put(key, data, CreateOnly())
    except PreconditionFailed:
        if sha256(store.get(key)).hexdigest() != sha:
            raise


def run_fetch(deps: Deps, plan: WatchPlan, repo: RepoSnapshot) -> FetchPlan:
    """Download each report the watch plan requests, then store each file the fetch plan names.

    Bytes stay in memory, keyed by their `Sha256`, until `plan_fetch` decides. Each GET and each
    put is tried up to `TRIES` times while it raises EffectError. It writes no file in the
    checkout.
    """
    held: dict[Sha256, bytes] = {}
    fetched: list[Fetched] = []
    for request in plan.fetch:
        response = retried(partial(deps.http.get, request.url))
        if response.status != 200:
            fetched.append(Fetched(request, response.status, None, 0, None))
            continue
        sha = Sha256(sha256(response.body).hexdigest())
        held[sha] = response.body
        page1 = deps.pdf.page1_text(response.body)
        fetched.append(Fetched(request, 200, sha, len(response.body), page1))
    result = plan_fetch(fetched, repo.index, ())
    for item in result.store:
        retried(partial(put_immutable, deps.store, item.dest_key, held[item.sha256], item.sha256))
    return result
