"""The settings of the archive bucket on R2, read once from the environment."""

from collections.abc import Mapping
from dataclasses import dataclass, field

VARIABLES = (
    "DATADESK_R2_ENDPOINT_URL",
    "DATADESK_R2_ACCESS_KEY_ID",
    "DATADESK_R2_SECRET_ACCESS_KEY",
    "DATADESK_R2_ARCHIVE_BUCKET",
)


@dataclass(frozen=True, slots=True)
class Settings:
    """Where the archive bucket is, and the keys that open it. Its repr leaves both keys out."""

    endpoint_url: str
    access_key_id: str = field(repr=False)
    secret_access_key: str = field(repr=False)
    archive_bucket: str


class MissingSettings(Exception):
    """A variable that `load_settings` needs is unset or empty. The message names no value."""


def load_settings(environ: Mapping[str, str]) -> Settings:
    """Read the four DATADESK_R2_* variables from `environ`.

    Raises
    ------
    MissingSettings
        Naming every variable that is unset or empty.
    """
    if missing := [name for name in VARIABLES if not environ.get(name)]:
        raise MissingSettings(f"set {', '.join(missing)} in the environment")
    return Settings(*(environ[name] for name in VARIABLES))


def hide_keys(text: str, settings: Settings) -> str:
    """Replace each non-empty key in `text` with `$` and the name of its variable.

    A service message that echoes the access key then prints `$DATADESK_R2_ACCESS_KEY_ID` in
    its place. Everything `datadesk` prints after the settings load passes through here.
    """
    keys = {
        "DATADESK_R2_ACCESS_KEY_ID": settings.access_key_id,
        "DATADESK_R2_SECRET_ACCESS_KEY": settings.secret_access_key,
    }
    for name, key in keys.items():
        if key:
            text = text.replace(key, f"${name}")
    return text
