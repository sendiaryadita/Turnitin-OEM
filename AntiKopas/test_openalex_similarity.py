from detector.services.openalex import search_literature
from detector.services.similarity import compare_multiple_sources


user_text = """
Regulasi emosi merupakan kemampuan seseorang dalam
mengatur dan mengendalikan respons emosional ketika
menghadapi berbagai situasi.
"""


# 1. Cari literatur dari OpenAlex
sources = search_literature(
    "regulasi emosi remaja",
    per_page=5
)


# 2. Buat satu chunk dari teks user
chunks = [
    {
        "chunk_id": 1,
        "text": user_text
    }
]


# 3. Bandingkan teks user dengan hasil OpenAlex
results = compare_multiple_sources(
    chunks,
    sources,
    threshold=0.7
)


# 4. Tampilkan hasil
for result in results:

    print("\n==============================")
    print("Chunk:", result["chunk_id"])
    print("Text :", result["text"])

    best_match = result["best_match"]

    if best_match:
        print("\nBest Match:")
        print("Source ID :", best_match["source_id"])
        print("Title     :", best_match["title"])
        print("Score     :", best_match["similarity_score"])
        print("Match     :", best_match["is_match"])
        