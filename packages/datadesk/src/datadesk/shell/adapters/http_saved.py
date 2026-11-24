from pathlib import Path

from datadesk.shell.ports import EffectError, HttpResponse

RESPONSES = "responses.tsv"
HEADER = "url\tfile"


class SavedFolderError(Exception):
    pass


class SavedHttp:
    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self.files = _read_responses(folder)

    def get(self, url: str) -> HttpResponse:
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
    except OSError as error:
        raise SavedFolderError(f"cannot read {RESPONSES} in {folder}: {error}") from error
    if not lines or lines[0] != HEADER:
        raise SavedFolderError(f"{RESPONSES} in {folder} does not start with the header url, file")
    files: dict[str, str] = {}
    for number, line in enumerate(lines[1:], 2):
        fields = line.split("\t")
        if len(fields) != 2 or not all(fields):
            raise SavedFolderError(f"{RESPONSES} line {number} is not a url and a file")
        url, name = fields
        if url in files:
            raise SavedFolderError(f"{RESPONSES} line {number} lists {url} again")
        if Path(name).name != name or not (folder / name).is_file():
            raise SavedFolderError(
                f"{RESPONSES} line {number} names {name}, not a file in {folder}"
            )
        files[url] = name
    return files
