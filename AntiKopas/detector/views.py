import os
from datetime import datetime

from django.http import FileResponse
from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.antikopas_service import analyze_antikopas
from .services.document_parser import extract_text
from .services.report_generator import generate_report


@api_view(["GET"])
def health_check(request):
    return Response({
        "status": "ok",
        "message": "AntiKopas backend is running"
    })


@api_view(["POST"])
def detect_similarity(request):

    title = request.data.get("title")
    uploaded_file = request.FILES.get("file")

    # =========================
    # VALIDASI TITLE
    # =========================

    if not title:
        return Response({
            "status": "error",
            "message": "title wajib dikirim"
        }, status=400)

    # =========================
    # VALIDASI FILE
    # =========================

    if not uploaded_file:
        return Response({
            "status": "error",
            "message": "file wajib dikirim"
        }, status=400)

    # =========================
    # EXTRACT TEXT
    # =========================

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

    if not text or not text.strip():
        return Response({
            "status": "error",
            "message": (
                "Isi dokumen tidak dapat dibaca"
            )
        }, status=400)

    # =========================
    # AI ANALYSIS
    # =========================

    try:
        analysis = analyze_antikopas(
            text,
            title
        )

    except Exception as e:
        return Response({
            "status": "error",
            "message": (
                f"Gagal melakukan analisis AI: {str(e)}"
            )
        }, status=500)

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

    # =========================
    # COLLECT MATCHED SOURCES
    # =========================

    matched_sources = []

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

            existing_keys = [
                source.get("doi")
                or source.get("url")
                or source.get("title")
                for source in matched_sources
            ]

            if source_key not in existing_keys:
                matched_sources.append(
                    source_data
                )

    # =========================
    # CREATE REPORT DIRECTORY
    # =========================

    report_directory = os.path.join(
        settings.BASE_DIR,
        "reports"
    )

    os.makedirs(
        report_directory,
        exist_ok=True
    )

    # =========================
    # REPORT FILENAME
    # =========================

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    report_filename = (
        f"antikopas_report_{timestamp}.pdf"
    )

    report_path = os.path.join(
        report_directory,
        report_filename
    )

    # =========================
    # GENERATE PDF
    # =========================

    try:

        generate_report(
            output_path=report_path,
            title=title,

            # similarity_index dari sistem
            # berada pada skala 0-100
            similarity_index=(
                similarity_index / 100
            ),

            total_chunks=total_chunks,
            matched_chunks=matched_chunks,
            matched_sources=matched_sources
        )

    except Exception as e:
        return Response({
            "status": "error",
            "message": (
                f"Gagal membuat report PDF: {str(e)}"
            )
        }, status=500)

    # =========================
    # REPORT URL
    # =========================

    report_url = request.build_absolute_uri(
        f"/api/reports/{report_filename}/"
    )

    # =========================
    # RESPONSE
    # =========================

    return Response({

        "status": "success",

        "title": title,

        "filename": uploaded_file.name,

        "similarity_index": similarity_index,

        "total_chunks": total_chunks,

        "matched_chunks": matched_chunks,

        "matched_sources": matched_sources,

        "chunks": document_results,

        "report_filename": report_filename,

        "report_url": report_url
    })


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

    report_path = os.path.join(
        report_directory,
        safe_filename
    )

    if not os.path.exists(report_path):
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