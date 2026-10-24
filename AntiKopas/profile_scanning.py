
"""
AntiKopas - Profiling Kecepatan Scanning

Mengukur waktu:
1. Ekstraksi PDF
2. Pencarian jurnal OpenAlex + full text
3. Embedding Cloudflare BGE-M3
4. Validasi Academic CrossEncoder V2
5. Total analisis

Tidak mengubah pipeline produksi.
"""

import os
import time
from collections import defaultdict
from pathlib import Path
from functools import wraps

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

import django
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile

from detector.services.document_parser import extract_text
from detector.services import full_pipeline
from detector.services.similarity_index import (
    calculate_similarity_index,
)


PDF_PATH = Path(
    "testing_documents/ANTIKOPAS_DOKUMEN_UJI_SEMANTIK.pdf"
)

DOCUMENT_TITLE = (
    "Pengaruh Penggunaan Artificial Intelligence "
    "terhadap Motivasi Belajar dan Kompetensi "
    "Akademik Mahasiswa"
)

timings = defaultdict(float)
counts = defaultdict(int)


def measure(label, function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        start = time.perf_counter()

        try:
            return function(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            timings[label] += elapsed
            counts[label] += 1

    return wrapped


def main():
    if not PDF_PATH.is_file():
        raise FileNotFoundError(
            f"PDF uji tidak ditemukan: {PDF_PATH}"
        )

    # Pantau setiap query OpenAlex.
    full_pipeline.search_literature = measure(
        "OpenAlex + Full Text",
        full_pipeline.search_literature,
    )

    # Pantau semua panggilan embedding Cloudflare.
    original_encode = (
        full_pipeline.embedding_model.encode
    )

    full_pipeline.embedding_model.encode = measure(
        "Cloudflare BGE-M3",
        original_encode,
    )

    # Pantau proses CrossEncoder.
    original_predict = (
        full_pipeline.cross_encoder.predict
    )

    full_pipeline.cross_encoder.predict = measure(
        "Academic V2",
        original_predict,
    )

    total_start = time.perf_counter()

    print("\n[Profiling] Membaca dokumen PDF...")

    with PDF_PATH.open("rb") as handle:
        uploaded_file = SimpleUploadedFile(
            PDF_PATH.name,
            handle.read(),
            content_type="application/pdf",
        )

    parse_start = time.perf_counter()
    document_text = extract_text(uploaded_file)

    timings["Ekstraksi PDF"] = (
        time.perf_counter() - parse_start
    )
    counts["Ekstraksi PDF"] = 1

    print(
        "[Profiling] Jumlah karakter:",
        len(document_text),
    )

    results = full_pipeline.analyze_with_openalex(
        document_text,
        DOCUMENT_TITLE,
    )

    similarity = calculate_similarity_index(
        results
    )

    total_time = (
        time.perf_counter() - total_start
    )

    print("\n" + "=" * 60)
    print("ANTIKOPAS - HASIL PROFILING")
    print("=" * 60)

    for label in [
        "Ekstraksi PDF",
        "OpenAlex + Full Text",
        "Cloudflare BGE-M3",
        "Academic V2",
    ]:
        print(
            f"{label:25s} : "
            f"{timings[label]:8.2f} detik "
            f"({counts[label]} panggilan)"
        )

    print("-" * 60)

    print(
        f"{'Total scanning':25s} : "
        f"{total_time:8.2f} detik"
    )

    print(
        "Similarity Index        :",
        similarity["similarity_index"],
    )

    print(
        "Total chunks            :",
        similarity["total_chunks"],
    )

    print(
        "Matched chunks          :",
        similarity["matched_chunks"],
    )

    print("=" * 60)

    slowest = max(
        [
            "Ekstraksi PDF",
            "OpenAlex + Full Text",
            "Cloudflare BGE-M3",
            "Academic V2",
        ],
        key=lambda label: timings[label],
    )

    print(
        "\nTAHAP TERLAMA:",
        slowest,
    )


if __name__ == "__main__":
    main()
