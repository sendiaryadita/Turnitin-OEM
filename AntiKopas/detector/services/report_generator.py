
"""
ANTIKOPAS
PDF Similarity Report Generator
Cloudflare BGE-M3 + Academic CrossEncoder V2

Kompatibel dengan views.py:

generate_report(
    output_path,
    title,
    similarity_index,
    total_chunks,
    matched_chunks,
    matched_sources,
    source_similarities=None,
    chunks=None,
)

Catatan:
- Similarity Index = cakupan chunk cocok.
- Bukan persentase plagiarisme.
- Skor embedding dan CrossEncoder bukan persentase.
- Bukti berasal dari hasil pipeline, bukan teks buatan.
"""

import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape, quoteattr

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    CondPageBreak,
    KeepTogether,
)


# ==================================================
# 1. KONFIGURASI
# ==================================================

NAVY = colors.HexColor("#152B45")
BLUE = colors.HexColor("#2369A8")
TEAL = colors.HexColor("#16847F")

LIGHT_BLUE = colors.HexColor("#EDF4FA")
LIGHT_GRAY = colors.HexColor("#F3F6F9")

DARK_TEXT = colors.HexColor("#263445")
MUTED = colors.HexColor("#637487")
BORDER = colors.HexColor("#DCE4ED")

PAGE_WIDTH, PAGE_HEIGHT = A4

LEFT_MARGIN = 19 * mm
RIGHT_MARGIN = 19 * mm
TOP_MARGIN = 26 * mm
BOTTOM_MARGIN = 23 * mm

CONTENT_WIDTH = (
    PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
)

MAX_EVIDENCE_PER_SOURCE = 2
MAX_EVIDENCE_CHARACTERS = 650


# ==================================================
# 2. FONT
# ==================================================

def setup_fonts():
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

    for regular, bold in candidates:
        if not regular.is_file() or not bold.is_file():
            continue

        try:
            if "AntiKopas-Regular" not in (
                pdfmetrics.getRegisteredFontNames()
            ):
                pdfmetrics.registerFont(
                    TTFont(
                        "AntiKopas-Regular",
                        str(regular),
                    )
                )

            if "AntiKopas-Bold" not in (
                pdfmetrics.getRegisteredFontNames()
            ):
                pdfmetrics.registerFont(
                    TTFont(
                        "AntiKopas-Bold",
                        str(bold),
                    )
                )

            pdfmetrics.registerFontFamily(
                "AntiKopas-Regular",
                normal="AntiKopas-Regular",
                bold="AntiKopas-Bold",
                italic="AntiKopas-Regular",
                boldItalic="AntiKopas-Bold",
            )

            return "AntiKopas-Regular", "AntiKopas-Bold"

        except Exception as error:
            print("[Report] Font fallback:", error)

    return "Helvetica", "Helvetica-Bold"


FONT_REGULAR, FONT_BOLD = setup_fonts()


# ==================================================
# 3. HELPER
# ==================================================

def readable_text(value, limit=None):
    text = re.sub(
        r"\s+",
        " ",
        str(value or ""),
    ).strip()

    if limit and len(text) > limit:
        return text[:limit].rstrip() + "..."

    return text


def safe_text(value, default="-"):
    text = readable_text(value)
    return escape(text) if text else default


def safe_number(value, default=0.0):
    try:
        result = float(value)

        if not (
            float("-inf") < result < float("inf")
        ):
            return default

        return result

    except (TypeError, ValueError):
        return default


def percentage_value(value):
    """
    Mendukung pemanggilan lama:
    0.50 -> 50.00

    Dan nilai API:
    50.0 -> 50.00
    """
    number = safe_number(value)

    if 0 <= number <= 1:
        number *= 100

    return max(0.0, min(100.0, number))


def valid_url(value):
    url = str(value or "").strip()

    if not url or len(url) > 2048:
        return ""

    parsed = urlparse(url)

    if parsed.scheme.lower() not in (
        "http",
        "https",
    ):
        return ""

    return url if parsed.netloc else ""


def url_paragraph(value, style):
    url = valid_url(value)

    if not url:
        return Paragraph(
            safe_text(value),
            style,
        )

    markup = (
        f"<link href={quoteattr(url)} "
        f"color='#2369A8'>"
        f"{safe_text(url)}"
        "</link>"
    )

    return Paragraph(markup, style)


def normalized_doi(value):
    doi = str(value or "").strip().casefold()

    doi = re.sub(
        r"^(?:https?://(?:dx\.)?doi\.org/"
        r"|doi\s*:\s*)",
        "",
        doi,
    )

    return doi.rstrip(".,;)]}")


def matches_same_source(left, right):
    if not (
        isinstance(left, dict)
        and isinstance(right, dict)
    ):
        return False

    left_doi = normalized_doi(left.get("doi"))
    right_doi = normalized_doi(right.get("doi"))

    if left_doi and right_doi:
        return left_doi == right_doi

    left_id = readable_text(
        left.get("openalex_id")
        or left.get("source_id")
    ).casefold()

    right_id = readable_text(
        right.get("openalex_id")
        or right.get("source_id")
    ).casefold()

    if left_id and right_id:
        return left_id == right_id

    left_title = readable_text(
        left.get("title")
    ).casefold()

    right_title = readable_text(
        right.get("title")
    ).casefold()

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
        if matches_same_source(source, item):
            return item

    return None


def embedding_model_name(match):
    """
    Identifikasi model berdasarkan metadata hasil
    scanning, bukan asumsi dari nama field lama.
    """

    if not isinstance(match, dict):
        return "Embedding model tidak diketahui"

    model = readable_text(
        match.get("embedding_model")
    ).casefold()

    if "bge-m3" in model:
        return "Cloudflare BGE-M3"

    if "minilm" in model:
        return "MiniLM"

    if model:
        return readable_text(
            match.get("embedding_model")
        )

    # Jika tidak ada metadata, jangan menamai
    # skor lama sebagai BGE-M3 secara otomatis.
    return "Embedding model tidak diketahui"


def embedding_score_value(match):
    if not isinstance(match, dict):
        return None

    score = match.get("embedding_score")

    if score is None:
        score = match.get("minilm_score")

    if score is None:
        return None

    return safe_number(score)


def collect_source_evidence(source, chunks):
    """
    Ambil bukti asli dari output pipeline.

    Maksimal dua contoh per sumber.
    Mengutamakan skor CrossEncoder tinggi.
    """

    if not isinstance(chunks, (list, tuple)):
        return []

    evidence = []

    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue

        document_text = readable_text(
            chunk.get("chunk_text")
        )

        chunk_index = chunk.get(
            "chunk_index",
            "-",
        )

        if not document_text:
            continue

        for match in chunk.get("matches") or []:
            if not isinstance(match, dict):
                continue

            if not match.get("matched", False):
                continue

            if not matches_same_source(
                source,
                match,
            ):
                continue

            source_text = readable_text(
                match.get("source_excerpt")
            )

            if not source_text:
                continue

            evidence.append({
                "chunk_index": chunk_index,
                "document_text": document_text,
                "source_text": source_text,
                "embedding_model": (
                    embedding_model_name(match)
                ),
                "embedding_score": (
                    embedding_score_value(match)
                ),
                "cross_score": (
                    match.get("cross_score")
                ),
                "text_scope": (
                    match.get("text_scope")
                    or match.get("source_text_scope")
                ),
            })

            break

    evidence.sort(
        key=lambda item: safe_number(
            item.get("cross_score"),
            default=float("-inf"),
        ),
        reverse=True,
    )

    return evidence[:MAX_EVIDENCE_PER_SOURCE]


def detect_pipeline_model(chunks):
    """
    Nama model yang diketahui dari hasil scanning.
    """

    if not isinstance(chunks, (list, tuple)):
        return "Tidak tersedia"

    models = set()

    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue

        for match in chunk.get("matches") or []:
            if not isinstance(match, dict):
                continue

            if not match.get("matched", False):
                continue

            models.add(
                embedding_model_name(match)
            )

    models.discard(
        "Embedding model tidak diketahui"
    )

    if not models:
        return "Tidak tercatat dalam hasil"

    return ", ".join(sorted(models))


# ==================================================
# 4. STYLE
# ==================================================

def build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["brand"] = ParagraphStyle(
        "AKBrand",
        parent=base["Title"],
        fontName=FONT_BOLD,
        fontSize=20,
        leading=25,
        alignment=TA_CENTER,
        textColor=NAVY,
        spaceAfter=4,
    )

    styles["subtitle"] = ParagraphStyle(
        "AKSubtitle",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=10,
        leading=15,
        alignment=TA_CENTER,
        textColor=MUTED,
        spaceAfter=14,
    )

    styles["heading"] = ParagraphStyle(
        "AKHeading",
        parent=base["Heading2"],
        fontName=FONT_BOLD,
        fontSize=11.5,
        leading=16,
        textColor=NAVY,
        spaceBefore=14,
        spaceAfter=8,
    )

    styles["body"] = ParagraphStyle(
        "AKBody",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=14,
        textColor=DARK_TEXT,
        spaceAfter=5,
        splitLongWords=True,
    )

    styles["small"] = ParagraphStyle(
        "AKSmall",
        parent=styles["body"],
        fontSize=8,
        leading=12,
        textColor=MUTED,
        spaceAfter=3,
    )

    styles["label"] = ParagraphStyle(
        "AKLabel",
        parent=styles["body"],
        fontName=FONT_BOLD,
        fontSize=8.5,
        textColor=NAVY,
        spaceAfter=0,
    )

    styles["score"] = ParagraphStyle(
        "AKScore",
        parent=base["Title"],
        fontName=FONT_BOLD,
        fontSize=31,
        leading=37,
        alignment=TA_CENTER,
        textColor=TEAL,
        spaceAfter=2,
    )

    styles["score_label"] = ParagraphStyle(
        "AKScoreLabel",
        parent=styles["small"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=14,
    )

    styles["source_title"] = ParagraphStyle(
        "AKSourceTitle",
        parent=styles["body"],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=15,
        textColor=NAVY,
        spaceAfter=7,
    )

    styles["evidence"] = ParagraphStyle(
        "AKEvidence",
        parent=styles["body"],
        fontSize=8.5,
        leading=13,
        spaceAfter=0,
    )

    styles["note"] = ParagraphStyle(
        "AKNote",
        parent=styles["body"],
        fontSize=8.3,
        leading=13,
        textColor=MUTED,
    )

    return styles


# ==================================================
# 5. HEADER / FOOTER
# ==================================================

def draw_page_decoration(canvas, doc):
    canvas.saveState()

    canvas.setFillColor(NAVY)

    canvas.rect(
        0,
        PAGE_HEIGHT - 9 * mm,
        PAGE_WIDTH,
        9 * mm,
        fill=1,
        stroke=0,
    )

    canvas.setFillColor(MUTED)

    canvas.setFont(FONT_BOLD, 8)
    canvas.drawString(
        LEFT_MARGIN,
        PAGE_HEIGHT - 17 * mm,
        "ANTI KOPAS",
    )

    canvas.setFont(FONT_REGULAR, 7.5)
    canvas.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        PAGE_HEIGHT - 17 * mm,
        "SEMANTIC SIMILARITY REPORT",
    )

    canvas.setStrokeColor(BORDER)

    canvas.line(
        LEFT_MARGIN,
        17 * mm,
        PAGE_WIDTH - RIGHT_MARGIN,
        17 * mm,
    )

    canvas.setFont(FONT_REGULAR, 7)
    canvas.setFillColor(MUTED)

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


# ==================================================
# 6. KOMPONEN
# ==================================================

def section_heading(text, styles):
    return Paragraph(
        safe_text(text),
        styles["heading"],
    )


def make_progress_bar(percent):
    width = CONTENT_WIDTH
    height = 9 * mm

    drawing = Drawing(width, height)

    drawing.add(
        Rect(
            0,
            0,
            width,
            height,
            rx=3,
            ry=3,
            fillColor=LIGHT_GRAY,
            strokeColor=None,
        )
    )

    fill_width = width * percent / 100

    if fill_width > 0:
        drawing.add(
            Rect(
                0,
                0,
                fill_width,
                height,
                rx=3,
                ry=3,
                fillColor=TEAL,
                strokeColor=None,
            )
        )

    return drawing


def make_detail_table(
    title,
    total_chunks,
    matched_chunks,
    source_count,
    model_name,
    styles,
):
    data = [
        ("Judul Dokumen", title),
        ("Total Segmen", str(total_chunks)),
        ("Segmen Cocok", str(matched_chunks)),
        ("Sumber Terdeteksi", str(source_count)),
        ("Model Embedding", model_name),
        (
            "Model Validasi",
            "Academic CrossEncoder V2",
        ),
        (
            "Waktu Laporan",
            datetime.now().strftime(
                "%d-%m-%Y %H:%M"
            ),
        ),
    ]

    rows = []

    for label, value in data:
        rows.append([
            Paragraph(
                safe_text(label),
                styles["label"],
            ),
            Paragraph(
                safe_text(value),
                styles["body"],
            ),
        ])

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


def make_evidence_table(item, styles):
    doc_excerpt = readable_text(
        item.get("document_text"),
        MAX_EVIDENCE_CHARACTERS,
    )

    source_excerpt = readable_text(
        item.get("source_text"),
        MAX_EVIDENCE_CHARACTERS,
    )

    chunk_index = safe_text(
        item.get("chunk_index")
    )

    rows = [
        [
            Paragraph(
                f"<b>Segmen Dokumen {chunk_index}</b>",
                styles["label"],
            )
        ],
        [
            Paragraph(
                safe_text(doc_excerpt),
                styles["evidence"],
            )
        ],
        [
            Paragraph(
                "<b>Cuplikan Teks Sumber</b>",
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
        colWidths=[
            CONTENT_WIDTH - 15 * mm
        ],
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

    return table


def add_evidence(elements, evidence, styles):
    if not evidence:
        return

    elements.append(Spacer(1, 4 * mm))

    elements.append(
        Paragraph(
            "<b>BUKTI KEMIRIPAN TEKS</b>",
            styles["body"],
        )
    )

    for item in evidence:
        elements.append(
            CondPageBreak(55 * mm)
        )

        elements.append(
            make_evidence_table(item, styles)
        )

        model_name = item.get(
            "embedding_model",
            "Embedding model tidak diketahui",
        )

        embedding_score = item.get(
            "embedding_score"
        )

        cross_score = item.get(
            "cross_score"
        )

        score_parts = []

        if embedding_score is not None:
            score_parts.append(
                f"{safe_text(model_name)}: "
                f"{safe_number(embedding_score):.4f}"
            )

        if cross_score is not None:
            score_parts.append(
                "Academic V2 (raw score): "
                f"{safe_number(cross_score):.4f}"
            )

        if score_parts:
            elements.append(
                Spacer(1, 2 * mm)
            )

            elements.append(
                Paragraph(
                    " | ".join(score_parts),
                    styles["small"],
                )
            )

        elements.append(
            Spacer(1, 4 * mm)
        )


# ==================================================
# 7. GENERATE REPORT
# ==================================================

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
    Fungsi kompatibel dengan views.py lama.
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

    valid_sources = [
        source
        for source in matched_sources
        if isinstance(source, dict)
    ]

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

    model_name = detect_pipeline_model(
        chunks
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=RIGHT_MARGIN,
        leftMargin=LEFT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="AntiKopas Semantic Similarity Report",
        author="AntiKopas",
        subject="Analisis Kemiripan Semantik Dokumen",
    )

    elements = []

    # --------------------------------------
    # A. JUDUL
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
            "SEMANTIC SIMILARITY REPORT",
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
            f"{score_percent:.2f}%",
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
            "Similarity Index menunjukkan "
            "proporsi segmen dokumen yang "
            "memiliki kecocokan semantik "
            "dengan sumber akademik yang "
            "lolos seleksi sistem. "
            "Angka ini bukan persentase "
            "plagiarisme atau bukti penyalinan.",
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
            source_count=len(valid_sources),
            model_name=model_name,
            styles=styles,
        )
    )

    # --------------------------------------
    # D. SUMBER AKADEMIK
    # --------------------------------------

    elements.append(
        section_heading(
            "SUMBER AKADEMIK TERDETEKSI",
            styles,
        )
    )

    if not valid_sources:
        elements.append(
            Paragraph(
                "Tidak ditemukan sumber akademik "
                "yang melewati seluruh kriteria "
                "kecocokan sistem.",
                styles["body"],
            )
        )

    for index, source in enumerate(
        valid_sources,
        start=1,
    ):
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

        source_doi = source.get("doi") or ""

        elements.append(
            KeepTogether([
                Paragraph(
                    f"<b>{index}. {source_title}</b>",
                    styles["source_title"],
                ),
                Paragraph(
                    "<b>Tahun publikasi:</b> "
                    f"{source_year}",
                    styles["body"],
                ),
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

        stats = find_source_statistics(
            source,
            source_similarities,
        )

        if isinstance(stats, dict):
            coverage = stats.get(
                "similarity_percentage"
            )

            if coverage is not None:
                elements.append(
                    Paragraph(
                        "<b>Cakupan per sumber:</b> "
                        f"{safe_number(coverage):.2f}%",
                        styles["body"],
                    )
                )

            count = stats.get(
                "matched_chunks"
            )

            if count is not None:
                elements.append(
                    Paragraph(
                        "<b>Segmen cocok:</b> "
                        f"{safe_text(count)}",
                        styles["body"],
                    )
                )

            indices = stats.get(
                "matched_chunk_indices"
            )

            if isinstance(
                indices,
                (list, tuple),
            ) and indices:
                elements.append(
                    Paragraph(
                        "<b>Indeks segmen:</b> "
                        + safe_text(
                            ", ".join(
                                str(i)
                                for i in indices
                            )
                        ),
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
    # E. CATATAN METODOLOGI
    # --------------------------------------

    elements.append(
        section_heading(
            "METODOLOGI DAN INTERPRETASI",
            styles,
        )
    )

    notes = [
        (
            "AntiKopas mencari sumber akademik "
            "melalui OpenAlex, kemudian "
            "membandingkan segmen dokumen "
            "dengan teks sumber yang tersedia."
        ),
        (
            "Cloudflare BGE-M3 digunakan "
            "untuk pencarian kandidat "
            "kemiripan semantik pada "
            "konfigurasi pemindaian saat ini."
        ),
        (
            "Academic CrossEncoder V2 "
            "digunakan untuk memvalidasi "
            "pasangan kandidat."
        ),
        (
            "Skor BGE-M3 merupakan nilai "
            "cosine similarity. Skor Academic "
            "V2 merupakan raw score model. "
            "Keduanya bukan persentase plagiarisme."
        ),
        (
            "Cakupan per sumber dapat saling "
            "tumpang tindih. Persentase antar "
            "sumber tidak boleh dijumlahkan "
            "untuk menghasilkan Similarity Index."
        ),
        (
            "Bukti sumber dapat berasal "
            "dari abstrak maupun teks lengkap "
            "yang berhasil diakses sistem. "
            "Ketersediaan teks setiap sumber "
            "bisa berbeda."
        ),
        (
            "Kemiripan makna tidak otomatis "
            "menunjukkan penyalinan atau "
            "pelanggaran integritas akademik. "
            "Hasil perlu ditinjau manusia "
            "dengan mempertimbangkan konteks "
            "dan sitasi."
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
    # F. CATATAN KETERSEDIAAN BUKTI
    # --------------------------------------

    if (
        valid_sources
        and (
            source_similarities is None
            or chunks is None
        )
    ):
        elements.append(
            Spacer(1, 4 * mm)
        )

        elements.append(
            Paragraph(
                "<b>Catatan:</b> Persentase "
                "per sumber dan bukti pasangan "
                "teks hanya dapat ditampilkan "
                "jika data detail diberikan "
                "kepada generator laporan.",
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
        "[AntiKopas Report] Semantic Coverage:",
        f"{score_percent:.2f}%",
    )

    print(
        "[AntiKopas Report] Sumber:",
        len(valid_sources),
    )

    print(
        "[AntiKopas Report] Embedding:",
        model_name,
    )

    return str(output_path)
