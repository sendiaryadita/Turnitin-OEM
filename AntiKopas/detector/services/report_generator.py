
"""
ANTI KOPAS
Professional Similarity Report Generator
STEP 4 - PDF Report Upgrade

Kompatibel dengan pemanggilan lama:

generate_report(
    output_path,
    title,
    similarity_index,
    total_chunks,
    matched_chunks,
    matched_sources,
)

Fitur tambahan opsional:

generate_report(
    ...,
    source_similarities=source_similarities,
    chunks=chunks,
)

Ketika data tambahan tidak dikirim,
PDF tetap dapat dibuat tanpa error.
"""

import re

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape, quoteattr

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_CENTER,
    TA_LEFT,
    TA_RIGHT,
)

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)

from reportlab.lib.units import mm

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from reportlab.graphics.shapes import (
    Drawing,
    Rect,
)

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
    CondPageBreak,
)


# ==========================================
# 1. WARNA DAN KONFIGURASI
# ==========================================

NAVY = colors.HexColor("#152B45")
BLUE = colors.HexColor("#2369A8")
TEAL = colors.HexColor("#16847F")

LIGHT_BLUE = colors.HexColor("#EDF4FA")
LIGHT_GRAY = colors.HexColor("#F3F6F9")

DARK_TEXT = colors.HexColor("#263445")
MUTED = colors.HexColor("#637487")

BORDER = colors.HexColor("#DCE4ED")
WHITE = colors.white

PAGE_WIDTH, PAGE_HEIGHT = A4

LEFT_MARGIN = 19 * mm
RIGHT_MARGIN = 19 * mm
TOP_MARGIN = 26 * mm
BOTTOM_MARGIN = 23 * mm

CONTENT_WIDTH = (
    PAGE_WIDTH
    - LEFT_MARGIN
    - RIGHT_MARGIN
)

MAX_EVIDENCE_PER_SOURCE = 2
MAX_EVIDENCE_CHARACTERS = 650


# ==========================================
# 2. FONT
# ==========================================

def setup_fonts():
    """
    Menggunakan font Unicode jika ada.

    Aman untuk Windows.
    Fallback menggunakan Helvetica.
    """

    candidates = [
        (
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
        ),
        (
            Path("C:/Windows/Fonts/calibri.ttf"),
            Path("C:/Windows/Fonts/calibrib.ttf"),
        ),
        (
            Path(
                "/usr/share/fonts/truetype/"
                "dejavu/DejaVuSans.ttf"
            ),
            Path(
                "/usr/share/fonts/truetype/"
                "dejavu/DejaVuSans-Bold.ttf"
            ),
        ),
    ]

    for regular_path, bold_path in candidates:

        if not (
            regular_path.is_file()
            and bold_path.is_file()
        ):
            continue

        try:
            if "AntiKopas-Regular" not in (
                pdfmetrics.getRegisteredFontNames()
            ):
                pdfmetrics.registerFont(
                    TTFont(
                        "AntiKopas-Regular",
                        str(regular_path),
                    )
                )

            if "AntiKopas-Bold" not in (
                pdfmetrics.getRegisteredFontNames()
            ):
                pdfmetrics.registerFont(
                    TTFont(
                        "AntiKopas-Bold",
                        str(bold_path),
                    )
                )

            pdfmetrics.registerFontFamily(
                "AntiKopas-Regular",
                normal="AntiKopas-Regular",
                bold="AntiKopas-Bold",
                italic="AntiKopas-Regular",
                boldItalic="AntiKopas-Bold",
            )

            return (
                "AntiKopas-Regular",
                "AntiKopas-Bold",
            )

        except Exception as error:
            print(
                "[Report] Font fallback:",
                str(error),
            )

    return "Helvetica", "Helvetica-Bold"


FONT_REGULAR, FONT_BOLD = setup_fonts()


# ==========================================
# 3. HELPER
# ==========================================

def safe_text(value, default="-"):
    """
    Membersihkan nilai sebelum digunakan
    pada ReportLab Paragraph.
    """

    if value is None:
        return default

    text = re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()

    return escape(text) if text else default


def readable_text(value, limit=None):
    """
    Menghasilkan teks biasa yang rapi.
    """

    text = re.sub(
        r"\s+",
        " ",
        str(value or ""),
    ).strip()

    if limit and len(text) > limit:
        return text[:limit].rstrip() + "..."

    return text


def safe_number(value, default=0.0):
    try:
        number = float(value)

        if not (
            float("-inf")
            < number
            < float("inf")
        ):
            return default

        return number

    except (TypeError, ValueError):
        return default


def percentage_value(value):
    """
    Mendukung:
    0.50 -> 50%
    50.0 -> 50%

    Generator lama menggunakan rasio 0-1.
    JSON API menggunakan persen 0-100.
    """

    number = safe_number(value)

    if 0 <= number <= 1:
        number *= 100

    return max(
        0.0,
        min(100.0, number),
    )


def format_percentage(value):
    return f"{value:.2f}%"


def valid_url(value):
    url = str(value or "").strip()

    if not url or len(url) > 2048:
        return ""

    parsed = urlparse(url)

    if (
        parsed.scheme.lower()
        not in ("http", "https")
    ):
        return ""

    if not parsed.netloc:
        return ""

    return url


def url_paragraph(value, style):
    """
    Membuat tautan DOI/URL aman
    untuk ReportLab Paragraph.
    """

    url = valid_url(value)

    if not url:
        return Paragraph(
            safe_text(value),
            style,
        )

    label = safe_text(url)

    markup = (
        f"<link href={quoteattr(url)}"
        f" color='#2369A8'>"
        f"{label}"
        "</link>"
    )

    return Paragraph(
        markup,
        style,
    )


def normalized_doi(value):
    doi = str(value or "").strip().lower()

    doi = re.sub(
        r"^(?:https?://(?:dx\.)?doi\.org/"
        r"|doi\s*:\s*)",
        "",
        doi,
    )

    return doi.rstrip(".,;)]}")


def source_identity(source):
    """
    Identitas untuk memasangkan
    sumber dengan informasi detail.
    """

    if not isinstance(source, dict):
        return ""

    doi = normalized_doi(
        source.get("doi")
    )

    if doi:
        return "doi:" + doi

    openalex_id = str(
        source.get("openalex_id")
        or source.get("source_id")
        or ""
    ).strip().lower()

    if openalex_id:
        return "id:" + openalex_id

    title = re.sub(
        r"\s+",
        " ",
        str(source.get("title") or ""),
    ).strip().casefold()

    return "title:" + title if title else ""


def matches_same_source(left, right):
    """
    Cocokkan DOI, ID OpenAlex,
    kemudian judul sumber.

    Tidak menyamakan sumber yang hanya
    memiliki topik serupa.
    """

    if not (
        isinstance(left, dict)
        and isinstance(right, dict)
    ):
        return False

    left_doi = normalized_doi(
        left.get("doi")
    )

    right_doi = normalized_doi(
        right.get("doi")
    )

    if left_doi and right_doi:
        return left_doi == right_doi

    left_id = str(
        left.get("openalex_id")
        or left.get("source_id")
        or ""
    ).strip().casefold()

    right_id = str(
        right.get("openalex_id")
        or right.get("source_id")
        or ""
    ).strip().casefold()

    if left_id and right_id:
        return left_id == right_id

    left_title = re.sub(
        r"\s+",
        " ",
        str(left.get("title") or ""),
    ).strip().casefold()

    right_title = re.sub(
        r"\s+",
        " ",
        str(right.get("title") or ""),
    ).strip().casefold()

    return bool(
        left_title
        and right_title
        and left_title == right_title
    )


def find_source_statistics(
    source,
    source_similarities,
):
    if not isinstance(
        source_similarities,
        (list, tuple),
    ):
        return None

    for item in source_similarities:

        if matches_same_source(
            source,
            item,
        ):
            return item

    return None


def collect_source_evidence(
    source,
    chunks,
):
    """
    Cari chunk dan kutipan abstrak
    berdasarkan sumber yang sama.

    Teks bukti berasal dari JSON asli,
    tidak dibuat ulang oleh generator.
    """

    if not isinstance(chunks, (list, tuple)):
        return []

    evidence = []

    for chunk in chunks:

        if not isinstance(chunk, dict):
            continue

        chunk_text = readable_text(
            chunk.get("chunk_text")
        )

        chunk_index = chunk.get(
            "chunk_index",
            "-",
        )

        for match in (
            chunk.get("matches") or []
        ):

            if not isinstance(match, dict):
                continue

            if not match.get(
                "matched",
                False,
            ):
                continue

            if not matches_same_source(
                source,
                match,
            ):
                continue

            excerpt = readable_text(
                match.get("source_excerpt")
            )

            # Jangan tampilkan bukti kosong
            # seolah-olah tersedia.
            if not chunk_text or not excerpt:
                continue

            evidence.append({
                "chunk_index": chunk_index,
                "document_text": chunk_text,
                "source_text": excerpt,
                "cross_score": match.get(
                    "cross_score"
                ),
            })

            break

        if len(evidence) >= MAX_EVIDENCE_PER_SOURCE:
            break

    return evidence


# ==========================================
# 4. STYLES
# ==========================================

def build_styles():
    base = getSampleStyleSheet()

    result = {}

    result["brand"] = ParagraphStyle(
        "AKBrand",
        parent=base["Title"],
        fontName=FONT_BOLD,
        fontSize=20,
        leading=25,
        alignment=TA_CENTER,
        textColor=NAVY,
        spaceAfter=4,
    )

    result["subtitle"] = ParagraphStyle(
        "AKSubtitle",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=10,
        leading=15,
        alignment=TA_CENTER,
        textColor=MUTED,
        spaceAfter=15,
    )

    result["heading"] = ParagraphStyle(
        "AKHeading",
        parent=base["Heading2"],
        fontName=FONT_BOLD,
        fontSize=11.5,
        leading=16,
        textColor=NAVY,
        spaceBefore=14,
        spaceAfter=8,
    )

    result["body"] = ParagraphStyle(
        "AKBody",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=14,
        textColor=DARK_TEXT,
        spaceAfter=5,
        splitLongWords=True,
    )

    result["small"] = ParagraphStyle(
        "AKSmall",
        parent=result["body"],
        fontSize=8,
        leading=12,
        textColor=MUTED,
        spaceAfter=3,
    )

    result["label"] = ParagraphStyle(
        "AKLabel",
        parent=result["body"],
        fontName=FONT_BOLD,
        fontSize=8.5,
        textColor=NAVY,
        spaceAfter=0,
    )

    result["score"] = ParagraphStyle(
        "AKScore",
        parent=base["Title"],
        fontName=FONT_BOLD,
        fontSize=31,
        leading=37,
        alignment=TA_CENTER,
        textColor=TEAL,
        spaceAfter=2,
    )

    result["score_label"] = ParagraphStyle(
        "AKScoreLabel",
        parent=result["small"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=14,
    )

    result["source_title"] = ParagraphStyle(
        "AKSourceTitle",
        parent=result["body"],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=15,
        textColor=NAVY,
        spaceAfter=7,
    )

    result["evidence"] = ParagraphStyle(
        "AKEvidence",
        parent=result["body"],
        fontSize=8.5,
        leading=13,
        spaceAfter=0,
    )

    result["note"] = ParagraphStyle(
        "AKNote",
        parent=result["body"],
        fontSize=8.3,
        leading=13,
        textColor=MUTED,
    )

    return result


# ==========================================
# 5. HEADER DAN FOOTER
# ==========================================

def draw_page_decoration(canvas, doc):
    canvas.saveState()

    # Garis bagian atas
    canvas.setFillColor(NAVY)

    canvas.rect(
        0,
        PAGE_HEIGHT - 9 * mm,
        PAGE_WIDTH,
        9 * mm,
        fill=1,
        stroke=0,
    )

    canvas.setFont(
        FONT_BOLD,
        8,
    )

    canvas.setFillColor(MUTED)

    canvas.drawString(
        LEFT_MARGIN,
        PAGE_HEIGHT - 17 * mm,
        "ANTI KOPAS",
    )

    canvas.setFont(
        FONT_REGULAR,
        7.5,
    )

    canvas.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        PAGE_HEIGHT - 17 * mm,
        "SIMILARITY ANALYSIS REPORT",
    )

    # Footer
    canvas.setStrokeColor(BORDER)

    canvas.line(
        LEFT_MARGIN,
        17 * mm,
        PAGE_WIDTH - RIGHT_MARGIN,
        17 * mm,
    )

    canvas.setFillColor(MUTED)

    canvas.setFont(
        FONT_REGULAR,
        7,
    )

    canvas.drawString(
        LEFT_MARGIN,
        12 * mm,
        "AntiKopas | Analisis Kemiripan Semantik",
    )

    canvas.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        12 * mm,
        f"Halaman {doc.page}",
    )

    canvas.restoreState()


# ==========================================
# 6. KOMPONEN PDF
# ==========================================

def section_heading(text, styles):
    return Paragraph(
        safe_text(text),
        styles["heading"],
    )


def make_progress_bar(percent):
    """
    Indikator visual persentase.
    """

    width = CONTENT_WIDTH
    height = 9 * mm

    drawing = Drawing(
        width,
        height,
    )

    drawing.add(
        Rect(
            0,
            0,
            width,
            height,
            rx=3,
            ry=3,
            strokeColor=None,
            fillColor=LIGHT_GRAY,
        )
    )

    fill_width = (
        width * percent / 100
    )

    if fill_width > 0:

        drawing.add(
            Rect(
                0,
                0,
                fill_width,
                height,
                rx=3,
                ry=3,
                strokeColor=None,
                fillColor=TEAL,
            )
        )

    return drawing


def make_detail_table(
    title,
    total_chunks,
    matched_chunks,
    source_count,
    styles,
):
    rows = [
        [
            Paragraph(
                "Judul Dokumen",
                styles["label"],
            ),
            Paragraph(
                safe_text(title),
                styles["body"],
            ),
        ],
        [
            Paragraph(
                "Total Segmen",
                styles["label"],
            ),
            Paragraph(
                f"{total_chunks} segmen dianalisis",
                styles["body"],
            ),
        ],
        [
            Paragraph(
                "Segmen Cocok",
                styles["label"],
            ),
            Paragraph(
                f"{matched_chunks} segmen",
                styles["body"],
            ),
        ],
        [
            Paragraph(
                "Sumber Terdeteksi",
                styles["label"],
            ),
            Paragraph(
                f"{source_count} sumber",
                styles["body"],
            ),
        ],
        [
            Paragraph(
                "Waktu Laporan",
                styles["label"],
            ),
            Paragraph(
                datetime.now().strftime(
                    "%d-%m-%Y %H:%M"
                ),
                styles["body"],
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            42 * mm,
            CONTENT_WIDTH - 42 * mm,
        ],
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                LIGHT_GRAY,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                10,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                10,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "LINEBELOW",
                (0, 0),
                (-1, -2),
                0.5,
                BORDER,
            ),
        ])
    )

    return table


def add_evidence(
    elements,
    evidence,
    styles,
):
    if not evidence:
        return

    elements.append(
        Spacer(1, 4 * mm)
    )

    elements.append(
        Paragraph(
            "<b>Bukti Kemiripan Teks</b>",
            styles["body"],
        )
    )

    for item in evidence:
        document_excerpt = readable_text(
            item["document_text"],
            MAX_EVIDENCE_CHARACTERS,
        )

        source_excerpt = readable_text(
            item["source_text"],
            MAX_EVIDENCE_CHARACTERS,
        )

        elements.append(
            CondPageBreak(50 * mm)
        )

        rows = [
            [
                Paragraph(
                    "<b>Segmen Dokumen "
                    f"{safe_text(item['chunk_index'])}"
                    "</b>",
                    styles["label"],
                )
            ],
            [
                Paragraph(
                    safe_text(document_excerpt),
                    styles["evidence"],
                )
            ],
            [
                Paragraph(
                    "<b>Potongan Abstrak Sumber</b>",
                    styles["label"],
                )
            ],
            [
                Paragraph(
                    safe_text(source_excerpt),
                    styles["evidence"],
                )
            ],
        ]

        table = Table(
            rows,
            colWidths=[CONTENT_WIDTH - 15 * mm],
            hAlign="LEFT",
        )

        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    LIGHT_BLUE,
                ),
                (
                    "BACKGROUND",
                    (0, 2),
                    (-1, 2),
                    LIGHT_BLUE,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ])
        )

        elements.append(table)
        elements.append(Spacer(1, 4 * mm))


# ==========================================
# 7. GENERATOR UTAMA
# ==========================================

def generate_report(
    output_path,
    title,
    similarity_index,
    total_chunks,
    matched_chunks,
    matched_sources,
    source_similarities=None,
    chunks=None,
):
    """
    Menerima enam parameter lama,
    ditambah dua parameter opsional.

    source_similarities:
        Daftar persentase per sumber.

    chunks:
        Daftar chunk dengan matches
        dan source_excerpt.

    Keduanya belum wajib dikirim
    oleh views.py.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    matched_sources = (
        matched_sources
        if isinstance(
            matched_sources,
            (list, tuple),
        )
        else []
    )

    styles = build_styles()

    score_percent = percentage_value(
        similarity_index
    )

    total_chunks = max(
        0,
        int(safe_number(total_chunks)),
    )

    matched_chunks = max(
        0,
        int(safe_number(matched_chunks)),
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=RIGHT_MARGIN,
        leftMargin=LEFT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="AntiKopas Similarity Report",
        author="AntiKopas",
        subject="Analisis kemiripan semantik dokumen",
    )

    elements = []

    # --------------------------------------
    # A. JUDUL LAPORAN
    # --------------------------------------

    elements.append(
        Spacer(1, 7 * mm)
    )

    elements.append(
        Paragraph(
            "ANTI KOPAS",
            styles["brand"],
        )
    )

    elements.append(
        Paragraph(
            "SIMILARITY ANALYSIS REPORT",
            styles["subtitle"],
        )
    )

    elements.append(
        HRFlowable(
            width="100%",
            thickness=1.2,
            color=BORDER,
            spaceAfter=13,
        )
    )

    # --------------------------------------
    # B. SIMILARITY INDEX
    # --------------------------------------

    elements.append(
        Paragraph(
            format_percentage(score_percent),
            styles["score"],
        )
    )

    elements.append(
        Paragraph(
            "Cakupan Segmen dengan Kemiripan Semantik",
            styles["score_label"],
        )
    )

    elements.append(
        Spacer(1, 4 * mm)
    )

    elements.append(
        make_progress_bar(score_percent)
    )

    elements.append(
        Spacer(1, 5 * mm)
    )

    elements.append(
        Paragraph(
            "Persentase ini menunjukkan bagian "
            "dokumen yang ditandai memiliki "
            "kemiripan semantik dengan sumber "
            "yang ditemukan sistem. "
            "Angka ini bukan bukti plagiarisme.",
            styles["note"],
        )
    )

    # --------------------------------------
    # C. DETAIL DOKUMEN
    # --------------------------------------

    elements.append(
        section_heading(
            "DETAIL DOKUMEN",
            styles,
        )
    )

    elements.append(
        make_detail_table(
            title=title,
            total_chunks=total_chunks,
            matched_chunks=matched_chunks,
            source_count=len(matched_sources),
            styles=styles,
        )
    )

    # --------------------------------------
    # D. HASIL SUMBER
    # --------------------------------------

    elements.append(
        section_heading(
            "SUMBER AKADEMIK TERDETEKSI",
            styles,
        )
    )

    if not matched_sources:
        elements.append(
            Paragraph(
                "Tidak ditemukan sumber yang "
                "melewati kriteria kecocokan "
                "yang diterapkan oleh sistem.",
                styles["body"],
            )
        )

    for index, source in enumerate(
        matched_sources,
        start=1,
    ):
        if not isinstance(source, dict):
            continue

        elements.append(
            CondPageBreak(45 * mm)
        )

        source_title = safe_text(
            source.get("title"),
            "Judul tidak tersedia",
        )

        source_year = safe_text(
            source.get("year"),
            "Tidak tersedia",
        )

        source_doi = (
            source.get("doi") or ""
        )

        cross_score = source.get(
            "cross_score"
        )

        stats = find_source_statistics(
            source,
            source_similarities,
        )

        heading = Paragraph(
            f"<b>{index}. {source_title}</b>",
            styles["source_title"],
        )

        metadata = Paragraph(
            f"<b>Tahun publikasi:</b> {source_year}",
            styles["body"],
        )

        elements.append(
            KeepTogether([
                heading,
                metadata,
            ])
        )

        if source_doi:
            elements.append(
                Paragraph(
                    "<b>DOI:</b>",
                    styles["label"],
                )
            )

            elements.append(
                url_paragraph(
                    source_doi,
                    styles["body"],
                )
            )

        elif source.get("url"):
            elements.append(
                Paragraph(
                    "<b>URL sumber:</b>",
                    styles["label"],
                )
            )

            elements.append(
                url_paragraph(
                    source.get("url"),
                    styles["body"],
                )
            )

        # Persentase hanya ditampilkan
        # jika datanya benar-benar tersedia.
        if isinstance(stats, dict):
            coverage = stats.get(
                "similarity_percentage"
            )

            if coverage is not None:
                coverage_value = safe_number(
                    coverage
                )

                elements.append(
                    Paragraph(
                        "<b>Cakupan per sumber:</b> "
                        f"{coverage_value:.2f}%",
                        styles["body"],
                    )
                )

            source_matched_chunks = (
                stats.get("matched_chunks")
            )

            if source_matched_chunks is not None:
                elements.append(
                    Paragraph(
                        "<b>Segmen cocok:</b> "
                        f"{safe_text(source_matched_chunks)}",
                        styles["body"],
                    )
                )

        if cross_score is not None:
            raw_score = safe_number(
                cross_score
            )

            elements.append(
                Paragraph(
                    "<b>Cross Encoder "
                    "Raw Score:</b> "
                    f"{raw_score:.3f}",
                    styles["body"],
                )
            )

        elements.append(
            Paragraph(
                "<i>Cross Encoder Raw Score "
                "adalah nilai model, "
                "bukan persentase kemiripan.</i>",
                styles["small"],
            )
        )

        evidence = collect_source_evidence(
            source,
            chunks,
        )

        if evidence:
            add_evidence(
                elements,
                evidence,
                styles,
            )

        elements.append(
            Spacer(1, 3 * mm)
        )

        elements.append(
            HRFlowable(
                width="100%",
                thickness=0.7,
                color=BORDER,
            )
        )

    # --------------------------------------
    # E. KETERSEDIAAN DATA TAMBAHAN
    # --------------------------------------

    if (
        matched_sources
        and (
            source_similarities is None
            or chunks is None
        )
    ):
        elements.append(
            Spacer(1, 5 * mm)
        )

        elements.append(
            Paragraph(
                "<b>Catatan detail:</b> "
                "Persentase per sumber dan "
                "bukti pasangan teks hanya "
                "ditampilkan jika data "
                "source_similarities dan chunks "
                "dikirim ke generator laporan.",
                styles["note"],
            )
        )

    # --------------------------------------
    # F. CATATAN INTERPRETASI
    # --------------------------------------

    elements.append(
        section_heading(
            "CATATAN INTERPRETASI",
            styles,
        )
    )

    notes = [
        (
            "Sistem menggunakan model "
            "kemiripan semantik untuk "
            "membandingkan segmen dokumen "
            "dengan abstrak sumber akademik."
        ),
        (
            "Kemiripan pembahasan tidak "
            "secara otomatis menunjukkan "
            "penyalinan atau pelanggaran "
            "integritas akademik."
        ),
        (
            "Hasil perlu diperiksa bersama "
            "teks sumber, konteks pembahasan, "
            "dan tanggal publikasi."
        ),
        (
            "Jumlah sumber yang ditampilkan "
            "bergantung pada hasil pencarian "
            "dan aturan seleksi sistem."
        ),
    ]

    for number, note in enumerate(
        notes,
        start=1,
    ):
        elements.append(
            Paragraph(
                f"{number}. {safe_text(note)}",
                styles["note"],
            )
        )

    # --------------------------------------
    # G. BUILD PDF
    # --------------------------------------

    doc.build(
        elements,
        onFirstPage=draw_page_decoration,
        onLaterPages=draw_page_decoration,
    )

    print(
        "[AntiKopas Report] PDF dibuat:",
        output_path,
    )

    print(
        "[AntiKopas Report] Similarity:",
        format_percentage(score_percent),
    )

    print(
        "[AntiKopas Report] Sumber:",
        len(matched_sources),
    )

    return str(output_path)
