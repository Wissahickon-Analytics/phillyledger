from collections.abc import Mapping
from io import BytesIO

from PIL import Image

FONTS = {
    "/F1": "3 0 R",
    "/F2": "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
}


def drawn_pdf(*contents: str, entries: Mapping[int, str] | None = None) -> bytes:
    kids = " ".join(f"{4 + 2 * number} 0 R" for number in range(len(contents)))
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {len(contents)} >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for number, text in enumerate(contents):
        content = text.encode()
        entry = (entries or {}).get(number + 1)
        fonts = " ".join(f"{name} {font}" for name, font in FONTS.items() if f"{name} " in text)
        objects += [
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"{'' if entry is None else f'{entry} '}"
                f"/Resources << /Font << {fonts} >> >> /Contents {5 + 2 * number} 0 R >>"
            ).encode(),
            b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content),
        ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf += b"%d 0 obj\n%s\nendobj\n" % (number, body)
    xref = len(pdf)
    pdf += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    pdf += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    pdf += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return bytes(pdf)


def text_pdf(*pages: str, entries: Mapping[int, str] | None = None) -> bytes:
    return drawn_pdf(
        *(f"BT /F1 12 Tf 72 720 Td ({words}) Tj ET" for words in pages), entries=entries
    )


def image_pdf() -> bytes:
    page = BytesIO()
    Image.new("RGB", (612, 792), "white").save(page, "PDF")
    return page.getvalue()


STYLED = "BT /F2 12 Tf 72 720 Td (Total) Tj ET BT /F1 9 Tf 200 720 Td (1,234) Tj ET"

RULES = " ".join(
    (
        "100 400 m 300 400 l S",
        "100 300 m 100 350 l S",
        "72 700 400 0.72 re f",
        "72 600 400 0.72 re f",
        "72 600 0.72 100.72 re f",
        "471 600 1.44 100.72 re f",
    )
)

NOT_RULES = "100 100 m 200 200 l S 72 500 400 4 re f 72 450 2 5 re f"

SIDEWAYS = "BT /F1 12 Tf 0 1 -1 0 300 72 Tm (TABLE P-1) Tj ET 400 100 200 1.44 re f"
