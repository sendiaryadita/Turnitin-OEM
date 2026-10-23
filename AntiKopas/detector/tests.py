from io import BytesIO

from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from .models import AnalysisJob, Document, Report
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

    # ==================================================
    # PENGUJIAN KEAMANAN AKSES ANTAR-USER
    # ==================================================

    def test_user_cannot_access_other_users_analysis(self):
        self.authenticate()

        other_user = User.objects.create_user(
            username="other_api_user",
            password="Strong-Other-Test-Password-2026!",
        )

        document = Document.objects.create(
            uploaded_by=other_user,
            title="Dokumen pengguna lain",
            original_file=ContentFile(
                b"Dokumen rahasia",
                name="dokumen_uji.txt"
            ),
            file_type="text/plain",
            file_size=15,
        )

        job = AnalysisJob.objects.create(
            document=document,
            status=AnalysisJob.Status.COMPLETED,
        )

        # 1. Tidak boleh melihat riwayat pengguna lain.
        listing = self.client.get("/api/analyses/")

        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json()["count"], 0)

        # 2. Statistik hanya menghitung data sendiri.
        stats = self.client.get("/api/analyses/stats/")

        self.assertEqual(stats.status_code, 200)
        self.assertEqual(stats.json()["total_analyses"], 0)

        # 3. Tidak boleh membuka detail pengguna lain.
        detail = self.client.get(
            f"/api/analyses/{job.id}/"
        )

        self.assertEqual(detail.status_code, 404)

        # 4. Tidak boleh mengubah judul pengguna lain.
        rename = self.client.patch(
            f"/api/analyses/{job.id}/",
            {"title": "Judul diubah"},
            content_type="application/json",
        )

        self.assertEqual(rename.status_code, 404)

        # 5. Tidak boleh menghapus analisis pengguna lain.
        deletion = self.client.delete(
            f"/api/analyses/{job.id}/"
        )

        self.assertEqual(deletion.status_code, 404)

        # 6. Pastikan data pengguna lain tetap tersimpan.
        self.assertTrue(
            AnalysisJob.objects.filter(pk=job.id).exists()
        )

        self.assertEqual(
            Document.objects.get(pk=document.id).title,
            "Dokumen pengguna lain"
        )

            # ==================================================
    # PENGUJIAN KEAMANAN DOWNLOAD LAPORAN PDF
    # ==================================================

    def test_report_cannot_be_accessed_by_other_users(self):
        self.authenticate()

        other_user = User.objects.create_user(
            username="report_owner",
            password="Strong-Report-Test-Password-2026!",
        )

        document = Document.objects.create(
            uploaded_by=other_user,
            title="Laporan pribadi",
            original_file="documents/test_report.pdf",
            file_type="application/pdf",
            file_size=100,
        )

        job = AnalysisJob.objects.create(
            document=document,
            status=AnalysisJob.Status.COMPLETED,
        )

        filename = "antikopas_report_access_test.pdf"

        Report.objects.create(
            analysis=job,
            file=f"reports/2026/10/{filename}",
        )

        # Gunakan folder sementara agar tidak mengubah
        # laporan asli milik pengguna.
        with TemporaryDirectory() as temporary:
            report_directory = Path(temporary) / "reports"
            report_directory.mkdir()

            report_file = report_directory / filename
            report_file.write_bytes(b"%PDF-1.4\n%%EOF")

            with override_settings(BASE_DIR=Path(temporary)):
                report_url = f"/api/reports/{filename}/"

                # 1. Pengunjung tanpa login harus ditolak.
                anonymous_response = Client().get(report_url)

                self.assertEqual(
                    anonymous_response.status_code,
                    401,
                )

                # 2. User lain tidak boleh mengakses PDF.
                denied_response = self.client.get(report_url)

                self.assertEqual(
                    denied_response.status_code,
                    404,
                )

                # 3. Login menggunakan akun pemilik laporan.
                owner_client = Client()

                login_response = owner_client.post(
                    "/api/auth/token/",
                    {
                        "username": "report_owner",
                        "password": "Strong-Report-Test-Password-2026!",
                    },
                )

                self.assertEqual(login_response.status_code, 200)

                owner_client.defaults["HTTP_AUTHORIZATION"] = (
                    "Bearer " + login_response.json()["access"]
                )

                # 4. Pemilik laporan harus dapat mengunduh PDF.
                allowed_response = owner_client.get(report_url)

                self.assertEqual(
                    allowed_response.status_code,
                    200,
                )

                self.assertEqual(
                    allowed_response["Content-Type"],
                    "application/pdf",
                )

                allowed_response.close()

                    # ==================================================
    # PENGUJIAN HAK AKSES ADMINISTRATOR
    # ==================================================

    def test_normal_user_cannot_access_django_admin(self):
        user_client = Client()
        user_client.force_login(self.user)

        response = user_client.get("/admin/")

        # Pengguna biasa diarahkan ke halaman login admin.
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_superuser_can_access_django_admin(self):
        admin_user = User.objects.create_superuser(
            username="admin_test",
            password="Strong-Admin-Test-Password-2026!",
        )

        admin_client = Client()
        admin_client.force_login(admin_user)

        response = admin_client.get("/admin/")

        self.assertEqual(response.status_code, 200)

    # ==================================================
    # PENGUJIAN IDENTITAS DAN ROLE PENGGUNA
    # ==================================================

    def test_current_user_returns_correct_roles(self):
        # 1. Periksa identitas pengguna biasa.
        self.authenticate()

        user_response = self.client.get("/api/auth/me/")

        self.assertEqual(user_response.status_code, 200)
        self.assertEqual(user_response.json()["user"]["role"], "user")
        self.assertFalse(user_response.json()["user"]["is_staff"])

        # 2. Buat administrator khusus pengujian.
        User.objects.create_superuser(
            username="role_admin_test",
            password="Strong-Role-Test-Password-2026!",
        )

        admin_client = Client()

        admin_login = admin_client.post(
            "/api/auth/token/",
            {
                "username": "role_admin_test",
                "password": "Strong-Role-Test-Password-2026!",
            },
        )

        self.assertEqual(admin_login.status_code, 200)

        admin_client.defaults["HTTP_AUTHORIZATION"] = (
            "Bearer " + admin_login.json()["access"]
        )

        # 3. Periksa identitas administrator.
        admin_response = admin_client.get("/api/auth/me/")

        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(admin_response.json()["user"]["role"], "admin")
        self.assertTrue(admin_response.json()["user"]["is_staff"])
        self.assertTrue(admin_response.json()["user"]["is_superuser"])