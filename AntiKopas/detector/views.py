
import os
import hashlib
import io
import zipfile
from datetime import datetime
from pathlib import Path

from django.utils import timezone
from django.utils.text import slugify

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import FileResponse
from django.conf import settings
from django.core.files import File
from django.db.models import Q

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import (
    AnalysisJob,
    Document,
    DocumentChunk,
    Report,
    SimilarityResult,
    SourceJournal,
)
from .services.history_cleanup import delete_analysis

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".docx"}
MAX_DOCUMENT_SIZE = 25 * 1024 * 1024

# ==========================================
# 1. HEALTH CHECK
# ==========================================

@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({
        "status": "ok",
        "message": "AntiKopas backend is running"
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    """Membuat akun pengguna baru tanpa mengembalikan password."""
    username = str(request.data.get("username", "")).strip()
    password = str(request.data.get("password", ""))
    password_confirm = str(request.data.get("password_confirm", ""))

    if not username or not password or not password_confirm:
        return Response({
            "status": "error",
            "message": "username, password, dan password_confirm wajib diisi",
        }, status=400)
    if password != password_confirm:
        return Response({
            "status": "error",
            "message": "Konfirmasi password tidak cocok",
        }, status=400)
    if User.objects.filter(username=username).exists():
        return Response({
            "status": "error",
            "message": "Username sudah digunakan",
        }, status=409)

    try:
        validate_password(password)
    except ValidationError as error:
        return Response({
            "status": "error",
            "message": list(error.messages),
        }, status=400)

    user = User.objects.create_user(username=username, password=password)
    return Response({
        "status": "success",
        "message": "Akun berhasil dibuat",
        "username": user.username,
    }, status=201)

# ==========================================
# IDENTITAS PENGGUNA YANG SEDANG LOGIN
# ==========================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = request.user

    return Response({
        "status": "success",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": "admin" if user.is_staff else "user",
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        }
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def analysis_list(request):
    """Mengembalikan riwayat analisis dengan pencarian dan pagination."""
    try:
        page = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("page_size", 10)), 1), 50)
    except (TypeError, ValueError):
        return Response({"status": "error", "message": "Parameter halaman tidak valid"}, status=400)

    jobs = AnalysisJob.objects.select_related("document").filter(
        document__uploaded_by=request.user
    ).active()
    query = str(request.query_params.get("q", "")).strip()
    status = str(request.query_params.get("status", "")).strip().lower()
    if query:
        jobs = jobs.filter(document__title__icontains=query)
    if status in {choice.value for choice in AnalysisJob.Status}:
        jobs = jobs.filter(status=status)

    total = jobs.count()
    total_pages = max((total + page_size - 1) // page_size, 1)
    page = min(page, total_pages)
    start = (page - 1) * page_size
    jobs = jobs[start:start + page_size]
    return Response({
        "status": "success",
        "count": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "results": [
            {
                "id": job.id,
                "title": job.document.title,
                "status": job.status,
                "progress_percent": (
                    100
                    if job.status == AnalysisJob.Status.COMPLETED
                    else job.progress_percent
                ),
                "progress_stage": (
                    "Pemeriksaan selesai"
                    if job.status == AnalysisJob.Status.COMPLETED
                    else "Pemeriksaan gagal"
                    if job.status == AnalysisJob.Status.FAILED
                    else job.progress_stage
                ),
                "similarity_index": float(job.similarity_index),
                "total_chunks": job.total_chunks,
                "matched_chunks": job.matched_chunks,
                "created_at": job.created_at,
                "completed_at": job.completed_at,
                "expires_at": job.expires_at,
                "report_url": (
                    request.build_absolute_uri(
                        f"/api/reports/{os.path.basename(job.report.file.name)}/"
                    ) if hasattr(job, "report") and job.report.file else None
                ),
            }
            for job in jobs
        ],
    })


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def analysis_detail(request, analysis_id):
    """Mengembalikan detail analisis beserta chunk dan sumber."""
    try:
        job = AnalysisJob.objects.select_related("document").get(
            pk=analysis_id,
            document__uploaded_by=request.user,
        )
    except AnalysisJob.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Analisis tidak ditemukan",
        }, status=404)

    if request.method != "DELETE" and job.is_expired:
        return expired_response()

    if request.method == "PATCH":
        title = str(request.data.get("title", "")).strip()
        if not title:
            return Response({"status": "error", "message": "Judul wajib diisi"}, status=400)
        if len(title) > 500:
            return Response({"status": "error", "message": "Judul maksimal 500 karakter"}, status=400)
        job.document.title = title
        job.document.save(update_fields=["title", "updated_at"])
        return Response({"status": "success", "message": "Judul berhasil diperbarui", "title": title})

    if request.method == "DELETE":
        delete_analysis(job.pk)
        return Response({
            "status": "success",
            "message": "Riwayat analisis berhasil dihapus",
        })

    chunks = []
    for chunk in job.chunks.all():
        results = chunk.similarity_results.select_related("source").all()
        chunks.append({
            "index": chunk.chunk_index,
            "text": chunk.text,
            "token_count": chunk.token_count,
            "matches": [
                {
                    "matched": result.matched,
                    "embedding_score": result.embedding_score,
                    "cross_encoder_score": result.cross_encoder_score,
                    "validation_reason": result.validation_reason,
                    "source_excerpt": result.source_excerpt,
                    "source": {
                        "title": result.source.title,
                        "year": result.source.year,
                        "doi": result.source.doi,
                        "url": result.source.url,
                    },
                }
                for result in results
            ],
        })

    report_url = None
    if hasattr(job, "report") and job.report.file:
        report_url = request.build_absolute_uri(
            f"/api/reports/{os.path.basename(job.report.file.name)}/"
        )

    return Response({
        "status": "success",
        "id": job.id,
        "document": {
            "id": job.document_id,
            "title": job.document.title,
            "filename": os.path.basename(job.document.original_file.name),
        },
        "analysis": {
            "status": job.status,
            "similarity_index": float(job.similarity_index),
            "total_chunks": job.total_chunks,
            "matched_chunks": job.matched_chunks,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "expires_at": job.expires_at,
        },
        "chunks": chunks,
        "report_url": report_url,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def analysis_stats(request):
    jobs = AnalysisJob.objects.filter(document__uploaded_by=request.user).active()
    completed = jobs.filter(status=AnalysisJob.Status.COMPLETED)
    total_chunks = sum(jobs.values_list("total_chunks", flat=True))
    matched_chunks = sum(jobs.values_list("matched_chunks", flat=True))
    average_similarity = 0
    if completed.exists():
        average_similarity = sum(
            float(value) for value in completed.values_list("similarity_index", flat=True)
        ) / completed.count()
    return Response({
        "status": "success",
        "total_analyses": jobs.count(),
        "retention_seconds": settings.ANALYSIS_RETENTION_HOURS * 3600,
        "completed_analyses": completed.count(),
        "processing_analyses": jobs.filter(
            status__in=[AnalysisJob.Status.PENDING, AnalysisJob.Status.PROCESSING]
        ).count(),
        "failed_analyses": jobs.filter(status=AnalysisJob.Status.FAILED).count(),
        "total_chunks": total_chunks,
        "matched_chunks": matched_chunks,
        "average_similarity": round(average_similarity, 2),
    })


# ==========================================
# 2. DETECT SIMILARITY
# ==========================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
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

    file_extension = Path(uploaded_file.name or "").suffix.lower()
    if file_extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        return Response({
            "status": "error",
            "message": "Format file tidak didukung. Gunakan PDF atau DOCX.",
        }, status=400)

    if uploaded_file.size > MAX_DOCUMENT_SIZE:
        return Response({
            "status": "error",
            "message": "Ukuran file terlalu besar. Maksimal ukuran file adalah 25 MB.",
        }, status=400)

    # Simpan dokumen dan buat jejak proses sebelum model AI dijalankan.
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    if file_extension == ".pdf" and not file_bytes.startswith(b"%PDF-"):
        return Response({
            "status": "error",
            "message": "Isi file tidak sesuai dengan format PDF.",
        }, status=400)

    if file_extension == ".docx":
        uploaded_file.seek(0)
        is_valid_docx = zipfile.is_zipfile(io.BytesIO(file_bytes))
        uploaded_file.seek(0)
        if not is_valid_docx:
            return Response({
                "status": "error",
                "message": "Isi file tidak sesuai dengan format DOCX.",
            }, status=400)
    document = Document.objects.create(
        uploaded_by=request.user,
        title=title,
        original_file=uploaded_file,
        file_type=(uploaded_file.content_type or "")[:20],
        file_size=uploaded_file.size,
        sha256=hashlib.sha256(file_bytes).hexdigest(),
    )
    analysis_job = AnalysisJob.objects.create(
        document=document,
        status=AnalysisJob.Status.PROCESSING,
        progress_percent=2,
        progress_stage="Membaca dokumen",
        started_at=timezone.now(),
    )

    # Import service berat hanya setelah input dasar valid.
    # Health check, startup, dan validasi request tidak perlu memuat
    # Torch/model AI terlebih dahulu.
    from .services.document_parser import extract_text
    from .services.report_generator import generate_report

    def update_analysis_progress(progress_data):
        """Simpan progress tanpa membiarkan kegagalannya membatalkan scan."""
        if not isinstance(progress_data, dict):
            return

        try:
            current_percent = int(analysis_job.progress_percent or 0)
            incoming_percent = int(round(float(
                progress_data.get("percent", current_percent)
            )))
            incoming_percent = max(0, min(incoming_percent, 99))

            # Progress tidak boleh mundur jika callback datang tidak berurutan.
            if incoming_percent < current_percent:
                return

            stage = str(
                progress_data.get("stage")
                or analysis_job.progress_stage
                or "Memproses dokumen"
            ).strip()[:100]
            if not stage:
                stage = "Memproses dokumen"

            updated = AnalysisJob.objects.filter(
                pk=analysis_job.pk,
                status=AnalysisJob.Status.PROCESSING,
            ).update(
                progress_percent=incoming_percent,
                progress_stage=stage,
            )

            if updated:
                analysis_job.progress_percent = incoming_percent
                analysis_job.progress_stage = stage

        except Exception as progress_error:
            # Progress hanya untuk tampilan. Gangguan saat menyimpannya
            # tidak boleh menghentikan proses analisis yang sebenarnya.
            print(
                "[Progress] Gagal menyimpan progress:",
                type(progress_error).__name__,
            )

    def mark_analysis_failed(error):
        """Catat kegagalan tanpa mengubah progress menjadi 100%."""
        analysis_job.status = AnalysisJob.Status.FAILED
        analysis_job.error_message = str(error)
        analysis_job.completed_at = timezone.now()
        analysis_job.progress_stage = "Pemeriksaan gagal"
        analysis_job.save(update_fields=[
            "status",
            "error_message",
            "completed_at",
            "progress_stage",
        ])

    # --------------------------------------
    # D. EKSTRAKSI DOKUMEN
    # --------------------------------------

    try:
        text = extract_text(uploaded_file)

    except ValueError as e:
        mark_analysis_failed(e)
        return Response({
            "status": "error",
            "message": str(e)
        }, status=400)

    except Exception as e:
        mark_analysis_failed(e)
        return Response({
            "status": "error",
            "message": (
                f"Gagal membaca file: {str(e)}"
            )
        }, status=400)

    if not text or not str(text).strip():
        mark_analysis_failed("Isi dokumen tidak dapat dibaca")
        return Response({
            "status": "error",
            "message": "Isi dokumen tidak dapat dibaca"
        }, status=400)

    update_analysis_progress({
        "percent": 10,
        "stage": "Dokumen berhasil dibaca",
        "message": "Dokumen berhasil dibaca dan siap diperiksa.",
    })

    # --------------------------------------
    # E. ANALISIS AI
    # --------------------------------------

    try:
        from .services.antikopas_service import analyze_antikopas

        analysis = analyze_antikopas(
            text,
            title,
            progress_callback=update_analysis_progress,
        )

    except Exception as e:
        mark_analysis_failed(e)
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

    # Simpan hasil analisis sementara.
    # Status tetap PROCESSING sampai laporan PDF berhasil disimpan.
    update_analysis_progress({
        "percent": 98,
        "stage": "Menyimpan hasil pemeriksaan",
        "message": "Hasil perbandingan selesai dan sedang disimpan.",
    })
    analysis_job.total_chunks = total_chunks
    analysis_job.matched_chunks = matched_chunks
    analysis_job.similarity_index = float(similarity_index or 0)
    analysis_job.status = AnalysisJob.Status.PROCESSING
    analysis_job.completed_at = None

    analysis_job.save(update_fields=[
        "total_chunks",
        "matched_chunks",
        "similarity_index",
        "status",
        "completed_at",
    ])

    source_cache = {}
    for index, chunk_data in enumerate(document_results):
        chunk_text = str(chunk_data.get("text", ""))
        document_chunk = DocumentChunk.objects.create(
            analysis=analysis_job,
            chunk_index=chunk_data.get("chunk_index", index),
            text=chunk_text,
            token_count=len(chunk_text.split()),
        )
        for match in chunk_data.get("matches", []):
            source_key = (
                match.get("doi") or match.get("url") or match.get("title")
            )
            if not source_key:
                continue
            source_key = str(source_key).strip()
            source = source_cache.get(source_key)
            if source is None:
                source, _ = SourceJournal.objects.get_or_create(
                    openalex_id=str(match.get("openalex_id", ""))[:255],
                    title=str(match.get("title", "Untitled"))[:1000],
                    defaults={
                        "year": match.get("year"),
                        "doi": str(match.get("doi", ""))[:500],
                        "url": str(match.get("url", ""))[:2000],
                    },
                )
                source_cache[source_key] = source
            SimilarityResult.objects.update_or_create(
                analysis=analysis_job,
                chunk=document_chunk,
                source=source,
                defaults={
                    "embedding_score": match.get("minilm_score"),
                    "cross_encoder_score": match.get("cross_score"),
                    "matched": bool(match.get("matched")),
                    "validation_reason": str(match.get("validation_reason", ""))[:255],
                    "source_excerpt": str(match.get("source_excerpt", "")),
                },
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

    update_analysis_progress({
        "percent": 99,
        "stage": "Menyusun laporan PDF",
        "message": "Hasil pemeriksaan sedang disusun menjadi laporan.",
    })

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
        mark_analysis_failed(e)
        return Response({
            "status": "error",
            "message": (
                "Gagal membuat report PDF: "
                f"{str(e)}"
            )
        }, status=500)

    try:
        with open(report_path, "rb") as report_file:
            Report.objects.update_or_create(
                analysis=analysis_job,
                defaults={"file": File(report_file, name=report_filename)},
            )
    except Exception as e:
        mark_analysis_failed(e)
        return Response({
            "status": "error",
            "message": f"Gagal menyimpan laporan PDF: {str(e)}",
        }, status=500)

    # Analisis dinyatakan selesai setelah laporan PDF tersimpan.
    # Waktu ini akan menjadi acuan masa simpan dokumen 2 jam.
    analysis_job.status = AnalysisJob.Status.COMPLETED
    analysis_job.completed_at = timezone.now()
    analysis_job.progress_percent = 100
    analysis_job.progress_stage = "Pemeriksaan selesai"

    analysis_job.save(update_fields=[
        "status",
        "completed_at",
        "progress_percent",
        "progress_stage",
    ])

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

        "analysis_id": analysis_job.id,

        "document_id": document.id,

        "title": title,

        "filename": uploaded_file.name,

        "similarity_index": similarity_index,

        "total_similarity": total_similarity,

        "total_chunks": total_chunks,

        "matched_chunks": matched_chunks,

        "matched_sources": matched_sources,

        "source_similarities": source_similarities,

        "diagnostic_code": analysis.get("diagnostic_code", ""),

        "diagnostic_message": analysis.get("diagnostic_message", ""),

        "chunks": document_results,

        "report_filename": report_filename,

        "expires_at": analysis_job.expires_at,

        "report_url": report_url

    })


# ==========================================
# 3. DOWNLOAD PDF REPORT
# ==========================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_report(
    request,
    filename
):

    safe_filename = os.path.basename(
        filename
    )

    # Hanya izinkan file PDF yang
    # dibuat oleh sistem AntiKopas.
    if (
        filename != safe_filename
        or not safe_filename.startswith(
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

    report_record = Report.objects.filter(
        Q(file=safe_filename) | Q(file__endswith="/" + safe_filename),
        analysis__document__uploaded_by=request.user,
    ).select_related("analysis__document").first()
    if report_record is None:
        return Response({
            "status": "error",
            "message": "Report tidak ditemukan",
        }, status=404)

    return report_response(report_record)


def expired_response():
    response = Response({
        "status": "error",
        "code": "analysis_expired",
        "message": "Masa simpan analisis sudah berakhir. Silakan unggah ulang dokumen.",
    }, status=410)
    response["Cache-Control"] = "private, no-store"
    return response


def report_response(report_record):
    if report_record.analysis.is_expired:
        return expired_response()

    # FileField adalah lokasi utama; salinan lama tetap didukung.
    try:
        report_file = report_record.file.open("rb")
    except FileNotFoundError:
        directory = (Path(settings.BASE_DIR) / "reports").resolve()
        report_path = (directory / Path(report_record.file.name).name).resolve()
        if report_path.parent != directory:
            return Response({"message": "Report tidak ditemukan"}, status=404)
        try:
            report_file = report_path.open("rb")
        except FileNotFoundError:
            return Response({"message": "Report tidak ditemukan"}, status=404)

    document = report_record.analysis.document
    original_title = Path(document.original_file.name).stem
    title_slug = (
        slugify(document.title) or slugify(original_title) or "hasil-analisis"
    )[:70].strip("-")
    download_filename = f"antikopas_{title_slug}_AK-{report_record.analysis_id}.pdf"

    response = FileResponse(
        report_file,
        as_attachment=True,
        filename=download_filename,
        content_type="application/pdf"
    )
    response["Cache-Control"] = "private, no-store"
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_media(request, filename):
    """Lindungi URL FileField yang sebelumnya dilayani sebagai file publik."""
    document = Document.objects.filter(
        original_file=filename, uploaded_by=request.user,
    ).first()
    if document is not None:
        if not document.analyses.active().exists():
            return expired_response()
        try:
            document_file = document.original_file.open("rb")
        except FileNotFoundError:
            return Response({"message": "Dokumen tidak ditemukan"}, status=404)
        response = FileResponse(
            document_file, as_attachment=True,
            filename=Path(document.original_file.name).name,
        )
        response["Cache-Control"] = "private, no-store"
        return response

    report = Report.objects.filter(
        file=filename, analysis__document__uploaded_by=request.user,
    ).select_related("analysis__document").first()
    if report is not None:
        return report_response(report)
    return Response({"message": "File tidak ditemukan"}, status=404)
