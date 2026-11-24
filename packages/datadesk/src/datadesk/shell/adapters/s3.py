from dataclasses import dataclass
from os import devnull
from typing import Any

from boto3.session import Session
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from botocore.session import Session as BotocoreSession

from datadesk.shell.ports import Condition, CreateOnly, EffectError, IfMatch, PreconditionFailed
from datadesk.shell.settings import Settings

# botocore reads AWS_PROFILE and the shared config and credentials files even when a client is
# given its keys, and a profile that the config file lacks raises ProfileNotFound.
NO_AMBIENT_PROFILE = {
    "profile": (None, None, None, None),
    "config_file": (None, None, devnull, None),
    "credentials_file": (None, None, devnull, None),
}
CLIENT_CONFIG = Config(
    region_name="auto",
    s3={"addressing_style": "path"},
    retries={"mode": "standard", "total_max_attempts": 1},
)


@dataclass(frozen=True, slots=True)
class S3Store:
    client: Any
    bucket: str

    def put(self, key: str, data: bytes, condition: Condition) -> str:
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
        try:
            return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        except ClientError as error:
            if error.response["Error"]["Code"] == "NoSuchKey":
                raise KeyError(key) from error
            raise EffectError(f"get {key}: {error}") from error
        except BotoCoreError as error:
            raise EffectError(f"get {key}: {error}") from error


def s3_store(settings: Settings) -> S3Store:
    session = Session(botocore_session=BotocoreSession(session_vars=NO_AMBIENT_PROFILE))
    client = session.client(
        "s3",
        endpoint_url=settings.endpoint_url,
        aws_access_key_id=settings.access_key_id,
        aws_secret_access_key=settings.secret_access_key,
        config=CLIENT_CONFIG,
    )
    return S3Store(client, settings.archive_bucket)
