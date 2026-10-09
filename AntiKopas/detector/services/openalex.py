
"""
AntiKopas - OpenAlex Full-Text Retrieval
STEP 5A

Fitur:
- Search OpenAlex
- Reconstruct abstract
- Cari lokasi PDF open-access
- Download PDF dengan batas ukuran dan timeout
- Ekstraksi seluruh halaman PDF yang memenuhi batas
- Fallback ke abstract
- Metadata text_scope untuk membedakan sumber
- Cache hasil unduhan
- Kompatibel dengan full_pipeline.py

Catatan:
Field "text" berisi:
- full text, jika PDF berhasil diekstrak
- abstract, jika full text tidak tersedia

Pengambilan full text dibatasi pada beberapa
kandidat per pencarian supaya aplikasi ringan.
"""

import io
import ipaddress
import logging
import os
import re
import socket
import time

from functools import lru_cache
from urllib.parse import urljoin, urlsplit

import requests

from dotenv import load_dotenv


# ==========================================
# 1. KONFIGURASI
# ==========================================

load_dotenv()

logger = logging.getLogger(__name__)

OPENALEX_URL = (
    "https://api.openalex.org/works"
)

OPENALEX_API_KEY = os.getenv(
    "OPENALEX_API_KEY"
)

# Batas agar tidak membebani laptop.
MAX_FULLTEXT_WORKS_PER_SEARCH = 2
MAX_PDF_URLS_PER_WORK = 2

# Maksimum ukuran PDF: 6 MB.
MAX_PDF_BYTES = 6 * 1024 * 1024

# Hanya ekstrak PDF sampai 35 halaman.
# PDF lebih panjang memakai fallback abstract.
MAX_PDF_PAGES = 35

# Menolak dokumen yang terlalu besar
# untuk pipeline embedding lokal.
MAX_FULLTEXT_CHARACTERS = 120000

MIN_FULLTEXT_WORDS = 120

CONNECT_TIMEOUT = 5
READ_TIMEOUT = 12

MAX_REDIRECTS = 4

PDF_HEADERS = {
    "User-Agent": (
        "AntiKopas/1.0 Academic Research"
    ),
    "Accept": "application/pdf,*/*",
}


# ==========================================
# 2. ABSTRACT RECONSTRUCTION
# ==========================================

def reconstruct_abstract(inverted_index):
    if not isinstance(
        inverted_index,
        dict,
    ):
        return ""

    positions = []

    for word, indexes in (
        inverted_index.items()
    ):
        if not isinstance(indexes, list):
            continue

        for index in indexes:
            if isinstance(index, int):
                positions.append(
                    (index, word)
                )

    positions.sort(
        key=lambda item: item[0]
    )

    return " ".join(
        word
        for _, word in positions
    )


# ==========================================
# 3. CLEAN QUERY
# ==========================================

def clean_search_query(query):
    if not query:
        return ""

    query = re.sub(
        r"\s+",
        " ",
        str(query),
    ).strip()

    query = re.sub(
        r'[“”‘’"<>]',
        " ",
        query,
    )

    query = re.sub(
        r"\s+",
        " ",
        query,
    ).strip()

    words = query.split()

    return " ".join(
        words[:12]
    )


# ==========================================
# 4. VALIDASI URL PDF
# ==========================================

def is_safe_public_url(url):
    """
    Mengurangi risiko akses ke alamat
    internal/lokal melalui URL PDF.

    Ini pengamanan dasar, bukan sandbox
    jaringan yang sempurna.
    """

    try:
        parsed = urlsplit(
            str(url or "").strip()
        )

        if parsed.scheme.lower() not in (
            "https",
            "http",
        ):
            return False

        if (
            not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            return False

        # Batasi port.
        if parsed.port not in (
            None,
            80,
            443,
        ):
            return False

        hostname = (
            parsed.hostname
            .strip(".")
            .lower()
        )

        if (
            hostname == "localhost"
            or hostname.endswith(".localhost")
            or hostname.endswith(".local")
            or hostname.endswith(".internal")
        ):
            return False

        try:
            ip = ipaddress.ip_address(
                hostname
            )

            return ip.is_global

        except ValueError:
            pass

        # Periksa resolusi DNS.
        addresses = socket.getaddrinfo(
            hostname,
            parsed.port or (
                443
                if parsed.scheme == "https"
                else 80
            ),
            type=socket.SOCK_STREAM,
        )

        if not addresses:
            return False

        for address in addresses:
            ip_text = address[4][0]

            ip = ipaddress.ip_address(
                ip_text
            )

            if not ip.is_global:
                return False

        return True

    except (
        ValueError,
        OSError,
        TypeError,
    ):
        return False


# ==========================================
# 5. AMBIL LOKASI PDF OPEN ACCESS
# ==========================================

def get_open_access_pdf_urls(work):
    """
    Prioritas:
    1. best_oa_location
    2. primary_location jika open access
    3. locations[] jika open access

    Hanya menggunakan direct PDF URLs.
    Tidak scraping halaman publisher.
    """

    locations = []

    best_oa = work.get(
        "best_oa_location"
    )

    if isinstance(best_oa, dict):
        locations.append(best_oa)

    primary = work.get(
        "primary_location"
    )

    if isinstance(primary, dict):
        locations.append(primary)

    for location in (
        work.get("locations") or []
    ):
        if isinstance(location, dict):
            locations.append(location)

    urls = []
    seen = set()

    for location in locations:
        if location.get("is_oa") is not True:
            continue

        pdf_url = str(
            location.get("pdf_url") or ""
        ).strip()

        if not pdf_url:
            continue

        if pdf_url in seen:
            continue

        if not is_safe_public_url(pdf_url):
            continue

        seen.add(pdf_url)
        urls.append(pdf_url)

    return urls[
        :MAX_PDF_URLS_PER_WORK
    ]


# ==========================================
# 6. DOWNLOAD PDF
# ==========================================

def download_pdf_bytes(pdf_url):
    """
    Mengunduh PDF secara streaming.

    Tidak menyimpan file secara permanen.
    Menolak:
    - URL tidak aman
    - Redirect ke alamat internal
    - File terlalu besar
    - Respons bukan PDF
    """

    current_url = pdf_url

    for _ in range(
        MAX_REDIRECTS + 1
    ):
        if not is_safe_public_url(
            current_url
        ):
            logger.warning(
                "[FullText] URL PDF ditolak"
            )
            return None

        try:
            with requests.get(
                current_url,
                headers=PDF_HEADERS,
                timeout=(
                    CONNECT_TIMEOUT,
                    READ_TIMEOUT,
                ),
                stream=True,
                allow_redirects=False,
            ) as response:

                if response.status_code in (
                    301, 302, 303, 307, 308
                ):
                    redirect_url = (
                        response.headers.get(
                            "Location"
                        )
                    )

                    if not redirect_url:
                        return None

                    current_url = urljoin(
                        current_url,
                        redirect_url,
                    )

                    continue

                if response.status_code != 200:
                    logger.info(
                        "[FullText] HTTP %s",
                        response.status_code,
                    )
                    return None

                content_length = (
                    response.headers.get(
                        "Content-Length"
                    )
                )

                if content_length:
                    try:
                        if int(
                            content_length
                        ) > MAX_PDF_BYTES:
                            logger.info(
                                "[FullText] PDF terlalu besar"
                            )
                            return None
                    except ValueError:
                        pass

                buffer = io.BytesIO()
                downloaded = 0

                for block in (
                    response.iter_content(
                        chunk_size=65536
                    )
                ):
                    if not block:
                        continue

                    downloaded += len(block)

                    if downloaded > MAX_PDF_BYTES:
                        logger.info(
                            "[FullText] Download melewati batas"
                        )
                        return None

                    buffer.write(block)

                pdf_data = buffer.getvalue()

                # Validasi magic bytes.
                # Jangan percaya Content-Type saja.
                if not pdf_data.lstrip().startswith(
                    b"%PDF-"
                ):
                    logger.info(
                        "[FullText] Respons bukan PDF"
                    )
                    return None

                return pdf_data

        except requests.RequestException:
            logger.info(
                "[FullText] Gagal mengambil PDF",
                exc_info=False,
            )
            return None

    logger.info(
        "[FullText] Terlalu banyak redirect"
    )

    return None


# ==========================================
# 7. EKSTRAKSI TEKS PDF
# ==========================================

def normalize_pdf_text(text):
    text = str(text or "")

    # Soft hyphen.
    text = text.replace(
        "\u00ad",
        "",
    )

    # Gabungkan kata yang terpisah
    # oleh akhir baris PDF.
    text = re.sub(
        r"(?<=\w)-[ \t]*\n[ \t]*(?=\w)",
        "",
        text,
    )

    # Hilangkan karakter kontrol.
    text = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f]",
        " ",
        text,
    )

    return " ".join(
        text.split()
    )


def extract_pdf_fulltext(pdf_data):
    """
    Ekstrak seluruh halaman jika PDF
    memenuhi batas halaman dan ukuran teks.

    PDF hasil scan gambar tidak di-OCR.
    """

    try:
        import fitz
    except ImportError:
        logger.warning(
            "[FullText] PyMuPDF belum terpasang. "
            "Jalankan: pip install pymupdf"
        )
        return None

    try:
        document = fitz.open(
            stream=pdf_data,
            filetype="pdf",
        )

        try:
            page_count = len(document)

            if page_count == 0:
                return None

            if page_count > MAX_PDF_PAGES:
                logger.info(
                    "[FullText] PDF %s halaman "
                    "melebihi batas %s",
                    page_count,
                    MAX_PDF_PAGES,
                )
                return None

            pages = []
            total_characters = 0

            for page in document:
                page_text = (
                    page.get_text(
                        "text"
                    ) or ""
                )

                total_characters += len(
                    page_text
                )

                if (
                    total_characters
                    > MAX_FULLTEXT_CHARACTERS
                ):
                    logger.info(
                        "[FullText] Teks PDF terlalu panjang"
                    )
                    return None

                pages.append(page_text)

        finally:
            document.close()

        full_text = normalize_pdf_text(
            "\n".join(pages)
        )

        if (
            len(full_text.split())
            < MIN_FULLTEXT_WORDS
        ):
            logger.info(
                "[FullText] Teks PDF terlalu sedikit "
                "atau berupa scan gambar"
            )
            return None

        return {
            "text": full_text,
            "pages": page_count,
        }

    except Exception:
        logger.info(
            "[FullText] Ekstraksi PDF gagal",
            exc_info=False,
        )
        return None


# ==========================================
# 8. CACHE FULL TEXT
# ==========================================

@lru_cache(maxsize=16)
def retrieve_pdf_text(pdf_url):
    pdf_data = download_pdf_bytes(
        pdf_url
    )

    if not pdf_data:
        return None

    return extract_pdf_fulltext(
        pdf_data
    )


# ==========================================
# 9. FULL TEXT UNTUK SATU JURNAL
# ==========================================

def get_work_fulltext(work):
    """
    Mencoba beberapa lokasi OA.
    Berhenti saat satu PDF berhasil.
    """

    pdf_urls = get_open_access_pdf_urls(
        work
    )

    for pdf_url in pdf_urls:
        result = retrieve_pdf_text(
            pdf_url
        )

        if not result:
            continue

        return {
            "text": result["text"],
            "pages": result["pages"],
            "pdf_url": pdf_url,
        }

    return None


# ==========================================
# 10. SEARCH OPENALEX
# ==========================================

def search_literature(
    query,
    per_page=10,
):
    clean_query = clean_search_query(
        query
    )

    if len(clean_query) < 5:
        return []

    params = {
        "search": clean_query,
        "per_page": max(
            1,
            min(int(per_page), 100),
        ),
    }

    if OPENALEX_API_KEY:
        params["api_key"] = (
            OPENALEX_API_KEY
        )

    for attempt in range(3):
        try:
            response = requests.get(
                OPENALEX_URL,
                params=params,
                timeout=20,
            )

            if response.status_code == 200:
                data = response.json()

                results = []
                raw_works = data.get(
                    "results",
                    [],
                )

                # --------------------------------
                # A. KUMPULKAN METADATA + ABSTRACT
                # --------------------------------

                for work in raw_works:
                    if not isinstance(work, dict):
                        continue

                    abstract = reconstruct_abstract(
                        work.get(
                            "abstract_inverted_index"
                        )
                    )

                    primary_location = (
                        work.get(
                            "primary_location"
                        ) or {}
                    )

                    if not isinstance(
                        primary_location,
                        dict,
                    ):
                        primary_location = {}

                    results.append({
                        "source_id": work.get("id"),
                        "title": work.get(
                            "display_name"
                        ),
                        "year": work.get(
                            "publication_year"
                        ),
                        "doi": work.get("doi"),
                        "url": (
                            primary_location.get(
                                "landing_page_url"
                            )
                            or work.get("doi")
                        ),

                        # Kompatibel dengan
                        # pipeline sebelumnya.
                        "text": abstract,

                        # Metadata tambahan.
                        "abstract": abstract,
                        "text_scope": "abstract",
                        "fulltext_url": None,
                        "fulltext_pages": 0,
                        "fulltext_status": (
                            "abstract_only"
                        ),
                    })

                # --------------------------------
                # B. UPGRADE KE FULL TEXT
                # --------------------------------

                attempted_works = 0
                successful_works = 0

                result_index = 0

                for work in raw_works:
                    if not isinstance(work, dict):
                        continue

                    if result_index >= len(results):
                        break

                    source = results[result_index]
                    result_index += 1

                    if (
                        attempted_works
                        >= MAX_FULLTEXT_WORKS_PER_SEARCH
                    ):
                        break

                    pdf_urls = (
                        get_open_access_pdf_urls(
                            work
                        )
                    )

                    if not pdf_urls:
                        continue

                    attempted_works += 1

                    fulltext_result = None

                    for pdf_url in pdf_urls:
                        extracted = retrieve_pdf_text(
                            pdf_url
                        )

                        if not extracted:
                            continue

                        fulltext_result = {
                            "text": extracted["text"],
                            "pages": extracted["pages"],
                            "pdf_url": pdf_url,
                        }

                        break

                    if not fulltext_result:
                        source[
                            "fulltext_status"
                        ] = "download_or_extract_failed"
                        continue

                    # "text" sekarang diisi
                    # isi jurnal yang dibaca.
                    source["text"] = (
                        fulltext_result["text"]
                    )

                    source["text_scope"] = (
                        "full_text"
                    )

                    source["fulltext_url"] = (
                        fulltext_result["pdf_url"]
                    )

                    source["fulltext_pages"] = (
                        fulltext_result["pages"]
                    )

                    source["fulltext_status"] = (
                        "pdf_extracted"
                    )

                    successful_works += 1

                logger.info(
                    "[OpenAlex FullText] "
                    "Ditemukan: %s | "
                    "Percobaan PDF: %s | "
                    "Full text berhasil: %s | "
                    "Abstrak/fallback: %s",
                    len(results),
                    attempted_works,
                    successful_works,
                    len(results) - successful_works,
                )

                print(
                    "[OpenAlex FullText] "
                    f"Kandidat: {len(results)} | "
                    f"Dicoba: {attempted_works} | "
                    f"Berhasil: {successful_works}"
                )

                return results

            if response.status_code in (
                429, 500, 502, 503, 504
            ):
                logger.warning(
                    "OpenAlex gagal sementara: "
                    "HTTP %s (percobaan %s/3)",
                    response.status_code,
                    attempt + 1,
                )

                if attempt < 2:
                    time.sleep(
                        2 ** attempt
                    )

                continue

            # Hindari mencetak URL berisi API key.
            logger.error(
                "OpenAlex menolak request: HTTP %s",
                response.status_code,
            )

            return []

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ):
            logger.warning(
                "Koneksi OpenAlex gagal "
                "(percobaan %s/3)",
                attempt + 1,
            )

            if attempt < 2:
                time.sleep(
                    2 ** attempt
                )

        except (
            ValueError,
            TypeError,
            KeyError,
        ):
            logger.error(
                "Respons OpenAlex tidak valid"
            )

            return []

    logger.error(
        "OpenAlex tidak tersedia setelah "
        "3 percobaan"
    )

    return []
