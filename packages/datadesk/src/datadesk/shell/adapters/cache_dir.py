"""A `LocalCache` adapter that keeps each entry as one file in a folder."""

from pathlib import Path
from uuid import uuid4

from datadesk.core.parse_plan import WordKey
from datadesk.shell.ports import EffectError


class DirCache:
    """Keep each cache entry as one file, named by its key, directly in one folder.

    Building one does no I/O. A missing folder holds no entry, and the first `put` makes it. A
    put writes the bytes to a file of another name in the folder and then renames that file
    onto the key's name, so a reader never sees half an entry, and a crash leaves only a file
    whose name is not a key. `keys` passes over every name that is not a `WordKey`, such as
    that file or ``.DS_Store``. Past a missing entry or folder, which reads as absent, every
    `OSError` becomes `EffectError`, chained.
    """

    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def get(self, key: WordKey) -> bytes | None:
        """Return the entry's bytes, or None when the entry or the folder is missing.

        Raises
        ------
        EffectError
            When the entry cannot be read, as when the folder path is a file.
        """
        try:
            return (self.folder / key).read_bytes()
        except FileNotFoundError:
            return None
        except OSError as error:
            raise EffectError(f"cannot read cache entry {key} in {self.folder}: {error}") from error

    def put(self, key: WordKey, data: bytes) -> None:
        """Store `data` as the entry for `key`, in place of any entry it had.

        The file of another name is ``.<key>.<32 random hex digits>.part``, so two puts at once
        write to different files.

        Raises
        ------
        EffectError
            When the folder cannot be made or the file cannot be written or renamed.
        """
        part = self.folder / f".{key}.{uuid4().hex}.part"
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            part.write_bytes(data)
            part.replace(self.folder / key)
        except OSError as error:
            raise EffectError(
                f"cannot write cache entry {key} in {self.folder}: {error}"
            ) from error

    def keys(self) -> frozenset[WordKey]:
        """Return the key of every entry, or none when the folder is missing.

        Raises
        ------
        EffectError
            When the folder cannot be listed, as when its path is a file.
        """
        try:
            names = [path.name for path in self.folder.iterdir()]
        except FileNotFoundError:
            return frozenset()
        except OSError as error:
            raise EffectError(f"cannot list cache folder {self.folder}: {error}") from error
        return frozenset(key for name in names if (key := _word_key(name)) is not None)


def _word_key(name: str) -> WordKey | None:
    try:
        return WordKey(name)
    except ValueError:
        return None
