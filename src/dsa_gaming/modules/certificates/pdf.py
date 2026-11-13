from pathlib import Path
import io

from fpdf import FPDF

_FONTS = (
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    Path("/Library/Fonts/Arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)


def pdf_filename(name: str, language_name: str) -> str:
    raw = f"{name}-{language_name}-certificate"
    safe = "".join(ch if ch.isalnum() else "-" for ch in raw)
    while "--" in safe:
        safe = safe.replace("--", "-")
    return (safe.strip("-") or "certificate") + ".pdf"


def _use_font(pdf: FPDF) -> str:
    for path in _FONTS:
        if path.is_file():
            pdf.add_font("Body", "", str(path))
            return "Body"
    return "Helvetica"


def _text(value: str, unicode_font: bool) -> str:
    if unicode_font:
        return value
    return value.encode("latin-1", "replace").decode("latin-1")


def build_certificate_pdf(
    name: str,
    language_name: str,
    issued_on: str,
    public_id: str = "",
    signature: bytes | None = None,
    signer_name: str = "",
) -> bytes:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(0, 0, 297, 210, "F")
    pdf.set_fill_color(29, 78, 216)
    pdf.rect(0, 0, 297, 210, "F")
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(8, 8, 281, 194, "F")
    pdf.set_draw_color(245, 196, 81)
    pdf.set_line_width(0.8)
    pdf.rect(12, 12, 273, 186)
    font = _use_font(pdf)
    unicode_font = font == "Body"
    pdf.set_font(font, size=11)
    pdf.set_text_color(29, 78, 216)
    pdf.set_xy(0, 28)
    pdf.cell(297, 6, "DSA GAMING ENGINE", align="C")
    pdf.set_font(font, size=28)
    pdf.set_xy(0, 40)
    pdf.cell(297, 12, "CERTIFICATE OF COMPLETION", align="C")
    pdf.set_font(font, size=13)
    pdf.set_text_color(90, 98, 112)
    pdf.set_xy(0, 62)
    pdf.cell(297, 8, "PROUDLY AWARDED TO", align="C")
    pdf.set_text_color(17, 24, 39)
    pdf.set_font(font, size=26)
    pdf.set_xy(40, 74)
    pdf.multi_cell(217, 12, _text(name, unicode_font), align="C")
    pdf.set_font(font, size=13)
    pdf.set_text_color(55, 65, 81)
    pdf.set_x(40)
    line = f"for successfully completing the DSA marathon in {language_name}"
    pdf.multi_cell(217, 8, _text(line, unicode_font), align="C")
    pdf.set_font(font, size=12)
    pdf.set_text_color(17, 24, 39)
    pdf.set_xy(28, 158)
    pdf.cell(120, 7, _text(f"Date: {issued_on}", unicode_font))
    if public_id:
        pdf.set_xy(28, 166)
        pdf.cell(120, 7, _text(f"Certificate ID: {public_id}", unicode_font))
    if signature:
        pdf.image(io.BytesIO(signature), x=198, y=142, h=16)
    pdf.set_xy(188, 160)
    pdf.set_font(font, size=12)
    pdf.cell(90, 6, _text(signer_name, unicode_font), align="C")
    pdf.set_xy(188, 167)
    pdf.set_font(font, size=10)
    pdf.set_text_color(90, 98, 112)
    pdf.cell(90, 6, "Founder & CEO", align="C")
    return bytes(pdf.output())
