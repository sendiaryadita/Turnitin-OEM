from detector.services.chunking import chunk_text

from detector.services.similarity import (
    compare_multiple_sources,
    calculate_similarity_index
)


# =========================
# DOKUMEN MAHASISWA
# =========================

manuscript = """
Penggunaan media sosial telah berkembang pesat dalam kehidupan masyarakat.
Media sosial digunakan untuk berkomunikasi dan memperoleh informasi.
Namun penggunaan yang berlebihan dapat memberikan dampak terhadap remaja.

Remaja merupakan kelompok yang cukup aktif menggunakan media sosial.
Penggunaan media sosial secara berlebihan dapat memengaruhi pola tidur.
Selain itu, penggunaan yang terlalu lama dapat mengurangi aktivitas fisik.

Fotosintesis merupakan proses penting yang terjadi pada tumbuhan.
Proses ini membutuhkan cahaya matahari untuk menghasilkan energi.
"""


# =========================
# SUMBER LITERATUR
# =========================

sources = [

    {
        "source_id": "SOURCE_1",
        "title": "Pengaruh Media Sosial terhadap Remaja",
        "text": """
        Penggunaan media sosial secara berlebihan dapat memberikan dampak
        terhadap kondisi remaja dan dapat memengaruhi pola tidur.
        """
    },

    {
        "source_id": "SOURCE_2",
        "title": "Teknologi Digital dalam Pendidikan",
        "text": """
        Teknologi digital dapat membantu proses pembelajaran dan
        meningkatkan akses mahasiswa terhadap informasi akademik.
        """
    },

    {
        "source_id": "SOURCE_3",
        "title": "Proses Fotosintesis pada Tumbuhan",
        "text": """
        Fotosintesis merupakan proses penting pada tumbuhan yang
        membutuhkan cahaya matahari untuk menghasilkan energi.
        """
    }
]


# =========================
# CHUNKING
# =========================

chunks = chunk_text(
    manuscript,
    sentences_per_chunk=3
)


# =========================
# COMPARE
# =========================

results = compare_multiple_sources(
    chunks,
    sources,
    threshold=0.7
)

similarity_index = calculate_similarity_index(results)
# =========================
# HASIL
# =========================

print("\n=== MULTIPLE SOURCE COMPARISON ===")

for result in results:

    print(f"\nChunk {result['chunk_id']}")
    print(f"Text : {result['text']}")

    match = result["best_match"]

    if match:
        print(f"Best Source : {match['source_id']}")
        print(f"Similarity  : {match['similarity_score']:.4f}")
        print(f"Match       : {match['is_match']}")

print("\n=== SIMILARITY INDEX ===")
print(f"Similarity Index : {similarity_index:.4f}")

matched_blocks = sum(
    1
    for result in results
    if result["best_match"]
    and result["best_match"]["is_match"]
)

total_blocks = len(results)

print(f"Text Blocks Scanned : {total_blocks}")
print(f"Matched Blocks      : {matched_blocks}")
print(f"Similarity Index    : {similarity_index:.4f}")