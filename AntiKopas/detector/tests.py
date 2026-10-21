from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from .models import AnalysisJob, Document
from .services.document_parser import extract_text
from docx import Document as WordDocument


class BackendApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="api_test_user",
            password="Temporary-Test-Password-2026!",
        )

    def authenticate(self):
        login = self.client.post(
            "/api/auth/token/",
            {
                "username": "api_test_user",
                "password": "Temporary-Test-Password-2026!",
            },
        )
        self.client.defaults["HTTP_AUTHORIZATION"] = (
            "Bearer " + login.json()["access"]
        )

    def test_health_is_public(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_docx_parser_is_supported(self):
        buffer = BytesIO()
        word_document = WordDocument()
        word_document.add_paragraph("Teks dokumen Word untuk pengujian")
        word_document.save(buffer)
        buffer.seek(0)
        buffer.name = "uji.docx"
        text = extract_text(buffer)
        self.assertIn("Teks dokumen Word", text)

    def test_frontend_origin_is_allowed(self):
        response = self.client.get(
            "/api/health/",
            HTTP_ORIGIN="http://localhost:5173",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://localhost:5173",
        )

    def test_user_can_register(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "new_api_user",
                "password": "Strong-Registration-Password-2026!",
                "password_confirm": "Strong-Registration-Password-2026!",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username="new_api_user").exists())

    def test_analysis_requires_authentication(self):
        response = self.client.get("/api/analyses/")
        self.assertEqual(response.status_code, 401)

    def test_login_and_access_analysis(self):
        login = self.client.post(
            "/api/auth/token/",
            {
                "username": "api_test_user",
                "password": "Temporary-Test-Password-2026!",
            },
        )
        self.assertEqual(login.status_code, 200)
        self.client.defaults["HTTP_AUTHORIZATION"] = (
            "Bearer " + login.json()["access"]
        )
        response = self.client.get("/api/analyses/")
        self.assertEqual(response.status_code, 200)

    def test_detect_validates_required_fields(self):
        self.authenticate()
        response = self.client.post("/api/detect/", {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "title wajib dikirim")

    def test_detect_rejects_unsupported_file_extension(self):
        self.authenticate()
        upload = SimpleUploadedFile(
            "uji.txt",
            b"Isi dokumen pengujian",
            content_type="text/plain",
        )
        response = self.client.post(
            "/api/detect/",
            {"title": "Dokumen uji", "file": upload},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Format file tidak didukung", response.json()["message"])

    def test_detect_rejects_file_larger_than_limit(self):
        self.authenticate()
        upload = SimpleUploadedFile(
            "uji.pdf",
            b"0" * (25 * 1024 * 1024 + 1),
            content_type="application/pdf",
        )
        response = self.client.post(
            "/api/detect/",
            {"title": "Dokumen uji", "file": upload},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("25 MB", response.json()["message"])

    def test_detect_rejects_file_with_invalid_pdf_content(self):
        self.authenticate()
        upload = SimpleUploadedFile(
            "palsu.pdf",
            b"Ini bukan isi PDF",
            content_type="application/pdf",
        )
        response = self.client.post(
            "/api/detect/",
            {"title": "Dokumen uji", "file": upload},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("format PDF", response.json()["message"])

    def test_analysis_list_and_detail(self):
        self.authenticate()
        document = Document.objects.create(
            uploaded_by=self.user,
            title="Dokumen pengujian",
            original_file=ContentFile(b"uji", name="uji.txt"),
            file_type="text/plain",
            file_size=3,
        )
        job = AnalysisJob.objects.create(
            document=document,
            status=AnalysisJob.Status.COMPLETED,
            total_chunks=1,
            matched_chunks=0,
            similarity_index=0,
        )
        listing = self.client.get("/api/analyses/")
        detail = self.client.get(f"/api/analyses/{job.id}/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["id"], job.id)

    def test_analysis_can_be_deleted(self):
        self.authenticate()
        document = Document.objects.create(
            uploaded_by=self.user,
            title="Dokumen hapus",
            original_file=ContentFile(b"hapus", name="hapus.txt"),
            file_type="text/plain",
            file_size=5,
        )
        job = AnalysisJob.objects.create(document=document)
        response = self.client.delete(f"/api/analyses/{job.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AnalysisJob.objects.filter(pk=job.id).exists())

    def test_analysis_can_be_renamed_and_stats_are_available(self):
        self.authenticate()
        document = Document.objects.create(
            uploaded_by=self.user,
            title="Judul lama",
            original_file=ContentFile(b"uji", name="uji.txt"),
            file_type="text/plain",
            file_size=3,
        )
        job = AnalysisJob.objects.create(
            document=document,
            status=AnalysisJob.Status.COMPLETED,
            total_chunks=4,
            matched_chunks=1,
            similarity_index=25,
        )
        renamed = self.client.patch(
            f"/api/analyses/{job.id}/",
            {"title": "Judul baru"},
            content_type="application/json",
        )
        stats = self.client.get("/api/analyses/stats/")
        listing = self.client.get("/api/analyses/?q=Judul%20baru&page_size=1")
        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(stats.status_code, 200)
        self.assertEqual(stats.json()["total_analyses"], 1)
        self.assertEqual(listing.json()["results"][0]["title"], "Judul baru")
