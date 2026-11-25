"""An `ObjectStore` adapter for an S3 bucket, such as the archive bucket on R2."""

from dataclasses import dataclass
from os import devnull
from typing import Any

from boto3.session import Session
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from botocore.session import Session as BotocoreSession

from datadesk.shell.ports import Condition, CreateOnly, EffectError, IfMatch, PreconditionFailed
from datadesk.shell.settings import Settings

# botocore reads each session variable from its AWS_* environment variable even when a client is
# given its keys, and a profile that the config file lacks raises ProfileNotFound.
QUIET_SESSION_VARIABLES = {
    name: (config, None, default, convert)
    for name, (config, _, default, convert) in BotocoreSession.SESSION_VARIABLES.items()
} | {
    "config_file": (None, None, devnull, None),
    "credentials_file": (None, None, devnull, None),
}
CLIENT_CONFIG = Config(
    region_name="auto",
    s3={
        "addressing_style": "path",
        "us_east_1_regional_endpoint": "legacy",
        "use_arn_region": True,
        "s3_disable_multiregion_access_points": False,
    },
    retries={"mode": "standard", "total_max_attempts": 1},
)


@dataclass(frozen=True, slots=True)
class S3Store:
    """One bucket of an S3 service.

    `client` is a boto3 S3 client whose own retries are off, so the executor's tries are the
    only ones.
    """

    client: Any
    bucket: str

    def put(self, key: str, data: bytes, condition: Condition) -> str:
        """Write `data` under `key` when `condition` holds, and return the new ETag.

        CreateOnly and IfMatch(None) send If-None-Match: *, and IfMatch(etag) sends If-Match. A
        refused precondition raises PreconditionFailed with the key. Any other client or botocore
        error raises EffectError.
        """
        match condition:
            case CreateOnly() | IfMatch(None):
                precondition = {"IfNoneMatch": "*"}
            case IfMatch(etag):
                precondition = {"IfMatch": etag}
        try:
            response = self.client.put_object(
                Bucket=self.bucket, Key=key, Body=data, **precondition
            )
        except ClientError as error:
            if error.response["Error"]["Code"] == "PreconditionFailed":
                raise PreconditionFailed(key) from error
            raise EffectError(f"put {key}: {error}") from error
        except BotoCoreError as error:
            raise EffectError(f"put {key}: {error}") from error
        return response["ETag"]

    def head(self, key: str) -> str | None:
        """Return the ETag under `key`, or None on a 404. Any other error raises EffectError."""
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as error:
            if error.response["ResponseMetadata"]["HTTPStatusCode"] == 404:
                return None
            raise EffectError(f"head {key}: {error}") from error
        except BotoCoreError as error:
            raise EffectError(f"head {key}: {error}") from error
        return response["ETag"]

    def get(self, key: str) -> bytes:
        """Return the bytes under `key`. NoSuchKey raises KeyError, any other error EffectError."""
        try:
            return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        except ClientError as error:
            if error.response["Error"]["Code"] == "NoSuchKey":
                raise KeyError(key) from error
            raise EffectError(f"get {key}: {error}") from error
        except BotoCoreError as error:
            raise EffectError(f"get {key}: {error}") from error


def s3_store(settings: Settings) -> S3Store:
    """Build the store for the archive bucket from `settings` alone.

    The botocore session maps none of its session variables, AWS_PROFILE among them, to the
    environment, and reads `os.devnull` as its config and credentials files, so `settings` alone
    gives the endpoint, the keys and the bucket. botocore still reads some variables that are
    not session variables. `CLIENT_CONFIG` sets the three S3 settings that it reads from AWS_S3_*
    variables, which overrides them, and design section 4 names others it reads, such as
    AWS_EXECUTION_ENV and the proxy variables.
    """
    session = Session(botocore_session=BotocoreSession(session_vars=QUIET_SESSION_VARIABLES))
    client = session.client(
        "s3",
        endpoint_url=settings.endpoint_url,
        aws_access_key_id=settings.access_key_id,
        aws_secret_access_key=settings.secret_access_key,
        config=CLIENT_CONFIG,
    )
    return S3Store(client, settings.archive_bucket)
