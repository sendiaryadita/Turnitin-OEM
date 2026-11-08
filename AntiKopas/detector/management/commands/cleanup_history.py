import os
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from detector.models import AnalysisJob


class Command(BaseCommand):
    help = (
        "Menghapus hasil analisis AntiKopas yang sudah melewati masa simpan. "
        "Default: 2 jam sejak completed_at."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Hanya menampilkan data yang akan dihapus tanpa menghapus apa pun.",
        )
        parser.add_argument(
            "--hours",
            type=float,
            default=2.0,
            help="Masa simpan dalam jam. Default: 2.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        retention_hours = options["hours"]

        if retention_hours <= 0:
            self.stderr.write(
                self.style.ERROR("--hours harus lebih besar dari 0.")
            )
            return

        now = timezone.now()
        cutoff = now - timedelta(hours=retention_hours)

        expired_jobs = (
            AnalysisJob.objects
            .select_related("document")
            .filter(
                status__in=[
                    AnalysisJob.Status.COMPLETED,
                    AnalysisJob.Status.FAILED,
                ],
                completed_at__isnull=False,
                completed_at__lte=cutoff,
            )
            .order_by("completed_at")
        )

        total = expired_jobs.count()
        mode = "DRY RUN" if dry_run else "DELETE"

        self.stdout.write(
            f"[AntiKopas Cleanup] Mode={mode} | "
            f"retention={retention_hours:g} jam | "
            f"kandidat={total}"
        )

        if total == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "[AntiKopas Cleanup] Tidak ada data kedaluwarsa."
                )
            )
            return

        deleted_jobs = 0
        deleted_documents = 0
        deleted_legacy_reports = 0
        failed_deletions = 0

        for job in expired_jobs.iterator():
            document = job.document
            job_id = job.pk
            title = document.title
            completed_at = job.completed_at
            expires_at = completed_at + timedelta(hours=retention_hours)

            # Saat ini satu Document biasanya memiliki satu AnalysisJob.
            # Pengecekan ini mencegah file dokumen ikut terhapus jika suatu
            # saat satu dokumen dipakai oleh lebih dari satu job.
            has_other_jobs = document.analyses.exclude(pk=job.pk).exists()

            report = getattr(job, "report", None)

            report_storage_name = ""
            report_basename = ""

            if report is not None and report.file:
                report_storage_name = str(report.file.name or "")
                report_basename = os.path.basename(report_storage_name)

            document_storage_name = (
                str(document.original_file.name or "")
                if document.original_file
                else ""
            )

            # views.py saat ini membuat PDF awal di BASE_DIR/reports/<filename>
            # lalu juga menyimpannya ke FileField Report. Karena itu cleanup
            # perlu membersihkan file report "flat" ini juga agar storage server
            # tidak terus menumpuk.
            legacy_report_path = (
                Path(settings.BASE_DIR) / "reports" / report_basename
                if report_basename
                else None
            )

            if dry_run:
                self.stdout.write(
                    f"  - Job #{job_id} | {job.status} | "
                    f"{title!r} | expired={expires_at.isoformat()}"
                )

                if report_storage_name:
                    self.stdout.write(
                        f"      report storage: {report_storage_name}"
                    )

                if legacy_report_path is not None:
                    self.stdout.write(
                        f"      report runtime: {legacy_report_path}"
                    )

                if document_storage_name and not has_other_jobs:
                    self.stdout.write(
                        f"      document: {document_storage_name}"
                    )

                continue

            try:
                # FileField tidak otomatis menghapus file fisik ketika row DB
                # dihapus, jadi file pada storage dibersihkan lebih dulu.
                if report is not None and report.file:
                    report.file.delete(save=False)

                # Bersihkan PDF hasil generate yang dipakai endpoint download.
                if (
                    legacy_report_path is not None
                    and legacy_report_path.is_file()
                ):
                    legacy_report_path.unlink()
                    deleted_legacy_reports += 1

                if not has_other_jobs and document.original_file:
                    document.original_file.delete(save=False)

                # Cascade dari AnalysisJob membersihkan Report, DocumentChunk,
                # SimilarityResult, dan relasi lain dengan on_delete=CASCADE.
                job.delete()
                deleted_jobs += 1

                if not has_other_jobs:
                    document.delete()
                    deleted_documents += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [OK] Job expired dihapus: #{job_id} - {title}"
                    )
                )

            except Exception as exc:
                failed_deletions += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"  [GAGAL] Job #{job_id} - {title}: {exc}"
                    )
                )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[AntiKopas Cleanup] DRY RUN selesai. "
                    f"{total} job akan dihapus."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                "[AntiKopas Cleanup] Selesai | "
                f"job={deleted_jobs} | "
                f"document={deleted_documents} | "
                f"report_runtime={deleted_legacy_reports} | "
                f"gagal={failed_deletions}"
            )
        )
