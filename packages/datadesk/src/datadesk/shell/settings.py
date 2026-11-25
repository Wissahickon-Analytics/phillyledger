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
    endpoint_url: str
    access_key_id: str = field(repr=False)
    secret_access_key: str = field(repr=False)
    archive_bucket: str


class MissingSettings(Exception):
    pass


def load_settings(environ: Mapping[str, str]) -> Settings:
    if missing := [name for name in VARIABLES if not environ.get(name)]:
        raise MissingSettings(f"set {', '.join(missing)} in the environment")
    return Settings(*(environ[name] for name in VARIABLES))


def hide_keys(text: str, settings: Settings) -> str:
    keys = {
        "DATADESK_R2_ACCESS_KEY_ID": settings.access_key_id,
        "DATADESK_R2_SECRET_ACCESS_KEY": settings.secret_access_key,
    }
    for name, key in keys.items():
        if key:
            text = text.replace(key, f"${name}")
    return text
