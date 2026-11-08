
import re
import unicodedata

from .full_pipeline import analyze_with_openalex
from .similarity_index import calculate_similarity_index


def _report_analysis_progress(
    progress_callback,
    percent,
    stage,
    message=None,
):
    """Laporkan tahapan layanan tanpa mengganggu analisis utama."""
    if not callable(progress_callback):
        return

    try:
        payload = {
            "percent": max(0, min(99, int(round(percent)))),
            "stage": str(stage),
        }
        if message:
            payload["message"] = str(message)

        progress_callback(payload)
    except Exception as error:
        print(
            "[AntiKopas] Peringatan: callback progress gagal:",
            type(error).__name__,
        )


# ==================================================
# DETEKSI SITASI AKADEMIK
# ==================================================

# Contoh:
# (Nasution, 2015)
# (Setyowati & Mulasari, 2013)
# (Pratama & Ihsan, 2017)
# (Penulis et al., 2022)
# (Penulis, 2020; Penulis Lain, 2021)

PARENTHETICAL_CITATION = re.compile(
    r"\("
    r"(?=[^()]{1,160},\s*(?:18|19|20)\d{2}[a-z]?\b)"
    r"[^()]{1,160}"
    r"\)",
    re.IGNORECASE,
)


# Contoh:
# Menurut Nasution (2015)
# Setyowati dan Mulasari (2013)
# Smith et al. (2022)

NARRATIVE_CITATION = re.compile(
    r"\b[A-ZÀ-ÖØ-Þ][\w'’.-]+"
    r"(?:\s+(?:&|dan|and)\s+"
    r"[A-ZÀ-ÖØ-Þ][\w'’.-]+"
    r"|\s+et\s+al\.?)?"
    r"\s*\(\s*(?:18|19|20)\d{2}[a-z]?\s*\)",
)


# Contoh:
# [1]
# [2, 3]
# [4-6]

NUMBERED_CITATION = re.compile(
    r"\[\s*\d+"
    r"(?:\s*[-,;]\s*\d+)*"
    r"\s*\]"
)


def contains_in_text_citation(text):
    """
    Mendeteksi pola sitasi dalam teks.

    Ini hanya pengenal format sitasi,
    bukan daftar topik atau bidang ilmu.

    False positive/negative masih mungkin terjadi
    pada format referensi yang tidak umum.
    """

    text = unicodedata.normalize(
        "NFKC",
        str(text or ""),
    )

    return bool(
        PARENTHETICAL_CITATION.search(text)
        or NARRATIVE_CITATION.search(text)
        or NUMBERED_CITATION.search(text)
    )


# ==================================================
# PISAHKAN SEGMENTASI BERSITASI
# ==================================================

def filter_cited_segments(document_results):
    """
    Mengembalikan segmen yang layak dihitung.

    Aturan:
    1. Segmen dokumen dengan sitasi dikecualikan
       dari indeks tanpa sitasi.

    2. Jika bukti sumber memiliki sitasi,
       pasangan bukti itu tidak digunakan.

    3. Tidak mengubah keputusan AI pada pasangan
       yang tidak mengandung sitasi.

    4. Segmen yang dikecualikan tidak dihitung
       sebagai cocok maupun tidak cocok.
    """

    eligible_results = []

    excluded_document_segments = 0
    excluded_source_matches = 0

    for chunk in document_results:
        if not isinstance(chunk, dict):
            continue

        chunk_text = str(
            chunk.get("chunk_text") or ""
        )

        # Segmen dokumen yang mengandung sitasi
        # tidak masuk pembilang ataupun penyebut.
        if contains_in_text_citation(chunk_text):
            excluded_document_segments += 1
            continue

        original_matches = (
            chunk.get("matches") or []
        )

        filtered_matches = []

        for match in original_matches:
            if not isinstance(match, dict):
                continue

            source_excerpt = str(
                match.get("source_excerpt") or ""
            )

            # Jangan gunakan bukti sumber yang
            # mengandung sitasi penulis-tahun.
            if contains_in_text_citation(
                source_excerpt
            ):
                excluded_source_matches += 1
                continue

            filtered_matches.append(
                dict(match)
            )

        # Jangan mengubah objek asli dari pipeline.
        clean_chunk = dict(chunk)

        clean_chunk["matches"] = filtered_matches

        eligible_results.append(clean_chunk)

    stats = {
        "excluded_document_segments": (
            excluded_document_segments
        ),
        "excluded_source_matches": (
            excluded_source_matches
        ),
        "eligible_segments": len(
            eligible_results
        ),
    }

    return eligible_results, stats


# ==================================================
# ANALISIS UTAMA ANTIKOPAS
# ==================================================

def analyze_antikopas(
    document_text,
    document_title=None,
    progress_callback=None,
):
    # ----------------------------------------------
    # 1. JALANKAN AI
    # ----------------------------------------------

    # Pertahankan kompatibilitas pemanggilan lama.
    # Callback hanya diteruskan jika pemanggil memang menyediakannya.
    if callable(progress_callback):
        document_results = analyze_with_openalex(
            document_text,
            document_title,
            progress_callback=progress_callback,
        )
    else:
        document_results = analyze_with_openalex(
            document_text,
            document_title,
        )

    _report_analysis_progress(
        progress_callback,
        95,
        "Menghitung hasil pemeriksaan",
        "Perbandingan sumber selesai. Menghitung hasil kemiripan dokumen.",
    )

    # ----------------------------------------------
    # 2. SIMPAN HASIL KESELURUHAN
    # ----------------------------------------------

    raw_index = calculate_similarity_index(
        document_results
    )

    _report_analysis_progress(
        progress_callback,
        96,
        "Memeriksa sitasi",
        "Memeriksa bagian dan bukti sumber yang mengandung sitasi.",
    )

    # ----------------------------------------------
    # 3. PISAHKAN SEGMEN BERSITASI
    # ----------------------------------------------

    (
        eligible_results,
        citation_stats,
    ) = filter_cited_segments(
        document_results
    )

    # ----------------------------------------------
    # 4. HITUNG INDEKS TANPA SITASI
    # ----------------------------------------------

    index_result = calculate_similarity_index(
        eligible_results
    )

    _report_analysis_progress(
        progress_callback,
        98,
        "Menyiapkan ringkasan hasil",
        "Perhitungan akhir selesai. Hasil siap disimpan dan dibuatkan laporan.",
    )

    # Perhitungan tetap menggunakan persentase
    # segmen unik yang memiliki bukti cocok.
    #
    # matched_chunks / total_chunks * 100
    #
    # Bedanya: total_chunks sekarang hanya
    # mencakup segmen yang tidak bersitasi.

    total_chunks = index_result[
        "total_chunks"
    ]

    matched_chunks = index_result[
        "matched_chunks"
    ]

    similarity_index = index_result[
        "similarity_index"
    ]

    # ----------------------------------------------
    # 5. INFORMASI DIAGNOSTIK
    # ----------------------------------------------

    diagnostic_code = getattr(
        document_results,
        "diagnostic_code",
        "",
    )

    original_diagnostic = getattr(
        document_results,
        "diagnostic_message",
        "",
    )

    excluded_segments = citation_stats[
        "excluded_document_segments"
    ]

    excluded_matches = citation_stats[
        "excluded_source_matches"
    ]

    diagnostic_parts = []

    if original_diagnostic:
        diagnostic_parts.append(
            original_diagnostic
        )

    if excluded_segments or excluded_matches:
        diagnostic_parts.append(
            "Dari "
            f"{total_chunks} bagian dokumen yang diperiksa, "
            f"{matched_chunks} bagian menunjukkan kemiripan. "
            f"{excluded_segments} bagian yang memiliki sitasi "
            "tidak dihitung sebagai kemiripan. "
            f"{excluded_matches} kecocokan dari sumber bersitasi "
            "juga tidak digunakan."
        )

    if total_chunks == 0:
        diagnostic_code = "no_eligible_segments"

        diagnostic_parts.append(
            "Tidak ada bagian dokumen tanpa sitasi "
            "yang dapat dibandingkan. "
            "Angka 0% pada kondisi ini bukan berarti "
            "dokumen Anda pasti tidak memiliki kemiripan."
        )

    diagnostic_message = " ".join(
        diagnostic_parts
    )

    # ----------------------------------------------
    # 6. LOG AUDIT
    # ----------------------------------------------

    print()
    print("=" * 52)
    print("[AntiKopas] AUDIT SIMILARITY INDEX")
    print("=" * 52)

    print(
        "[Similarity] Keseluruhan:",
        f'{raw_index["similarity_index"]:.2f}%',
    )

    print(
        "[Similarity] Tanpa sitasi:",
        f"{similarity_index:.2f}%",
    )


    print(
        "[Similarity] Rumus:",
        (
            f"({matched_chunks} / {total_chunks}) x 100"
            if total_chunks > 0
            else "Tidak ada segmen tanpa sitasi yang dapat dinilai"
        ),
    )


    print(
        "[Citation] Segmen dokumen dikecualikan:",
        excluded_segments,
    )

    print(
        "[Citation] Pasangan sumber dikecualikan:",
        excluded_matches,
    )

    print("=" * 52)
    print()

    # ----------------------------------------------
    # 7. KEMBALIKAN OUTPUT KOMPATIBEL
    # ----------------------------------------------

    return {
        # Indeks utama tanpa sitasi.
        "similarity_index": similarity_index,
        "total_chunks": total_chunks,
        "matched_chunks": matched_chunks,
        "chunks": eligible_results,

        # Format yang digunakan report.
        "total_similarity": index_result[
            "total_similarity"
        ],
        "source_similarities": index_result[
            "source_similarities"
        ],

        # Hasil mentah dipertahankan untuk audit.
        "raw_similarity_index": raw_index[
            "similarity_index"
        ],
        "raw_total_chunks": raw_index[
            "total_chunks"
        ],
        "raw_matched_chunks": raw_index[
            "matched_chunks"
        ],

        # Statistik pengecualian.
        "excluded_citation_segments": (
            excluded_segments
        ),
        "excluded_citation_matches": (
            excluded_matches
        ),

        # Status diagnostik.
        "diagnostic_code": diagnostic_code,
        "diagnostic_message": diagnostic_message,
    }
