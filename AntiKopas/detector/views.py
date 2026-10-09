
import os
from datetime import datetime

from django.http import FileResponse
from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.antikopas_service import analyze_antikopas
from .services.document_parser import extract_text
from .services.report_generator import generate_report


# ==========================================
# 1. HEALTH CHECK
# ==========================================

@api_view(["GET"])
def health_check(request):
    return Response({
        "status": "ok",
        "message": "AntiKopas backend is running"
    })


# ==========================================
# 2. DETECT SIMILARITY
# ==========================================

@api_view(["POST"])
def detect_similarity(request):

    # --------------------------------------
    # A. AMBIL INPUT
    # --------------------------------------

    title = request.data.get("title")
    uploaded_file = request.FILES.get("file")

    # --------------------------------------
    # B. VALIDASI TITLE
    # --------------------------------------

    if not title or not str(title).strip():
        return Response({
            "status": "error",
            "message": "title wajib dikirim"
        }, status=400)

    title = str(title).strip()

    # --------------------------------------
    # C. VALIDASI FILE
    # --------------------------------------

    if not uploaded_file:
        return Response({
            "status": "error",
            "message": "file wajib dikirim"
        }, status=400)

    # --------------------------------------
    # D. EKSTRAKSI DOKUMEN
    # --------------------------------------

    try:
        text = extract_text(uploaded_file)

    except ValueError as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=400)

    except Exception as e:
        return Response({
            "status": "error",
            "message": (
                f"Gagal membaca file: {str(e)}"
            )
        }, status=400)

    if not text or not str(text).strip():
        return Response({
            "status": "error",
            "message": "Isi dokumen tidak dapat dibaca"
        }, status=400)

    # --------------------------------------
    # E. ANALISIS AI
    # --------------------------------------

    try:
        analysis = analyze_antikopas(
            text,
            title
        )

    except Exception as e:
        return Response({
            "status": "error",
            "message": (
                "Gagal melakukan analisis AI: "
                f"{str(e)}"
            )
        }, status=500)

    # --------------------------------------
    # F. AMBIL HASIL ANALISIS
    # --------------------------------------

    similarity_index = analysis[
        "similarity_index"
    ]

    total_chunks = analysis[
        "total_chunks"
    ]

    matched_chunks = analysis[
        "matched_chunks"
    ]

    document_results = analysis[
        "chunks"
    ]

    total_similarity = analysis.get(
        "total_similarity",
        similarity_index
    )

    source_similarities = analysis.get(
        "source_similarities",
        []
    )

    # --------------------------------------
    # G. KUMPULKAN JURNAL YANG COCOK
    # --------------------------------------

    matched_sources = []
    seen_source_keys = set()

    for chunk in document_results:

        matches = chunk.get(
            "matches",
            []
        )

        for match in matches:

            if not match.get("matched"):
                continue

            source_data = {
                "title": match.get("title"),
                "year": match.get("year"),
                "doi": match.get("doi"),
                "url": match.get("url"),
                "minilm_score": match.get(
                    "minilm_score"
                ),
                "cross_score": match.get(
                    "cross_score"
                ),
                "similarity_score": match.get(
                    "cross_score"
                )
            }

            source_key = (
                source_data["doi"]
                or source_data["url"]
                or source_data["title"]
            )

            if not source_key:
                continue

            source_key = str(
                source_key
            ).strip().casefold()

            if source_key in seen_source_keys:
                continue

            seen_source_keys.add(
                source_key
            )

            matched_sources.append(
                source_data
            )

    # --------------------------------------
    # H. DIREKTORI REPORT
    # --------------------------------------

    report_directory = os.path.join(
        settings.BASE_DIR,
        "reports"
    )

    os.makedirs(
        report_directory,
        exist_ok=True
    )

    # --------------------------------------
    # I. NAMA FILE REPORT
    # --------------------------------------

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    report_filename = (
        f"antikopas_report_{timestamp}.pdf"
    )

    report_path = os.path.join(
        report_directory,
        report_filename
    )

    # --------------------------------------
    # J. GENERATE PDF REPORT LENGKAP
    # --------------------------------------

    try:
        generate_report(

            output_path=report_path,

            title=title,

            # Fungsi report menerima rasio 0-1.
            # Nilai dari API berada pada skala
            # persentase 0-100.
            similarity_index=(
                float(similarity_index) / 100.0
            ),

            total_chunks=total_chunks,

            matched_chunks=matched_chunks,

            matched_sources=matched_sources,

            # =================================
            # FITUR BARU STEP 4B
            # =================================

            # Persentase dan jumlah chunk
            # yang cocok untuk setiap jurnal.
            source_similarities=source_similarities,

            # Teks dokumen, matched source,
            # dan source_excerpt yang menjadi
            # bukti perbandingan.
            chunks=document_results,

        )

        print(
            "[AntiKopas] PDF report berhasil:",
            report_filename
        )

        print(
            "[AntiKopas] Sumber:",
            len(matched_sources)
        )

        print(
            "[AntiKopas] Data bukti:",
            len(document_results),
            "chunk"
        )

    except Exception as e:
        return Response({
            "status": "error",
            "message": (
                "Gagal membuat report PDF: "
                f"{str(e)}"
            )
        }, status=500)

    # --------------------------------------
    # K. REPORT URL
    # --------------------------------------

    report_url = request.build_absolute_uri(
        f"/api/reports/{report_filename}/"
    )

    # --------------------------------------
    # L. RESPONSE POSTMAN
    # --------------------------------------

    return Response({

        "status": "success",

        "title": title,

        "filename": uploaded_file.name,

        "similarity_index": similarity_index,

        "total_similarity": total_similarity,

        "total_chunks": total_chunks,

        "matched_chunks": matched_chunks,

        "matched_sources": matched_sources,

        "source_similarities": source_similarities,

        "chunks": document_results,

        "report_filename": report_filename,

        "report_url": report_url

    })


# ==========================================
# 3. DOWNLOAD PDF REPORT
# ==========================================

@api_view(["GET"])
def download_report(
    request,
    filename
):

    report_directory = os.path.join(
        settings.BASE_DIR,
        "reports"
    )

    safe_filename = os.path.basename(
        filename
    )

    # Hanya izinkan file PDF yang
    # dibuat oleh sistem AntiKopas.
    if (
        not safe_filename.startswith(
            "antikopas_report_"
        )
        or not safe_filename.endswith(
            ".pdf"
        )
    ):
        return Response({
            "status": "error",
            "message": "Nama report tidak valid"
        }, status=400)

    report_path = os.path.join(
        report_directory,
        safe_filename
    )

    if not os.path.isfile(
        report_path
    ):
        return Response({
            "status": "error",
            "message": "Report tidak ditemukan"
        }, status=404)

    return FileResponse(
        open(report_path, "rb"),
        as_attachment=True,
        filename=safe_filename,
        content_type="application/pdf"
    )
