from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.units import mm


def generate_report(
    output_path,
    title,
    similarity_index,
    total_chunks,
    matched_chunks,
    matched_sources
):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=12
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontSize=9,
        leading=13
    )

    score_style = ParagraphStyle(
        "Score",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=28,
        spaceAfter=20
    )

    elements = []

    # Header
    elements.append(
        Paragraph(
            "ANTI KOPAS",
            title_style
        )
    )

    elements.append(
        Paragraph(
            "SIMILARITY REPORT",
            heading_style
        )
    )

    # Similarity Index
    elements.append(
        Paragraph(
            f"{similarity_index * 100:.2f}%",
            score_style
        )
    )

    # Document Details
    elements.append(
        Paragraph(
            "DOCUMENT DETAILS",
            heading_style
        )
    )

    details = [
        ["Title", title],
        ["Blocks", f"{total_chunks} segments scanned"],
        ["Matched", f"{matched_chunks} segments"],
        ["Sources", f"{len(matched_sources)} matched"]
    ]

    details_table = Table(
        details,
        colWidths=[35 * mm, 125 * mm]
    )

    details_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    elements.append(details_table)

    # Matched Sources
    elements.append(
        Paragraph(
            "MATCHED SOURCES",
            heading_style
        )
    )

    if not matched_sources:
        elements.append(
            Paragraph(
                "Tidak ditemukan sumber yang melewati threshold.",
                normal_style
            )
        )

    for index, source in enumerate(
        matched_sources,
        start=1
    ):
        elements.append(
            Paragraph(
                f"<b>{index}. {source['title']}</b>",
                normal_style
            )
        )

        elements.append(
            Paragraph(
                f"Tahun: {source['year']}",
                normal_style
            )
        )

        elements.append(
            Paragraph(
                f"DOI: {source['doi']}",
                normal_style
            )
        )

        elements.append(
            Paragraph(
                f"Similarity: "
                f"{source['similarity_score'] * 100:.2f}%",
                normal_style
            )
        )

        elements.append(
            Spacer(1, 8)
        )

    doc.build(elements)