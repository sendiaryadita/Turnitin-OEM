
"""
AK_08.1 - Audit Full Text Jurnal AntiKopas

Tujuan:
1. Mengambil metadata satu jurnal dari OpenAlex.
2. Memeriksa apakah URL PDF open access tersedia.
3. Mencoba membaca PDF melalui openalex.py yang ada.
4. Memeriksa apakah teks hasil ekstraksi mencakup isi jurnal.

Tidak menggunakan BGE-M3 atau Academic V2.
Tidak mengubah backend produksi.
"""

import os
import re
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from detector.services.openalex import (
    reconstruct_abstract,
    get_open_access_pdf_urls,
    get_work_fulltext,
    MAX_FULLTEXT_WORKS_PER_SEARCH,
    MAX_PDF_PAGES,
    MAX_PDF_BYTES,
)


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Jurnal dari hasil pengujian AntiKopas sebelumnya.
# Boleh diganti ke DOI jurnal lain pada tes berikutnya.
TEST_DOI = "10.59944/amorti.v5i2.861"

OPENALEX_URL = (
    "https://api.openalex.org/works/"
    f"https://doi.org/{TEST_DOI}"
)


def line():
    print("=" * 65)


def compact(text):
    return " ".join(str(text or "").split())


def get_openalex_work():
    print("\n[1] Menghubungi OpenAlex...")

    params = {}

    api_key = os.getenv("OPENALEX_API_KEY", "").strip()

    if api_key:
        params["api_key"] = api_key

    try:
        response = requests.get(
            OPENALEX_URL,
            params=params,
            timeout=(10, 30),
        )
    except requests.RequestException as error:
        print(
            "GAGAL: Koneksi OpenAlex:",
            type(error).__name__,
        )
        return None

    print("HTTP Status:", response.status_code)

    if response.status_code != 200:
        print(
            "GAGAL: Jurnal tidak berhasil diambil "
            "dari OpenAlex."
        )
        print(
            "Periksa DOI, API key, dan koneksi."
        )
        return None

    try:
        work = response.json()
    except ValueError:
        print("GAGAL: Respons bukan JSON.")
        return None

    if not isinstance(work, dict):
        print("GAGAL: Format jurnal tidak valid.")
        return None

    return work


def audit():
    line()
    print("ANTIKOPAS - AUDIT FULL TEXT JURNAL")
    print("Backlog: AK_08.1")
    line()

    print("DOI:", TEST_DOI)
    print(
        "Batas PDF per pencarian:",
        MAX_FULLTEXT_WORKS_PER_SEARCH,
    )
    print(
        "Maksimal halaman:",
        MAX_PDF_PAGES,
    )
    print(
        "Maksimal ukuran PDF:",
        MAX_PDF_BYTES // (1024 * 1024),
        "MB",
    )

    work = get_openalex_work()

    if work is None:
        return

    title = compact(work.get("display_name"))
    abstract = reconstruct_abstract(
        work.get("abstract_inverted_index")
    )

    print("\n[2] METADATA JURNAL")
    print("Judul:", title)
    print("Tahun:", work.get("publication_year"))
    print("Open Access:", work.get("open_access"))
    print("Panjang abstrak:", len(abstract.split()), "kata")

    locations = work.get("locations") or []
    print("Jumlah lokasi OpenAlex:", len(locations))

    raw_pdf_urls = []

    for location in locations:
        if not isinstance(location, dict):
            continue

        pdf_url = location.get("pdf_url")

        if pdf_url:
            raw_pdf_urls.append(pdf_url)

    print(
        "Lokasi yang mencantumkan URL PDF:",
        len(raw_pdf_urls),
    )

    print("\n[3] PEMERIKSAAN PDF OPEN ACCESS")

    pdf_urls = get_open_access_pdf_urls(work)

    print(
        "URL PDF yang diterima sistem:",
        len(pdf_urls),
    )

    for index, url in enumerate(pdf_urls, start=1):
        print(f"PDF #{index}: {url}")

    if not pdf_urls:
        print()
        print("HASIL: BELUM ADA PDF YANG BISA DICOBA.")
        print(
            "OpenAlex mungkin hanya menyediakan abstrak, "
            "atau URL PDF tidak lolos pemeriksaan."
        )
        print(
            "Ini tidak berarti PDF jurnal pasti "
            "tidak tersedia di situs penerbit."
        )
        return

    print("\n[4] MENCOBA EKSTRAKSI FULL TEXT")

    start = time.perf_counter()

    result = get_work_fulltext(work)

    elapsed = time.perf_counter() - start

    print(
        "Waktu percobaan:",
        f"{elapsed:.2f}",
        "detik",
    )

    if not result:
        print()
        print("HASIL: FULL TEXT GAGAL DIEKSTRAK.")
        print(
            "Kemungkinan: PDF gagal diunduh, "
            "terlalu besar, melebihi batas halaman, "
            "atau teks tidak dapat dibaca."
        )
        print(
            "Perlu diperiksa lebih lanjut pada "
            "AK_08.2 dan AK_08.3."
        )
        return

    text = compact(result.get("text"))
    pages = result.get("pages", 0)
    pdf_url = result.get("pdf_url", "")

    print()
    line()
    print("HASIL AUDIT FULL TEXT")
    line()

    print("Status: BERHASIL")
    print("Jumlah halaman PDF:", pages)
    print("Jumlah kata:", len(text.split()))
    print("Jumlah karakter:", len(text))
    print("Sumber PDF:", pdf_url)

    print("\n[5] PEMERIKSAAN BAGIAN ISI")

    keywords = [
        "pendahuluan",
        "metode",
        "hasil dan pembahasan",
        "pembahasan",
        "kesimpulan",
        "daftar pustaka",
    ]

    for keyword in keywords:
        found = bool(
            re.search(
                rf"\b{re.escape(keyword)}\b",
                text,
                flags=re.IGNORECASE,
            )
        )

        print(
            f"{keyword:22s}:",
            "DITEMUKAN" if found else "TIDAK TERDETEKSI",
        )

    # Tampilkan cuplikan dari tengah dokumen
    # agar tidak hanya melihat halaman awal.
    middle = len(text) // 2

    excerpt = text[
        max(0, middle - 250):
        min(len(text), middle + 450)
    ]

    print("\n[6] CONTOH TEKS BAGIAN TENGAH PDF")
    print("-" * 65)
    print(excerpt)
    print("-" * 65)

    print("\nKESIMPULAN AWAL:")
    print(
        "Parser berhasil mengambil teks dari PDF. "
        "Periksa cuplikan di atas untuk memastikan "
        "isi jurnal benar-benar ikut terbaca."
    )
    print(
        "Nama bagian yang terdeteksi belum "
        "merupakan bukti lokasi halaman yang akurat."
    )

    line()


if __name__ == "__main__":
    audit()
