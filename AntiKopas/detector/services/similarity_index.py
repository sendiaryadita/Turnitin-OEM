
from collections import defaultdict


# ==========================================
# NORMALISASI IDENTITAS JURNAL
# ==========================================

def get_source_key(match):
    """
    Mengidentifikasi jurnal yang sama
    meskipun muncul pada banyak chunk.
    """

    openalex_id = match.get("openalex_id")
    doi = match.get("doi")
    url = match.get("url")
    title = match.get("title")

    if openalex_id:
        return "openalex:" + str(openalex_id).strip().casefold()

    if doi:
        normalized_doi = str(doi).strip().casefold()

        for prefix in (
            "https://doi.org/",
            "http://doi.org/",
            "https://dx.doi.org/",
            "http://dx.doi.org/",
            "doi:",
        ):
            if normalized_doi.startswith(prefix):
                normalized_doi = normalized_doi[len(prefix):]
                break

        return "doi:" + normalized_doi

    if url:
        return "url:" + str(url).strip().casefold()

    if title:
        normalized_title = " ".join(
            str(title).casefold().split()
        )
        return "title:" + normalized_title

    return None


# ==========================================
# HITUNG SIMILARITY
# ==========================================

def calculate_similarity_index(document_results):
    """
    Menghitung:
    - Total cakupan kemiripan
    - Kemiripan per jurnal
    - Chunk unik yang cocok

    Persentase berdasarkan cakupan chunk
    dokumen yang di-upload, bukan
    persentase plagiarisme.
    """

    total_chunks = len(document_results)

    # Hasil untuk dokumen kosong
    if total_chunks == 0:
        return {
            "total_chunks": 0,
            "matched_chunks": 0,
            "similarity_index": 0.0,
            "total_similarity": 0.0,
            "source_similarities": [],
        }

    # Menyimpan chunk cocok secara global
    global_matched_chunks = set()

    # Menyimpan metadata dan chunk setiap jurnal
    sources = {}

    # ======================================
    # PROSES SETIAP CHUNK
    # ======================================

    for position, chunk in enumerate(
        document_results,
        start=1,
    ):

        chunk_index = chunk.get(
            "chunk_index",
            position,
        )

        matches = chunk.get("matches", [])

        for match in matches:

            # Hanya yang dinyatakan matched
            # oleh full_pipeline.py
            if not match.get("matched", False):
                continue

            source_key = get_source_key(match)

            if not source_key:
                continue

            if source_key not in sources:

                sources[source_key] = {
                    "openalex_id": match.get(
                        "openalex_id"
                    ),
                    "title": match.get("title"),
                    "year": match.get("year"),
                    "doi": match.get("doi"),
                    "url": match.get("url"),
                    "chunk_indices": set(),
                }

            # Satu chunk hanya dihitung sekali
            # untuk jurnal yang sama
            sources[source_key][
                "chunk_indices"
            ].add(chunk_index)

            # Total: semua chunk cocok,
            # tanpa duplikasi antarjurnal
            global_matched_chunks.add(
                chunk_index
            )

    # ======================================
    # HITUNG TOTAL
    # ======================================

    matched_chunks = len(
        global_matched_chunks
    )

    total_similarity = round(
        (matched_chunks / total_chunks) * 100,
        2,
    )

    # ======================================
    # HITUNG PERSENTASE PER JURNAL
    # ======================================

    source_similarities = []

    for source in sources.values():

        chunk_indices = sorted(
            source["chunk_indices"]
        )

        source_matched_chunks = len(
            chunk_indices
        )

        percentage = round(
            (
                source_matched_chunks
                / total_chunks
            ) * 100,
            2,
        )

        source_similarities.append({
            "openalex_id": source["openalex_id"],
            "title": source["title"],
            "year": source["year"],
            "doi": source["doi"],
            "url": source["url"],
            "matched_chunks": source_matched_chunks,
            "similarity_percentage": percentage,
            "matched_chunk_indices": chunk_indices,
        })

    # Urutkan dari persentase terbesar
    source_similarities.sort(
        key=lambda source: (
            -source["similarity_percentage"],
            -source["matched_chunks"],
            str(source["title"] or ""),
        )
    )

    # ======================================
    # RETURN HASIL
    # ======================================

    return {
        # Kompatibel dengan kode lama
        "total_chunks": total_chunks,
        "matched_chunks": matched_chunks,
        "similarity_index": total_similarity,

        # Format baru untuk report AntiKopas
        "total_similarity": total_similarity,
        "source_similarities": source_similarities,
    }
