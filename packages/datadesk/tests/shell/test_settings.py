import pytest

from datadesk.shell.settings import MissingSettings, Settings, load_settings

ENDPOINT = "https://account-PLANTED.r2.cloudflarestorage.com"
ACCESS_KEY = "access-key-PLANTED"
SECRET = "secret-key-PLANTED"
BUCKET = "bucket-PLANTED"
ENVIRON = {
    "DATADESK_R2_ENDPOINT_URL": ENDPOINT,
    "DATADESK_R2_ACCESS_KEY_ID": ACCESS_KEY,
    "DATADESK_R2_SECRET_ACCESS_KEY": SECRET,
    "DATADESK_R2_ARCHIVE_BUCKET": BUCKET,
}


def test_load_settings_reads_the_four_variables() -> None:
    environ = {**ENVIRON, "AWS_ACCESS_KEY_ID": "ambient", "DATADESK_R2_OTHER": "x"}
    assert load_settings(environ) == Settings(ENDPOINT, ACCESS_KEY, SECRET, BUCKET)


def test_settings_keep_both_keys_out_of_their_repr() -> None:
    shown = repr(load_settings(ENVIRON))
    assert ENDPOINT in shown
    assert BUCKET in shown
    assert ACCESS_KEY not in shown
    assert SECRET not in shown


@pytest.mark.parametrize(
    "missing",
    [
        pytest.param(("DATADESK_R2_SECRET_ACCESS_KEY",), id="one_variable"),
        pytest.param(
            ("DATADESK_R2_ENDPOINT_URL", "DATADESK_R2_ARCHIVE_BUCKET"), id="two_variables"
        ),
        pytest.param(tuple(ENVIRON), id="every_variable"),
    ],
)
def test_load_settings_names_each_missing_variable_and_prints_no_value(
    missing: tuple[str, ...],
) -> None:
    environ = {name: value for name, value in ENVIRON.items() if name not in missing}
    with pytest.raises(MissingSettings) as raised:
        load_settings(environ)
    message = str(raised.value)
    assert [name for name in ENVIRON if name in message] == list(missing)
    assert not [value for value in ENVIRON.values() if value in message]


def test_an_empty_variable_is_missing() -> None:
    with pytest.raises(MissingSettings, match="DATADESK_R2_ACCESS_KEY_ID"):
        load_settings({**ENVIRON, "DATADESK_R2_ACCESS_KEY_ID": ""})
