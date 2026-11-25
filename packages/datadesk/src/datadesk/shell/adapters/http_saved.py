"""An `Http` adapter that answers from a folder of responses that a browser saved."""

import re
from pathlib import Path

from datadesk.shell.ports import EffectError, HttpResponse

RESPONSES = "responses.tsv"
HEADER = "url\tfile"
URL = re.compile(r"https?://\S+")


class SavedFolderError(Exception):
    """A saved folder that `SavedHttp` refuses. The message names the file or line and why."""


class SavedHttp:
    """Answer GET requests from the files of a saved folder.

    The folder holds the saved files and `responses.tsv`, whose first row is the header
    `url<TAB>file` and whose other rows each pair a URL with a file name. A listed URL answers 200
    with its file's bytes, and any other URL answers 404.

    Building one reads `responses.tsv` and raises SavedFolderError for a file it cannot read or
    that is not UTF-8, another header, a row that is not one URL and one file name, a URL that
    does not start with https:// or http:// or that holds whitespace, a URL listed twice, and a
    name that is not a file directly in the folder or that is a symbolic link.
    """

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self.files = _read_responses(folder)

    def get(self, url: str) -> HttpResponse:
        """Return 200 and the file's bytes for a listed URL, and 404 for any other.

        Raises
        ------
        EffectError
            When the listed file cannot be read.
        """
        name = self.files.get(url)
        if name is None:
            return HttpResponse(404, b"")
        try:
            return HttpResponse(200, (self.folder / name).read_bytes())
        except OSError as error:
            raise EffectError(f"cannot read {name} for {url}: {error}") from error


def _read_responses(folder: Path) -> dict[str, str]:
    try:
        lines = (folder / RESPONSES).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise SavedFolderError(f"cannot read {RESPONSES} in {folder}: {error}") from error
    if not lines or lines[0] != HEADER:
        raise SavedFolderError(f"{RESPONSES} in {folder} does not start with the header url, file")
    files: dict[str, str] = {}
    for number, line in enumerate(lines[1:], 2):
        fields = line.split("\t")
        if len(fields) != 2 or not all(fields):
            raise SavedFolderError(f"{RESPONSES} line {number} is not a url and a file")
        url, name = fields
        if not URL.fullmatch(url):
            raise SavedFolderError(f"{RESPONSES} line {number} lists {url!r}, not a URL")
        if url in files:
            raise SavedFolderError(f"{RESPONSES} line {number} lists {url} again")
        path = folder / name
        if Path(name).name != name or path.is_symlink() or not path.is_file():
            raise SavedFolderError(
                f"{RESPONSES} line {number} names {name}, not a file in {folder}"
            )
        files[url] = name
    return files
