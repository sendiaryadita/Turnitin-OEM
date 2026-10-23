
"""
AntiKopas - Automatic History Cleanup

Menjaga riwayat selama 2 jam setelah analisis
selesai atau gagal.

Tidak menghapus job pending/processing.

Mode default: simulasi (dry run).
Penghapusan nyata: python cleanup_history.py --apply
"""

import argparse
import os
import re
from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

import django  # noqa: E402

django.setup()

from django.db import transaction  # noqa: E402
from django.db.models import Q  # noqa: E402
from django.utils import timezone  # noqa: E402

from detector.models import (  # noqa: E402
    AnalysisJob,
    Document,
    Report,
    SourceJournal,
)


def delete_stored_file(storage, name, label):
    """Hapus file melalui storage Django."""

    if not name:
        return

    # Hindari menghapus file yang masih digunakan
    # oleh data lain di database.
    if label == "upload":
        still_used = Document.objects.filter(
            original_file=name
        ).exists()
    else:
        still_used = Report.objects.filter(
            file=name
        ).exists()

    if still_used:
        print(
            f"[SKIP] File masih digunakan: {name}"
        )
        return

    try:
        storage.delete(name)
        print(f"[FILE] Dihapus: {name}")
    except Exception as exc:
        print(
            f"[WARNING] Gagal hapus file {name}: {exc}"
        )


def delete_generated_report_copy(report_name):
    """
    Hapus salinan PDF yang dibuat di folder
    BASE_DIR/reports oleh report_generator.

    Hanya menerima nama file laporan AntiKopas.
    """

    if not report_name:
        return

    filename = Path(report_name).name

    allowed = re.fullmatch(
        r"antikopas_report_"
        r"\d{8}_\d{6}_\d{6}\.pdf",
        filename,
    )

    if not allowed:
        return

    report_path = BASE_DIR / "reports" / filename

    try:
        if report_path.is_file():
            report_path.unlink()
            print(
                "[PDF] Salinan laporan dihapus:",
                filename,
            )
    except OSError as exc:
        print(
            "[WARNING] Gagal hapus salinan PDF:",
            exc,
        )


def cleanup_job(job_id, cutoff):
    """
    Hapus satu job kedaluwarsa beserta data terkait.
    Penghapusan database dilakukan dalam transaksi.
    """

    report_file = None
    original_file = None
    report_name = ""

    with transaction.atomic():
        job = (
            AnalysisJob.objects
            .select_for_update()
            .select_related("document")
            .get(pk=job_id)
        )

        allowed_status = {
            AnalysisJob.Status.COMPLETED,
            AnalysisJob.Status.FAILED,
        }

        finished_at = (
            job.completed_at or job.created_at
        )

        # Jangan hapus job aktif atau yang belum
        # berusia dua jam.
        if (
            job.status not in allowed_status
            or finished_at > cutoff
        ):
            return False

        document = job.document

        report = Report.objects.filter(
            analysis_id=job.pk
        ).first()

        if report and report.file:
            report_name = report.file.name

            report_file = (
                report.file.storage,
                report.file.name,
            )

        if document.original_file:
            original_file = (
                document.original_file.storage,
                document.original_file.name,
            )

        document_id = document.pk

        # Cascade akan menghapus Report,
        # DocumentChunk, dan SimilarityResult.
        job.delete()

        # Dokumen mungkin dipakai job lain.
        # Hapus hanya jika tidak ada job tersisa.
        has_other_jobs = AnalysisJob.objects.filter(
            document_id=document_id
        ).exists()

        delete_document = not has_other_jobs

        if delete_document:
            document.delete()

    # File fisik dihapus setelah transaksi DB sukses.
    if report_file:
        delete_stored_file(
            report_file[0],
            report_file[1],
            "report",
        )

    if report_name:
        delete_generated_report_copy(report_name)

    if delete_document and original_file:
        delete_stored_file(
            original_file[0],
            original_file[1],
            "upload",
        )

    print(f"[CLEANUP] Job #{job_id} dihapus")

    return True


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Hapus history AntiKopas yang "
            "melewati masa penyimpanan."
        )
    )

    parser.add_argument(
        "--hours",
        type=int,
        default=2,
        help="Lama penyimpanan dalam jam (default: 2).",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Jalankan penghapusan sungguhan.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maksimal job per eksekusi.",
    )

    args = parser.parse_args()

    if args.hours < 1 or args.limit < 1:
        parser.error(
            "--hours dan --limit harus lebih dari 0"
        )

    cutoff = timezone.now() - timedelta(
        hours=args.hours
    )

    eligible = (
        AnalysisJob.objects.filter(
            status__in=[
                AnalysisJob.Status.COMPLETED,
                AnalysisJob.Status.FAILED,
            ]
        )
        .filter(
            Q(completed_at__lte=cutoff)
            | Q(
                completed_at__isnull=True,
                created_at__lte=cutoff,
            )
        )
        .order_by("pk")
    )

    total = eligible.count()

    print()
    print("====================================")
    print("ANTIKOPAS - HISTORY CLEANUP")
    print("====================================")
    print(f"Retensi       : {args.hours} jam")
    print(f"Batas waktu  : {cutoff.isoformat()}")
    print(f"Job kedaluwarsa: {total}")
    print(
        "Mode          :",
        "HAPUS" if args.apply else "SIMULASI",
    )

    if not args.apply:
        print()
        print(
            "[AMAN] Tidak ada data yang dihapus."
        )

        for job in eligible[:10]:
            print(
                f"  Job #{job.pk} - "
                f"{job.status} - "
                f"{job.created_at}"
            )

        print(
            "\nGunakan --apply untuk "
            "penghapusan sungguhan."
        )
        return

    job_ids = list(
        eligible.values_list(
            "pk",
            flat=True,
        )[:args.limit]
    )

    deleted = 0
    errors = 0

    for job_id in job_ids:
        try:
            if cleanup_job(job_id, cutoff):
                deleted += 1

        except AnalysisJob.DoesNotExist:
            continue

        except Exception as exc:
            errors += 1
            print(
                f"[ERROR] Job #{job_id}: {exc}"
            )

    # Metadata jurnal yang tidak lagi dipakai
    # oleh hasil analisis mana pun.
    orphan_sources = SourceJournal.objects.filter(
        similarity_results__isnull=True,
        created_at__lte=cutoff,
    )

    source_count = orphan_sources.count()

    orphan_sources.delete()

    print()
    print("====================================")
    print(f"Job dihapus       : {deleted}")
    print(f"Metadata dibersihkan: {source_count}")
    print(f"Error             : {errors}")
    print("====================================")


if __name__ == "__main__":
    main()
