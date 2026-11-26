from datetime import timedelta
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command, get_commands
from django.core.management.base import CommandError
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from docx import Document as WordDocument
from rest_framework.test import APIClient

from .models import AnalysisJob, Document, DocumentChunk, Report, SimilarityResult, SourceJournal
from .services.history_cleanup import cleanup_expired_analyses, run_cleanup_loop


@override_settings(ANALYSIS_RETENTION_HOURS=2, ANALYSIS_STALE_HOURS=24)
class RetentionTests(TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        settings = override_settings(BASE_DIR=self.root, MEDIA_ROOT=self.root / "media")
        settings.enable()
        self.addCleanup(settings.disable)
        self.now = timezone.now()
        clock = patch("django.utils.timezone.now", return_value=self.now)
        clock.start()
        self.addCleanup(clock.stop)
        self.owner = User.objects.create_user(username="retention-owner")
        self.other = User.objects.create_user(username="retention-other")
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def make_job(self, *, status="completed", age=0, finished=True, started=True, document=None):
        if document is None:
            document = Document.objects.create(
                uploaded_by=self.owner, title="Dokumen retensi",
                original_file=ContentFile(b"isi dokumen", name="uji.pdf"),
            )
        anchor = self.now - timedelta(hours=age)
        job = AnalysisJob.objects.create(
            document=document, status=status,
            started_at=anchor if started else None,
            completed_at=anchor if finished else None,
        )
        AnalysisJob.objects.filter(pk=job.pk).update(created_at=anchor)
        job.refresh_from_db()
        return job

    def make_report(self, job, filename=None):
        filename = filename or f"antikopas_report_test_{job.pk}.pdf"
        report = Report.objects.create(
            analysis=job, file=ContentFile(b"%PDF-1.4\n%%EOF", name=filename),
        )
        directory = self.root / "reports"
        directory.mkdir(exist_ok=True)
        legacy = directory / Path(report.file.name).name
        legacy.write_bytes(b"%PDF-1.4\nlegacy\n%%EOF")
        return report, legacy

    def assert_download(self, url, content):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        try:
            self.assertEqual(b"".join(response.streaming_content), content)
        finally:
            response.close()

    def test_expiration_boundary_is_inclusive_and_matches_queryset(self):
        before = self.make_job(age=2 - 1 / 3600)
        boundary = self.make_job(age=2)
        after = self.make_job(age=2 + 1 / 3600)
        self.assertFalse(before.is_expired)
        self.assertEqual(boundary.expires_at, self.now)
        self.assertTrue(boundary.is_expired)
        self.assertTrue(after.is_expired)
        self.assertEqual(set(AnalysisJob.objects.active().values_list("pk", flat=True)), {before.pk})
        self.assertEqual(set(AnalysisJob.objects.expired().values_list("pk", flat=True)), {boundary.pk, after.pk})

    def test_terminal_jobs_without_finish_use_started_then_created(self):
        for status in ("completed", "failed"):
            for started in (True, False):
                with self.subTest(status=status, started=started):
                    job = self.make_job(status=status, age=2, finished=False, started=started)
                    self.assertEqual(job.expires_at, self.now)
                    self.assertTrue(job.is_expired)
                    self.assertTrue(AnalysisJob.objects.expired().filter(pk=job.pk).exists())

    def test_unfinished_jobs_expire_at_24_hours_using_start_or_creation(self):
        for status in ("pending", "processing"):
            for started in (True, False):
                with self.subTest(status=status, started=started):
                    fresh = self.make_job(status=status, age=23, finished=False, started=started)
                    stale = self.make_job(status=status, age=24, finished=False, started=started)
                    self.assertFalse(fresh.is_expired)
                    self.assertEqual(stale.expires_at, self.now)
                    self.assertTrue(AnalysisJob.objects.expired().filter(pk=stale.pk).exists())

    def test_completed_retention_starts_at_finish_not_upload(self):
        job = self.make_job(age=25)
        job.completed_at = self.now - timedelta(hours=1)
        job.save(update_fields=["completed_at"])
        self.assertFalse(job.is_expired)
        self.assertTrue(AnalysisJob.objects.active().filter(pk=job.pk).exists())

    def test_expired_detail_and_rename_are_blocked_before_cleanup(self):
        job = self.make_job(age=2)
        for method, kwargs in ((self.client.get, {}), (self.client.patch, {"data": {"title": "Ubah"}, "format": "json"})):
            response = method(f"/api/analyses/{job.pk}/", **kwargs)
            self.assertEqual(response.status_code, 410)
            self.assertEqual(response.json()["code"], "analysis_expired")
        job.document.refresh_from_db()
        self.assertEqual(job.document.title, "Dokumen retensi")
        self.assertTrue(AnalysisJob.objects.filter(pk=job.pk).exists())

    def test_expired_analyses_hidden_from_list_pagination_and_stats(self):
        self.make_job(age=2)
        self.make_job(status="failed", age=3)
        self.make_job(status="processing", age=24, finished=False)
        active = self.make_job(age=1)
        response = self.client.get("/api/analyses/?page_size=1")
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["id"], active.pk)
        self.assertEqual(response.json()["total_pages"], 1)
        self.assertIn("expires_at", response.json()["results"][0])
        stats = self.client.get("/api/analyses/stats/").json()
        self.assertEqual(stats["total_analyses"], 1)
        self.assertEqual(stats["completed_analyses"], 1)
        self.assertEqual(stats["failed_analyses"], 0)
        self.assertEqual(stats["processing_analyses"], 0)

    def test_active_detail_uses_authenticated_report_url_and_expiration(self):
        job = self.make_job(age=1)
        report, _ = self.make_report(job)
        response = self.client.get(f"/api/analyses/{job.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("/api/reports/", response.json()["report_url"])
        self.assertIn(Path(report.file.name).name, response.json()["report_url"])
        self.assertIn("expires_at", response.json()["analysis"])

    def test_expired_report_and_document_blocked_through_all_download_paths(self):
        job = self.make_job(age=2)
        report, _ = self.make_report(job)
        for url in (f"/api/reports/{Path(report.file.name).name}/", report.file.url, job.document.original_file.url):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 410)

    @override_settings(DEBUG=True)
    def test_media_requires_owner_login_even_in_debug(self):
        job = self.make_job()
        report, _ = self.make_report(job)
        urls = (job.document.original_file.url, report.file.url, f"/api/reports/{Path(report.file.name).name}/")
        for url in urls:
            self.assertEqual(APIClient().get(url).status_code, 401)
            self.client.force_authenticate(self.other)
            self.assertEqual(self.client.get(url).status_code, 404)
            self.client.force_authenticate(self.owner)
            self.assert_download(url, b"isi dokumen" if url == job.document.original_file.url else b"%PDF-1.4\n%%EOF")

    def test_expired_detail_does_not_reveal_other_users_data(self):
        job = self.make_job(age=2)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/analyses/{job.pk}/").status_code, 404)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(f"/api/analyses/{job.pk}/").status_code, 401)

    def test_legacy_report_fallback_still_obeys_expiration(self):
        job = self.make_job(age=1)
        report, _ = self.make_report(job)
        report.file.storage.delete(report.file.name)
        url = f"/api/reports/{Path(report.file.name).name}/"
        self.assert_download(url, b"%PDF-1.4\nlegacy\n%%EOF")
        job.completed_at = self.now - timedelta(hours=2)
        job.save(update_fields=["completed_at"])
        self.assertEqual(self.client.get(url).status_code, 410)

    def test_cleanup_deletes_expired_rows_upload_and_both_report_copies(self):
        job = self.make_job(age=2)
        document_id = job.document_id
        upload = Path(job.document.original_file.path)
        report, legacy = self.make_report(job)
        stored_report = Path(report.file.path)
        chunk = DocumentChunk.objects.create(analysis=job, chunk_index=1, text="rahasia")
        source = SourceJournal.objects.create(title="Sumber bersama")
        SimilarityResult.objects.create(analysis=job, chunk=chunk, source=source)
        result = cleanup_expired_analyses()
        self.assertEqual(result, {"candidates": 1, "deleted": 1, "errors": 0})
        self.assertFalse(AnalysisJob.objects.filter(pk=job.pk).exists())
        self.assertFalse(Document.objects.filter(pk=document_id).exists())
        self.assertFalse(Report.objects.exists())
        self.assertFalse(DocumentChunk.objects.exists())
        self.assertFalse(SimilarityResult.objects.exists())
        for file in (upload, stored_report, legacy):
            self.assertFalse(file.exists())
        self.assertTrue(SourceJournal.objects.filter(pk=source.pk).exists())
        self.assertEqual(cleanup_expired_analyses()["deleted"], 0)

    def test_cleanup_handles_failed_and_stalled_jobs_but_preserves_recent_jobs(self):
        for status, age, finished, started in (
            ("failed", 2, True, True), ("failed", 2, False, True),
            ("failed", 2, False, False), ("pending", 24, False, False),
            ("processing", 24, False, True),
        ):
            self.make_job(status=status, age=age, finished=finished, started=started)
        keep = [
            self.make_job(status="failed", age=1),
            self.make_job(status="processing", age=23, finished=False),
            self.make_job(status="pending", age=23, finished=False, started=False),
        ]
        self.assertEqual(cleanup_expired_analyses()["deleted"], 5)
        self.assertEqual(set(AnalysisJob.objects.values_list("pk", flat=True)), {job.pk for job in keep})

    def test_cleanup_keeps_shared_document_until_last_analysis_expires(self):
        expired = self.make_job(age=3)
        active = self.make_job(age=1, document=expired.document)
        upload = Path(expired.document.original_file.path)
        self.assertEqual(cleanup_expired_analyses()["deleted"], 1)
        self.assertTrue(upload.exists())
        self.assertTrue(Document.objects.filter(pk=active.document_id).exists())
        self.assert_download(active.document.original_file.url, b"isi dokumen")
        active.completed_at = self.now - timedelta(hours=2)
        active.save(update_fields=["completed_at"])
        self.assertEqual(cleanup_expired_analyses()["deleted"], 1)
        self.assertFalse(upload.exists())

    def test_cleanup_keeps_shared_storage_names_and_legacy_report(self):
        expired = self.make_job(age=3)
        active = self.make_job(age=1)
        active.document.original_file = expired.document.original_file.name
        active.document.save(update_fields=["original_file"])
        old_report, legacy = self.make_report(expired)
        Report.objects.create(analysis=active, file=old_report.file.name)
        upload = Path(expired.document.original_file.path)
        stored = Path(old_report.file.path)
        self.assertEqual(cleanup_expired_analyses()["deleted"], 1)
        for file in (upload, stored, legacy):
            self.assertTrue(file.exists())

    def test_owner_can_delete_expired_analysis_and_both_report_copies(self):
        job = self.make_job(age=2)
        report, legacy = self.make_report(job)
        stored = Path(report.file.path)
        response = self.client.delete(f"/api/analyses/{job.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(stored.exists())
        self.assertFalse(legacy.exists())

    def test_cleanup_dry_run_changes_neither_database_nor_files(self):
        job = self.make_job(age=2)
        report, legacy = self.make_report(job)
        output = StringIO()
        call_command("cleanup_history", dry_run=True, stdout=output)
        self.assertIn("DRY RUN | kandidat=1 | dihapus=0", output.getvalue())
        self.assertTrue(AnalysisJob.objects.filter(pk=job.pk).exists())
        self.assertTrue(Path(job.document.original_file.path).exists())
        self.assertTrue(Path(report.file.path).exists())
        self.assertTrue(legacy.exists())

    def test_cleanup_command_applies_retention_override_and_limit(self):
        first = self.make_job(age=1.5)
        second = self.make_job(age=1.5)
        call_command("cleanup_history", hours=1, limit=1, stdout=StringIO())
        self.assertFalse(AnalysisJob.objects.filter(pk=first.pk).exists())
        self.assertTrue(AnalysisJob.objects.filter(pk=second.pk).exists())
        self.assertFalse(second.is_expired)

    def test_invalid_cleanup_options_are_rejected(self):
        for options in ({"hours": 0}, {"hours": float("nan")}, {"interval": -1}, {"limit": 0}, {"watch": True, "dry_run": True}):
            with self.subTest(options=options), self.assertRaises(CommandError):
                call_command("cleanup_history", stdout=StringIO(), **options)

    def test_file_deletion_failure_keeps_rows_for_retry(self):
        job = self.make_job(age=2)
        report, legacy = self.make_report(job)
        with patch.object(report.file.storage, "delete", side_effect=PermissionError("file terkunci")):
            with self.assertLogs("detector.services.history_cleanup", level="ERROR"):
                result = cleanup_expired_analyses()
        self.assertEqual(result["errors"], 1)
        self.assertTrue(AnalysisJob.objects.filter(pk=job.pk).exists())
        self.assertTrue(Report.objects.filter(pk=report.pk).exists())
        self.assertTrue(legacy.exists())
        self.assertEqual(cleanup_expired_analyses()["deleted"], 1)

    def test_cleanup_rechecks_expiration_after_candidate_selection(self):
        job = self.make_job(age=2)
        from .services.history_cleanup import delete_analysis

        def finished_later(job_id, **kwargs):
            AnalysisJob.objects.filter(pk=job_id).update(completed_at=self.now)
            return delete_analysis(job_id, **kwargs)

        with patch("detector.services.history_cleanup.delete_analysis", side_effect=finished_later):
            self.assertEqual(cleanup_expired_analyses()["deleted"], 0)
        self.assertTrue(AnalysisJob.objects.filter(pk=job.pk).exists())

    def test_worker_recovers_from_failure_and_runs_again(self):
        stop = Event()
        waits = []

        def next_tick(interval):
            waits.append(interval)
            if len(waits) == 2:
                stop.set()

        with patch.object(stop, "wait", side_effect=next_tick), patch(
            "detector.services.history_cleanup.cleanup_expired_analyses",
            side_effect=[RuntimeError("database belum siap"), {"deleted": 0, "errors": 0}],
        ) as cleanup, patch("detector.services.history_cleanup.close_old_connections"), patch(
            "detector.services.history_cleanup.connections.close_all"
        ), self.assertLogs("detector.services.history_cleanup", level="ERROR"):
            run_cleanup_loop(stop, 60)
        self.assertEqual(cleanup.call_count, 2)
        self.assertEqual(waits, [60, 60])

    def test_runserver_registers_and_stops_its_cleanup_worker(self):
        from .management.commands.runserver import Command

        self.assertEqual(get_commands()["runserver"], "detector")
        stop, worker = Mock(), Mock()
        with patch("detector.management.commands.runserver.start_cleanup_worker", return_value=(stop, worker)), patch(
            "django.contrib.staticfiles.management.commands.runserver.Command.inner_run",
            side_effect=KeyboardInterrupt,
        ), self.assertRaises(KeyboardInterrupt):
            Command(stdout=StringIO()).inner_run()
        stop.set.assert_called_once()
        worker.join.assert_called_once_with(timeout=5)

    def test_watch_command_runs_worker_and_stops_on_interrupt(self):
        with patch("detector.management.commands.cleanup_history.run_cleanup_loop", side_effect=KeyboardInterrupt) as loop:
            output = StringIO()
            call_command("cleanup_history", watch=True, interval=10, stdout=output)
        self.assertEqual(loop.call_args.args[1], 10)
        self.assertIn("dihentikan", output.getvalue())

    def test_model_loading_failure_records_failed_job_with_finish_time(self):
        buffer = BytesIO()
        document = WordDocument()
        document.add_paragraph("Teks pengujian kegagalan pemuatan model.")
        document.save(buffer)
        upload = SimpleUploadedFile("uji.docx", buffer.getvalue())
        with patch.dict("sys.modules", {"detector.services.antikopas_service": None}):
            response = self.client.post("/api/detect/", {"title": "Uji model", "file": upload}, format="multipart")
        self.assertEqual(response.status_code, 500)
        job = AnalysisJob.objects.get()
        self.assertEqual(job.status, "failed")
        self.assertEqual(job.completed_at, self.now)
        self.assertEqual(job.expires_at, self.now + timedelta(hours=2))


class AutomaticCleanupTests(TransactionTestCase):
    def test_real_background_worker_deletes_expired_files_without_requests(self):
        from .services.history_cleanup import start_cleanup_worker

        with TemporaryDirectory() as temporary, override_settings(
            BASE_DIR=Path(temporary), MEDIA_ROOT=Path(temporary) / "media",
            ANALYSIS_RETENTION_HOURS=2, HISTORY_CLEANUP_INTERVAL_SECONDS=0.01,
        ):
            document = Document.objects.create(
                title="Worker otomatis", original_file=ContentFile(b"uji", name="uji.pdf"),
            )
            job = AnalysisJob.objects.create(
                document=document, status="completed",
                completed_at=timezone.now() - timedelta(hours=3),
            )
            report = Report.objects.create(
                analysis=job, file=ContentFile(b"%PDF-1.4", name="antikopas_report_worker.pdf"),
            )
            upload, pdf = Path(document.original_file.path), Path(report.file.path)
            finished = Event()
            results = []

            def observe_cleanup():
                result = cleanup_expired_analyses()
                results.append(result)
                finished.set()
                return result

            with patch("detector.services.history_cleanup.cleanup_expired_analyses", side_effect=observe_cleanup):
                stop, worker = start_cleanup_worker()
                try:
                    self.assertTrue(finished.wait(timeout=5), "Worker tidak menyelesaikan cleanup.")
                finally:
                    stop.set()
                    worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
            self.assertEqual(results[0]["deleted"], 1)
            self.assertFalse(AnalysisJob.objects.filter(pk=job.pk).exists())
            self.assertFalse(Document.objects.filter(pk=document.pk).exists())
            self.assertFalse(upload.exists())
            self.assertFalse(pdf.exists())
