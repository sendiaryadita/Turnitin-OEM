"""Verifikasi isi dan pagination laporan tanpa menjalankan model AI."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from pypdf import PdfReader

from .services.report_generator import generate_report


class ReportLayoutTests(TestCase):
    def test_zero_result_is_one_page_and_does_not_invent_categories(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "zero.pdf"
            generate_report(path, "Dokumen <uji> & hasil", 0, 37, 0, [])
            pdf = PdfReader(path)
            text = "\n".join(page.extract_text() for page in pdf.pages)
            self.assertEqual(len(pdf.pages), 1)
            self.assertIn("0.00%", text)
            self.assertIn("Dokumen <uji> & hasil", text)
            self.assertIn("Halaman 1 dari 1", text)
            for invented in ["STUDENT PAPERS", "INTERNET SOURCES", "Terverifikasi Digital"]:
                self.assertNotIn(invented, text)
            for technical in ["SEGMEN", "INFORMASI PEMERIKSAAN", "BASIS INDEKS", "EMBEDDING", "OPENALEX", "BGE-M3"]:
                self.assertNotIn(technical, text.upper())

    def test_source_colors_numbers_evidence_and_links_stay_connected(self):
        source = {"title": "Sumber <A>", "doi": "https://example.org/source-a", "year": 2026}
        chunks = [{"chunk_index": 2, "chunk_text": "Bukti dokumen yang benar.", "matches": [{
            **source, "matched": True, "source_excerpt": "Bukti sumber yang benar.",
            "embedding_model": "cloudflare-bge-m3", "cross_score": 3.2, "text_scope": "abstract",
        }]}]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.pdf"
            generate_report(path, "Dokumen", 0.25, 4, 1, [source], [
                {**source, "similarity_percentage": 25},
            ], chunks)
            pdf = PdfReader(path)
            self.assertEqual(len(pdf.pages), 2)
            summary, evidence = [page.extract_text() for page in pdf.pages]
            self.assertIn("25.00%", summary)
            self.assertIn("[1]", evidence)
            self.assertIn("Bukti dokumen yang benar.", evidence)
            self.assertIn("Bukti sumber yang benar.", evidence)
            self.assertIn("CUPLIKAN SUMBER [1]", evidence)
            self.assertNotIn("SEGMEN", evidence)
            for number, page in enumerate(pdf.pages, 1):
                self.assertIn(f"Halaman {number} dari 2", page.extract_text())
            links = [a.get_object().get("/A", {}).get("/URI")
                     for page in pdf.pages for a in page.get("/Annots", [])]
            self.assertIn(source["doi"], links)

    def test_many_sources_and_long_evidence_can_flow_across_pages(self):
        sources = [{"title": f"Sumber {i}", "url": f"https://example.org/{i}"} for i in range(20)]
        chunks = [{"chunk_index": 1, "chunk_text": "Bukti panjang. " * 400, "matches": [{
            **sources[0], "matched": True, "source_excerpt": "Sumber panjang. " * 400,
        }]}]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "long.pdf"
            generate_report(path, "Judul panjang " * 40, 0.5, 2, 1, sources, chunks=chunks)
            pdf = PdfReader(path)
            self.assertGreater(len(pdf.pages), 2)
            text = "\n".join(page.extract_text() for page in pdf.pages)
            self.assertIn("Sumber 19", text)
            self.assertIn("Bukti panjang.", text)
            self.assertIn("Sumber panjang.", text)
            for number, page in enumerate(pdf.pages, 1):
                self.assertIn(f"Halaman {number} dari {len(pdf.pages)}", page.extract_text())
