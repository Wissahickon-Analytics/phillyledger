from collections.abc import Callable
from contextlib import suppress
from functools import partial
from hashlib import sha256

from datadesk.core.fetch import Fetched, FetchPlan, plan_fetch
from datadesk.core.watch import WatchPlan
from datadesk.shell.gather import RepoSnapshot
from datadesk.shell.ports import CreateOnly, Deps, EffectError, ObjectStore, PreconditionFailed

TRIES = 3


def retried[T](effect: Callable[[], T]) -> T:
    for _ in range(TRIES - 1):
        with suppress(EffectError):
            return effect()
    return effect()


def put_immutable(store: ObjectStore, key: str, data: bytes, sha: str) -> None:
    try:
        store.put(key, data, CreateOnly())
    except PreconditionFailed:
        if sha256(store.get(key)).hexdigest() != sha:
            raise


def run_fetch(deps: Deps, plan: WatchPlan, repo: RepoSnapshot) -> FetchPlan:
    held: dict[str, bytes] = {}
    fetched: list[Fetched] = []
    for request in plan.fetch:
        response = retried(partial(deps.http.get, request.url))
        if response.status != 200:
            fetched.append(Fetched(request, response.status, None, 0, None))
            continue
        sha = sha256(response.body).hexdigest()
        held[sha] = response.body
        page1 = deps.pdf.page1_text(response.body)
        fetched.append(Fetched(request, 200, sha, len(response.body), page1))
    result = plan_fetch(fetched, repo.index, ())
    for item in result.store:
        retried(partial(put_immutable, deps.store, item.dest_key, held[item.sha256], item.sha256))
    return result
