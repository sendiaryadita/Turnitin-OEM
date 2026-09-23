from detector.services.chunking import chunk_text
from detector.services.similarity import compare_chunks


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
# SUMBER PEMBANDING
# =========================

source_text = """
Penggunaan media sosial secara berlebihan dapat memberikan dampak
terhadap kondisi remaja dan dapat memengaruhi pola tidur.
"""


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

results = compare_chunks(
    chunks,
    source_text,
    threshold=0.7
)


# =========================
# HASIL
# =========================

print("\n=== HASIL COMPARE CHUNKS ===")

for result in results:

    print(f"\nChunk {result['chunk_id']}")

    print(f"Text       : {result['text']}")

    print(
        f"Similarity : "
        f"{result['similarity_score']:.4f}"
    )

    print(
        f"Match      : "
        f"{result['is_match']}"
    )