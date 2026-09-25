import os
from datetime import datetime

from django.http import FileResponse
from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.openalex import search_literature
from .services.similarity import (
    compare_multiple_sources,
    calculate_similarity_index,
    rank_sources
)
from .services.chunking import split_into_chunks
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

    if not title:
        return Response({
            "status": "error",
            "message": "title wajib dikirim"
        }, status=400)

    if not uploaded_file:
        return Response({
            "status": "error",
            "message": "file wajib dikirim"
        }, status=400)

    # Ekstrak teks PDF/DOCX
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
            "message": f"Gagal membaca file: {str(e)}"
        }, status=400)

    if not text or not text.strip():
        return Response({
            "status": "error",
            "message": "Isi dokumen tidak dapat dibaca"
        }, status=400)

    # Cari literatur menggunakan judul
    sources = search_literature(
        title,
        per_page=20
    )

    # Chunking
    chunks = split_into_chunks(
        text,
        max_words=100
    )

    # Similarity
    results = compare_multiple_sources(
        chunks,
        sources,
        threshold=0.7
    )

    # Ranking maksimal 20 jurnal
    ranked_sources = rank_sources(
        chunks,
        sources,
        max_results=20
    )

    similarity_index = calculate_similarity_index(
        results
    )

    matched_chunks = sum(
        1
        for result in results
        if result["best_match"]
        and result["best_match"]["is_match"]
    )

    # Kumpulkan matched sources
    matched_sources = []

    for result in results:
        match = result["best_match"]

        if match and match["is_match"]:
            source_data = {
                "title": match["title"],
                "year": match["year"],
                "doi": match["doi"],
                "url": match["url"],
                "similarity_score": match["similarity_score"]
            }

            source_key = (
                source_data["doi"]
                or source_data["url"]
                or source_data["title"]
            )

            existing_keys = [
                source["doi"]
                or source["url"]
                or source["title"]
                for source in matched_sources
            ]

            if source_key not in existing_keys:
                matched_sources.append(source_data)

    # Folder report
    report_directory = os.path.join(
        settings.BASE_DIR,
        "reports"
    )

    os.makedirs(
        report_directory,
        exist_ok=True
    )

    # Nama report unik
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

    # Generate PDF
    generate_report(
        output_path=report_path,
        title=title,
        similarity_index=similarity_index,
        total_chunks=len(chunks),
        matched_chunks=matched_chunks,
        matched_sources=matched_sources
    )

    # URL download report
    report_url = request.build_absolute_uri(
        f"/api/reports/{report_filename}/"
    )

    # Response hasil scanning
    return Response({
        "status": "success",
        "title": title,
        "filename": uploaded_file.name,
        "similarity_index": similarity_index,
        "total_chunks": len(chunks),
        "matched_chunks": matched_chunks,
        "matched_sources": matched_sources,
        "ranked_sources": ranked_sources,
        "report_filename": report_filename,
        "report_url": report_url
    })


@api_view(["GET"])
def download_report(request, filename):
    report_directory = os.path.join(
        settings.BASE_DIR,
        "reports"
    )

    safe_filename = os.path.basename(filename)

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