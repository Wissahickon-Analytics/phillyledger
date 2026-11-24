from io import BytesIO

from PIL import Image


def text_pdf(*pages: str) -> bytes:
    kids = " ".join(f"{4 + 2 * number} 0 R" for number in range(len(pages)))
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for number, words in enumerate(pages):
        content = f"BT /F1 12 Tf 72 720 Td ({words}) Tj ET".encode()
        objects += [
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {5 + 2 * number} 0 R >>"
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


def image_pdf() -> bytes:
    page = BytesIO()
    Image.new("RGB", (612, 792), "white").save(page, "PDF")
    return page.getvalue()
