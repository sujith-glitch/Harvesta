"""Branded, server-side report exports for authenticated farmers."""

from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    REPORTLAB_AVAILABLE = True
except ImportError:  # Local fallback keeps exports working before dependencies are installed.
    REPORTLAB_AVAILABLE = False


def _font_name() -> str:
    """Use a Unicode font when one is available on the host."""
    candidates = (
        Path("C:/Windows/Fonts/Nirmala.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    for candidate in candidates:
        if candidate.exists():
            try:
                pdfmetrics.registerFont(TTFont("HarvestaUnicode", str(candidate)))
                return "HarvestaUnicode"
            except Exception:
                continue
    return "Helvetica"


def _safe(value: Any) -> str:
    if value is None or value == "":
        return "Not available"
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def build_report_pdf(report: Dict[str, Any], farmer_name: str) -> bytes:
    """Render one Harvesta report dictionary into a downloadable PDF."""
    if not REPORTLAB_AVAILABLE:
        return _build_basic_pdf(report, farmer_name)
    buffer = BytesIO()
    font = _font_name()
    page_size = landscape(A4)
    document = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=18 * mm,
        bottomMargin=17 * mm,
        title=report["title"],
        author="Harvesta Smart Agriculture AI",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "HarvestaTitle",
        parent=styles["Title"],
        fontName=font,
        fontSize=22,
        leading=27,
        textColor=colors.HexColor("#1F2A24"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "HarvestaSubtitle",
        parent=styles["BodyText"],
        fontName=font,
        fontSize=9.5,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#637068"),
        spaceAfter=14,
    )
    cell_style = ParagraphStyle(
        "HarvestaCell",
        parent=styles["BodyText"],
        fontName=font,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#28312D"),
    )
    header_style = ParagraphStyle(
        "HarvestaHeader",
        parent=cell_style,
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    story: List[Any] = [
        Paragraph("HARVESTA  |  SMART AGRICULTURE AI", subtitle_style),
        Paragraph(report["title"], title_style),
        Paragraph(
            f"{report['description']}<br/>Farmer: {_safe(farmer_name)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Generated: {_safe(report['generated_at'])} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Records: {report['record_count']}",
            subtitle_style,
        ),
        Spacer(1, 3 * mm),
    ]

    columns: Iterable[Dict[str, str]] = report["columns"]
    rows: List[Dict[str, Any]] = report["rows"]
    table_data = [
        [Paragraph(column["label"], header_style) for column in columns]
    ]
    for row in rows:
        table_data.append([
            Paragraph(_safe(row.get(column["key"])), cell_style) for column in columns
        ])
    if not rows:
        table_data.append([
            Paragraph("No saved records are available for this report yet.", cell_style),
            *[Paragraph("", cell_style) for _ in list(columns)[1:]],
        ])

    usable_width = page_size[0] - (32 * mm)
    column_count = max(1, len(report["columns"]))
    report_table = Table(
        table_data,
        colWidths=[usable_width / column_count] * column_count,
        repeatRows=1,
        hAlign="LEFT",
    )
    report_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3F7F22")),
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#DDE5D8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F8F2")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(report_table)

    def page_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#DDE5D8"))
        canvas.line(16 * mm, 12 * mm, page_size[0] - 16 * mm, 12 * mm)
        canvas.setFont(font, 7.5)
        canvas.setFillColor(colors.HexColor("#6B756F"))
        canvas.drawString(16 * mm, 8 * mm, "Harvesta farmer report - private account data")
        canvas.drawRightString(page_size[0] - 16 * mm, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    return buffer.getvalue()


def _pdf_text(value: Any) -> str:
    """Escape text for the dependency-free PDF compatibility renderer."""
    text = _safe(value).encode("latin-1", "replace").decode("latin-1")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_basic_pdf(report: Dict[str, Any], farmer_name: str) -> bytes:
    """Generate a standards-compliant text PDF when ReportLab is unavailable."""
    columns = report["columns"]
    column_width = max(12, min(28, 116 // max(1, len(columns))))
    header = " | ".join(str(column["label"])[:column_width].ljust(column_width) for column in columns)
    rule = "-" * min(118, len(header))
    rows = []
    for row in report["rows"]:
        rows.append(" | ".join(_safe(row.get(column["key"]))[:column_width].ljust(column_width) for column in columns))
    if not rows:
        rows = ["No saved records are available for this report yet."]

    page_chunks = [rows[index:index + 34] for index in range(0, len(rows), 34)] or [[]]
    page_streams = []
    for page_number, chunk in enumerate(page_chunks, start=1):
        lines = [
            "HARVESTA  |  SMART AGRICULTURE AI",
            report["title"],
            report["description"],
            f"Farmer: {farmer_name}  |  Generated: {report['generated_at']}  |  Records: {report['record_count']}",
            "",
            header,
            rule,
            *chunk,
            "",
            f"Private farmer report  |  Page {page_number} of {len(page_chunks)}",
        ]
        operations = ["BT", "/F1 9 Tf", "40 555 Td", "12 TL"]
        for line in lines:
            operations.append(f"({_pdf_text(line)}) Tj")
            operations.append("T*")
        operations.append("ET")
        page_streams.append("\n".join(operations).encode("latin-1"))

    objects = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    page_object_numbers = [4 + index * 2 for index in range(len(page_streams))]
    kids = " ".join(f"{number} 0 R" for number in page_object_numbers)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_streams)} >>".encode("ascii"))
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for index, stream in enumerate(page_streams):
        stream_object_number = 5 + index * 2
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 3 0 R >> >> /Contents {stream_object_number} 0 R >>".encode("ascii")
        )
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream")

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_number} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)
