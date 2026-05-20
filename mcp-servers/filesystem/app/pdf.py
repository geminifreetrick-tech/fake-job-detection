"""Render a detection-report PDF using ReportLab. Pure-Python, no extra system deps."""
from __future__ import annotations

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _fmt_pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def build_report(report: dict) -> bytes:
    """Render a fake-job detection report.

    Expected keys:
      - user_email (str)
      - prediction: {label, score, model_version}
      - text_excerpt (str)
      - explanations: list[{feature, label, value, contribution, direction}]
      - features: dict[str, float]
      - ocr (optional)
      - source_type
    """
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    body_style = styles["BodyText"]
    h2 = ParagraphStyle(
        "h2",
        parent=styles["Heading2"],
        spaceAfter=6,
    )
    small = ParagraphStyle("small", parent=body_style, fontSize=8, textColor=colors.grey)

    pred = report.get("prediction", {})
    label = (pred.get("label") or "unknown").upper()
    score = float(pred.get("score") or 0.0)
    model_version = pred.get("model_version", "n/a")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    story: list = []

    story.append(Paragraph("Fake-Job Detection Report", title_style))
    story.append(
        Paragraph(
            f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            f" &nbsp;&nbsp; Model: {model_version}",
            small,
        )
    )
    story.append(Spacer(1, 0.25 * inch))

    # Verdict box
    color = colors.HexColor("#b91c1c") if label == "FRAUD" else colors.HexColor("#15803d")
    verdict = Table(
        [[Paragraph(f"<b>Verdict:</b> {label}", body_style),
          Paragraph(f"<b>Fraud probability:</b> {_fmt_pct(score)}", body_style)]],
        colWidths=[3 * inch, 3 * inch],
    )
    verdict.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, color),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(verdict)
    story.append(Spacer(1, 0.2 * inch))

    # User
    user = report.get("user_email", "")
    if user:
        story.append(Paragraph(f"<b>Requested by:</b> {user}", body_style))
    src = report.get("source_type", "text")
    story.append(Paragraph(f"<b>Source type:</b> {src}", body_style))
    ocr = report.get("ocr")
    if ocr:
        story.append(
            Paragraph(
                f"<b>OCR:</b> pages={ocr.get('pages')}, used_ocr={ocr.get('used_ocr')}",
                body_style,
            )
        )
    story.append(Spacer(1, 0.2 * inch))

    # Top explanations
    story.append(Paragraph("Top contributing features", h2))
    rows = [["Feature", "Value", "Direction", "Contribution"]]
    for e in (report.get("explanations") or [])[:8]:
        rows.append(
            [
                Paragraph(str(e.get("label", e.get("feature", ""))), body_style),
                f"{float(e.get('value', 0.0)):.3f}",
                str(e.get("direction", "")),
                f"{float(e.get('contribution', 0.0)):+.3f}",
            ]
        )
    table = Table(rows, colWidths=[3.0 * inch, 0.9 * inch, 0.9 * inch, 1.2 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.25 * inch))

    # Excerpt
    excerpt = (report.get("text_excerpt") or "")[:1800]
    if excerpt:
        story.append(Paragraph("Job posting excerpt", h2))
        # ReportLab paragraphs interpret HTML; escape angle brackets defensively.
        safe = excerpt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(safe, body_style))
        story.append(Spacer(1, 0.2 * inch))

    story.append(
        Paragraph(
            "This report is generated automatically and is intended as a decision aid, "
            "not a definitive determination. Always verify suspicious postings independently.",
            small,
        )
    )
    doc.build(story)
    return buf.getvalue()
