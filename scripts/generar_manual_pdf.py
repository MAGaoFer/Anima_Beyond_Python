from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parent.parent
MANUAL_MD = ROOT / "docs" / "Manual_Usuario.md"
MANUAL_PDF = ROOT / "docs" / "Manual_Usuario.pdf"


def markdown_line_to_story(line, styles):
    clean = line.strip()
    if not clean:
        return [Spacer(1, 0.2 * cm)]

    if clean.startswith("# "):
        return [Paragraph(clean[2:], styles["h1"]), Spacer(1, 0.25 * cm)]

    if clean.startswith("## "):
        return [Paragraph(clean[3:], styles["h2"]), Spacer(1, 0.18 * cm)]

    if clean.startswith("### "):
        return [Paragraph(clean[4:], styles["h3"]), Spacer(1, 0.12 * cm)]

    if clean.startswith("---"):
        return [Spacer(1, 0.16 * cm)]

    if clean.startswith("- "):
        bullet_text = "• " + clean[2:]
        return [Paragraph(bullet_text, styles["body"])]

    if clean.startswith("```"):
        return []

    return [Paragraph(clean, styles["body"])]


def build_styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "ManualH1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1F2A44"),
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "ManualH2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#2E3F63"),
            spaceBefore=6,
            spaceAfter=5,
        ),
        "h3": ParagraphStyle(
            "ManualH3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#3B4E7A"),
            spaceBefore=4,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "ManualBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=4,
        ),
    }


def generate_manual_pdf():
    if not MANUAL_MD.exists():
        raise FileNotFoundError(f"No existe el manual fuente: {MANUAL_MD}")

    styles = build_styles()
    story = []
    lines = MANUAL_MD.read_text(encoding="utf-8").splitlines()

    for line in lines:
        story.extend(markdown_line_to_story(line, styles))

    doc = SimpleDocTemplate(
        str(MANUAL_PDF),
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        title="Manual de Usuario - Ánima: Beyond Fantasy",
        author="Proyecto Anima_Beyond_Python",
    )
    doc.build(story)
    print(f"PDF generado: {MANUAL_PDF}")


if __name__ == "__main__":
    generate_manual_pdf()
