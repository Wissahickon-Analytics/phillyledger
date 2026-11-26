from collections.abc import Callable
from pathlib import Path

import pytest
from packages.datadesk.tests.shell.fakes import DictCache

from datadesk.core.parse_plan import WordKey
from datadesk.shell.adapters.cache_dir import DirCache
from datadesk.shell.ports import EffectError, LocalCache

KEY = WordKey("0f1e2d3c4b5a69788796a5b4c3d2e1f05f238d579d4c1d7e2b3a4f5e6d7c8b9a")
OTHER_KEY = WordKey("9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b")

type MakeCache = Callable[[Path], LocalCache]


def dict_cache(_folder: Path) -> LocalCache:
    return DictCache()


def dir_cache(folder: Path) -> LocalCache:
    return DirCache(folder)


@pytest.fixture(params=[pytest.param(dict_cache, id="dict"), pytest.param(dir_cache, id="folder")])
def cache(request: pytest.FixtureRequest, tmp_path: Path) -> LocalCache:
    make: MakeCache = request.param
    return make(tmp_path / "cache")


def test_an_absent_key_gives_none_and_no_keys(cache: LocalCache) -> None:
    assert cache.get(KEY) is None
    assert cache.keys() == frozenset()


def test_a_put_is_read_back(cache: LocalCache) -> None:
    cache.put(KEY, b"words")
    assert cache.get(KEY) == b"words"
    assert cache.get(OTHER_KEY) is None


def test_a_second_put_replaces_the_entry(cache: LocalCache) -> None:
    cache.put(KEY, b"first")
    cache.put(KEY, b"second")
    assert cache.get(KEY) == b"second"
    assert cache.keys() == {KEY}


def test_keys_lists_each_key_that_was_put(cache: LocalCache) -> None:
    cache.put(KEY, b"words")
    cache.put(OTHER_KEY, b"")
    keys = cache.keys()
    assert keys == {KEY, OTHER_KEY}
    assert {type(key) for key in keys} == {WordKey}
    assert cache.get(OTHER_KEY) == b""


def test_a_second_cache_on_the_folder_reads_the_first_ones_entries(tmp_path: Path) -> None:
    DirCache(tmp_path / "cache").put(KEY, b"words")
    later = DirCache(tmp_path / "cache")
    assert later.get(KEY) == b"words"
    assert later.keys() == {KEY}


def test_a_put_makes_the_folder_and_leaves_one_file_named_by_the_key(tmp_path: Path) -> None:
    folder = tmp_path / "deep" / "cache"
    DirCache(folder).put(KEY, b"words")
    assert [path.name for path in folder.iterdir()] == [KEY]
    assert (folder / KEY).read_bytes() == b"words"


def test_building_a_cache_and_reading_a_missing_folder_make_nothing(tmp_path: Path) -> None:
    cache = DirCache(tmp_path / "cache")
    assert cache.get(KEY) is None
    assert cache.keys() == frozenset()
    assert list(tmp_path.iterdir()) == []


def test_keys_passes_over_a_name_that_is_not_a_key(tmp_path: Path) -> None:
    folder = tmp_path / "cache"
    cache = DirCache(folder)
    cache.put(KEY, b"words")
    for name in (".DS_Store", f".{OTHER_KEY}.c0ffee.part", OTHER_KEY.upper(), OTHER_KEY[:63]):
        (folder / name).write_bytes(b"junk")
    assert cache.keys() == {KEY}


@pytest.mark.parametrize(
    "effect",
    [
        pytest.param(lambda cache: cache.get(KEY), id="get"),
        pytest.param(lambda cache: cache.put(KEY, b"words"), id="put"),
        pytest.param(lambda cache: cache.keys(), id="keys"),
    ],
)
def test_a_folder_path_that_is_a_file_raises_effect_error(
    effect: Callable[[LocalCache], object], tmp_path: Path
) -> None:
    folder = tmp_path / "cache"
    folder.write_bytes(b"a file, not a folder")
    with pytest.raises(EffectError) as raised:
        effect(DirCache(folder))
    assert isinstance(raised.value.__cause__, OSError)
