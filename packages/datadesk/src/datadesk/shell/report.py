"""What the shell draws for a person to look at, starting with the row crops of step 4.

Design section 12.3 gives this module the printing of findings, plans and gates. Step 4 puts
the crop check here first (step 4 plan, shape 13): the crop file, which holds what fresh
readers typed from images alone, the one rule that finds the line a typed label names, and the
images that `datadesk crops` writes.
"""

from collections.abc import Sequence
from dataclasses import dataclass, fields
from enum import StrEnum
from io import BytesIO
from math import ceil, floor
from re import compile

from PIL import Image, ImageDraw, ImageFont

from checkedtables.lines import Line, group_lines
from checkedtables.refs import Sha256
from checkedtables.words import Page

ROW_PAD = 1.0

_PAGE = compile(r"[1-9][0-9]*")
_CAPTION_SIZE = 28
_CAPTION_MARGIN = 6


class RowEnd(StrEnum):
    """Which department row of a page a crop shows, the first or the last."""

    FIRST = "first"
    LAST = "last"


@dataclass(frozen=True, slots=True)
class CropRow:
    """One row of a crop file, such as ``docs/evidence/crops/qcmr_positions.tsv``.

    A row names one department row of one printed page. An empty string is a field that no
    reader has typed yet. Each reading comes from a fresh reader who sees images alone (step 4
    plan, answer 2 and risk 5).

    Attributes
    ----------
    edition : str
        The edition id as the index prints it, such as ``qcmr:2022-09-30:none``.
    sha256 : Sha256
        The indexed sha of the file that holds the page.
    page : int
        The 1-based page number in that file.
    row : RowEnd
        The first or the last row on the page that names a department and is not a total.
    page_label : str
        The row's label, typed from the image of the whole page before any crop existed. It
        picks the line that the crop shows, so the extracted words never choose the row.
    crop_label : str
        The row's label, typed from the crop alone.
    values : str
        The values typed from the crop, left to right, joined by single spaces.
    read_by : str
        Who typed the crop's reading.
    """

    edition: str
    sha256: Sha256
    page: int
    row: RowEnd
    page_label: str
    crop_label: str
    values: str
    read_by: str


_HEADER = "\t".join(field.name for field in fields(CropRow))


@dataclass(frozen=True, slots=True)
class NoLine:
    """No line of the page begins with the words of `label`."""

    label: str


@dataclass(frozen=True, slots=True)
class TwoLines:
    """Two or more lines of the page begin with the words of `label`, so no one is the row.

    A department's own row and a row under it can begin with the same words (step 4 plan, risk
    6). The caller reports `lines`, top to bottom, and never picks one.
    """

    label: str
    lines: tuple[Line, ...]


def read_crop_rows(text: str) -> tuple[CropRow, ...]:
    """Read a crop file: a header line, then one `CropRow` on each line, tab separated.

    The header names the fields of `CropRow` in order, and every line, the last included, ends
    in a newline.

    Raises
    ------
    ValueError
        Naming the line, for another header, a last line with no newline, a row with another
        number of fields, a sha that is not 64 lowercase hex characters, a page that is not a
        positive integer in ASCII digits, and a row end other than ``first`` or ``last``.
    """
    if not text.endswith("\n"):
        raise ValueError(f"line {text.count('\n') + 1} has no newline after it")
    header, *lines = text[:-1].split("\n")
    if header != _HEADER:
        raise ValueError(f"line 1 is {header!r}, not the header {_HEADER!r}")
    return tuple(_crop_row(number, line) for number, line in enumerate(lines, 2))


def row_line(page: Page, label: str) -> Line | NoLine | TwoLines:
    """Find the one line of `page` that begins with the words of `label`.

    The lines are those of the kit's `group_lines`. A line begins with the label when its first
    words, left to right, have the texts that splitting `label` on whitespace gives, exactly. A
    label of no words begins no line.
    """
    wanted = label.split()
    found = tuple(
        line
        for line in group_lines(page)
        if wanted and [word.text for word in line.words[: len(wanted)]] == wanted
    )
    match found:
        case ():
            return NoLine(label)
        case (line,):
            return line
        case _:
            return TwoLines(label, found)


def row_band(page_png: bytes, line: Line, dpi: int) -> bytes:
    """Cut the band that holds `line` out of a page image, across the whole width of the page.

    `page_png` is the page as `PdfReader.render` draws it at `dpi`, in the frame of the words,
    so a point is `dpi` / 72 pixels. The band runs from `ROW_PAD` points above the line's box
    to `ROW_PAD` points below it, out to whole pixels and inside the image. `ROW_PAD` is one
    point. A P-1 row is set in 7.44 point type, and on the 20 grid pages most lines stand 2.16
    points apart from box to box, so the pad keeps ink that reaches just past the box and stops
    more than a point short of the next line's box.

    Returns
    -------
    bytes
        The band as a PNG.
    """
    scale = dpi / 72
    image = Image.open(BytesIO(page_png))
    top = max(0, floor((line.box.top - ROW_PAD) * scale))
    bottom = min(image.height, ceil((line.box.bottom + ROW_PAD) * scale))
    return _png(image.crop((0, top, image.width, bottom)))


def contact_sheet(crops: Sequence[tuple[CropRow, bytes]]) -> bytes:
    """Stack row crops top to bottom, each followed by one printed line of its reading.

    The line gives the row's edition, page and end, then the crop label and values typed for
    it, so a person checks each reading against the crop above it. The sheet is as wide as the
    widest crop, on white. Since it prints the readings, it is drawn only after both readings
    (step 4 plan, risk 5).

    Returns
    -------
    bytes
        The sheet as a PNG.
    """
    font = ImageFont.load_default(size=_CAPTION_SIZE)
    texts = [
        f"{row.edition} page {row.page} {row.row}: {row.crop_label} | {row.values}"
        for row, _ in crops
    ]
    caption = ceil(max(font.getbbox(text)[3] for text in texts)) + 2 * _CAPTION_MARGIN
    images = [Image.open(BytesIO(png)) for _, png in crops]
    width = max(image.width for image in images)
    sheet = Image.new("RGB", (width, sum(image.height + caption for image in images)), "white")
    draw = ImageDraw.Draw(sheet)
    top = 0
    for text, image in zip(texts, images, strict=True):
        sheet.paste(image, (0, top))
        top += image.height
        draw.text((_CAPTION_MARGIN, top + _CAPTION_MARGIN), text, fill="black", font=font)
        top += caption
    return _png(sheet)


def _crop_row(number: int, line: str) -> CropRow:
    """Read line `number` of a crop file, the header being line 1."""
    values = line.split("\t")
    if len(values) != len(fields(CropRow)):
        raise ValueError(f"line {number} has {len(values)} fields, not {len(fields(CropRow))}")
    edition, sha, page, end, page_label, crop_label, typed, read_by = values
    if _PAGE.fullmatch(page) is None:
        raise ValueError(f"line {number}: the page {page!r} is not a positive integer")
    try:
        return CropRow(
            edition, Sha256(sha), int(page), RowEnd(end), page_label, crop_label, typed, read_by
        )
    except ValueError as error:
        raise ValueError(f"line {number}: {error}") from None


def _png(image: Image.Image) -> bytes:
    data = BytesIO()
    image.save(data, format="PNG")
    return data.getvalue()
