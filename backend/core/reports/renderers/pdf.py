"""
PDF-рендерер на reportlab.

Кириллический шрифт DejaVuSans.ttf ожидается в core/reports/renderers/fonts/.
Если файла нет — делается fallback на встроенный Helvetica (без кириллицы).
См. README в той же папке.
"""

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from core.reports.base import ReportData, ReportSection
from core.reports.renderers.formatters import format_cell

FONTS_DIR = Path(__file__).parent / "fonts"
PRIMARY_FONT_PATH = FONTS_DIR / "DejaVuSans.ttf"

_FONT_NAME = "Helvetica"
_FONT_REGISTERED = False


def _ensure_font() -> str:
    """
    Регистрирует DejaVuSans (если файл есть) и возвращает имя шрифта,
    которое нужно использовать в стилях.
    """
    global _FONT_NAME, _FONT_REGISTERED
    if _FONT_REGISTERED:
        return _FONT_NAME
    _FONT_REGISTERED = True
    if PRIMARY_FONT_PATH.is_file():
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", str(PRIMARY_FONT_PATH)))
            _FONT_NAME = "DejaVuSans"
        except Exception:
            _FONT_NAME = "Helvetica"
    return _FONT_NAME


def render_pdf(report: ReportData) -> bytes:
    font_name = _ensure_font()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=report.title,
    )

    base_styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=base_styles["Heading1"],
        fontName=font_name,
        fontSize=18,
        leading=22,
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        name="ReportMeta",
        parent=base_styles["Normal"],
        fontName=font_name,
        fontSize=9,
        textColor=colors.HexColor("#5C5555"),
        leading=12,
    )
    section_title_style = ParagraphStyle(
        name="ReportSectionTitle",
        parent=base_styles["Heading2"],
        fontName=font_name,
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=6,
    )
    note_style = ParagraphStyle(
        name="ReportNote",
        parent=base_styles["Italic"],
        fontName=font_name,
        fontSize=9,
        textColor=colors.HexColor("#7E7E7E"),
        leading=12,
        spaceAfter=6,
    )

    story = [Paragraph(_escape(report.title), title_style)]

    meta_lines = [report.period_label]
    if report.shop_label:
        meta_lines.append(report.shop_label)
    meta_lines.append(f"Сформировано: {report.generated_at.strftime('%d.%m.%Y %H:%M')}")
    for line in meta_lines:
        story.append(Paragraph(_escape(line), meta_style))
    story.append(Spacer(1, 6))

    for index, section in enumerate(report.sections):
        if index > 0:
            story.append(PageBreak())
        story.append(Paragraph(_escape(section.title), section_title_style))
        if section.note:
            story.append(Paragraph(_escape(section.note), note_style))
        if section.columns:
            story.append(_section_table(section, font_name))

    doc.build(story)
    return buffer.getvalue()


def _section_table(section: ReportSection, font_name: str) -> Table:
    columns = section.columns
    header = [c.title for c in columns]

    body: list[list] = []
    for row in section.rows:
        body.append([format_cell(row.get(c.key), is_money=c.is_money) for c in columns])

    if section.totals:
        body.append([format_cell(section.totals.get(c.key, ""), is_money=c.is_money) for c in columns])

    data = [header] + body if body else [header, ["—"] * len(columns)]
    table = Table(data, repeatRows=1, hAlign="LEFT")

    style_cmds: list[tuple] = [
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F7F7F9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#303030")),
        ("FONTNAME", (0, 0), (-1, 0), font_name),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#7E7E7E")),
        ("GRID", (0, 1), (-1, -1), 0.25, colors.HexColor("#E6E2E0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]

    for col_idx, col in enumerate(columns):
        align = {"left": "LEFT", "right": "RIGHT", "center": "CENTER"}.get(col.align, "LEFT")
        style_cmds.append(("ALIGN", (col_idx, 1), (col_idx, -1), align))
        style_cmds.append(("ALIGN", (col_idx, 0), (col_idx, 0), align))

    if section.totals and body:
        style_cmds.append(("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F7F7F9")))
        style_cmds.append(("LINEABOVE", (0, -1), (-1, -1), 0.6, colors.HexColor("#7E7E7E")))

    table.setStyle(TableStyle(style_cmds))
    return table


def _escape(value: str) -> str:
    return (
        (value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
