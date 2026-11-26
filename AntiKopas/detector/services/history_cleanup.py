"""Aturan penghapusan yang dipakai API, command, dan worker berkala."""

import logging
from pathlib import Path
from threading import Event, Thread

from django.conf import settings
from django.db import close_old_connections, connections, transaction
from django.db.models import Q
from django.utils import timezone

from detector.models import AnalysisJob, Document, Report

logger = logging.getLogger(__name__)


def delete_analysis(job_id, *, expired_only=False, at=None):
    """Hapus file sebelum row DB; kegagalan file menyisakan row untuk retry.

    File/dokumen bersama dipertahankan selama masih direferensikan data lain.
    Seluruh path berasal dari FileField atau folder reports yang telah dibatasi.
    """
    with transaction.atomic():
        job = AnalysisJob.objects.select_for_update().filter(pk=job_id).first()
        if job is None:
            return False
        if expired_only and job.expires_at > (at or timezone.now()):
            return False

        document = Document.objects.select_for_update().get(pk=job.document_id)
        report = Report.objects.filter(analysis=job).first()
        if report and report.file:
            name = report.file.name
            filename = Path(name).name
            other_reports = Report.objects.exclude(pk=report.pk)
            if not other_reports.filter(file=name).exists():
                report.file.storage.delete(name)

            # Salinan lama di BASE_DIR/reports juga perlu dibersihkan.
            if not other_reports.filter(
                Q(file=filename) | Q(file__endswith="/" + filename)
            ).exists():
                directory = (Path(settings.BASE_DIR) / "reports").resolve()
                copy = (directory / filename).resolve()
                if copy.parent != directory:
                    raise ValueError("Lokasi laporan berada di luar folder reports.")
                if copy.is_file():
                    copy.unlink()

        delete_document = not document.analyses.exclude(pk=job.pk).exists()
        if delete_document and document.original_file:
            name = document.original_file.name
            if not Document.objects.exclude(pk=document.pk).filter(
                original_file=name
            ).exists():
                document.original_file.storage.delete(name)

        job.delete()
        if delete_document:
            document.delete()
    return True


def cleanup_expired_analyses(*, dry_run=False, at=None, limit=1000):
    at = at or timezone.now()
    jobs = AnalysisJob.objects.expired(at).order_by("pk")
    ids = list(jobs.values_list("pk", flat=True)[:limit])
    result = {"candidates": len(ids), "deleted": 0, "errors": 0}
    if dry_run:
        return result
    for job_id in ids:
        try:
            result["deleted"] += int(delete_analysis(job_id, expired_only=True, at=at))
        except Exception:
            result["errors"] += 1
            logger.exception("Gagal membersihkan analisis #%s; akan dicoba lagi.", job_id)
    return result


def run_cleanup_loop(stop, interval):
    """Satu putaran segera, kemudian berkala; gagal sekali tidak mematikan worker."""
    try:
        while not stop.is_set():
            try:
                close_old_connections()
                result = cleanup_expired_analyses()
                if result["deleted"] or result["errors"]:
                    logger.info("History cleanup: %s", result)
            except Exception:
                logger.exception("Worker cleanup gagal; akan mencoba pada putaran berikutnya.")
            finally:
                close_old_connections()
            stop.wait(interval)
    finally:
        connections.close_all()


def start_cleanup_worker():
    stop = Event()
    worker = Thread(
        target=run_cleanup_loop,
        args=(stop, settings.HISTORY_CLEANUP_INTERVAL_SECONDS),
        name="antikopas-history-cleanup",
        daemon=True,
    )
    worker.start()
    return stop, worker
