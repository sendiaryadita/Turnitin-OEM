from sentence_transformers import SentenceTransformer, CrossEncoder
from sklearn.metrics.pairwise import cosine_similarity
import torch


# ==========================================
# 1. LOAD MODEL
# ==========================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding model berhasil dimuat!")


print("Loading cross encoder...")

cross_encoder = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L6-v2",
    activation_fn=torch.nn.Sigmoid()
)

print("Cross Encoder berhasil dimuat!\n")


# ==========================================
# 2. DATA SIMULASI
# ==========================================

document_chunks = [
    "Kecerdasan buatan dapat membantu meningkatkan proses pembelajaran mahasiswa melalui sistem pembelajaran yang lebih adaptif.",

    "Penelitian ini menggunakan metode machine learning untuk melakukan klasifikasi terhadap data yang telah dikumpulkan.",

    "Sistem informasi akademik digunakan untuk membantu mahasiswa dalam mengakses jadwal dan informasi perkuliahan."
]


source_chunks = [
    "Artificial intelligence dapat digunakan untuk meningkatkan proses belajar mahasiswa melalui pembelajaran adaptif.",

    "Algoritma pembelajaran mesin dapat digunakan untuk mengelompokkan dan mengklasifikasikan data penelitian.",

    "Sistem informasi akademik membantu mahasiswa memperoleh informasi mengenai jadwal dan kegiatan perkuliahan.",

    "Rumah sakit menggunakan sistem informasi untuk mengelola data pasien dan pelayanan kesehatan."
]


# ==========================================
# 3. EMBEDDING
# ==========================================

print("Membuat embedding...")

document_embeddings = embedding_model.encode(
    document_chunks,
    normalize_embeddings=True
)

source_embeddings = embedding_model.encode(
    source_chunks,
    normalize_embeddings=True
)

print("Embedding selesai!\n")


# ==========================================
# 4. RETRIEVAL DENGAN COSINE SIMILARITY
# ==========================================

TOP_K = 2

print("=== TAHAP 1: RETRIEVAL ===")

for i, document_chunk in enumerate(document_chunks):

    similarities = cosine_similarity(
        [document_embeddings[i]],
        source_embeddings
    )[0]

    # Urutkan index berdasarkan similarity tertinggi
    ranked_indices = similarities.argsort()[::-1]

    top_indices = ranked_indices[:TOP_K]

    print(f"\n{'=' * 60}")
    print(f"DOCUMENT CHUNK {i + 1}")
    print(document_chunk)

    print("\nTop kandidat berdasarkan all-MiniLM:")

    for rank, source_index in enumerate(top_indices, start=1):

        print(
            f"{rank}. Source {source_index + 1}"
            f" | Cosine: {similarities[source_index]:.4f}"
        )

        print(
            f"   {source_chunks[source_index]}"
        )


# ==========================================
# 5. CROSS ENCODER RERANKING
# ==========================================

print("\n\n=== TAHAP 2: CROSS ENCODER ===")

for i, document_chunk in enumerate(document_chunks):

    similarities = cosine_similarity(
        [document_embeddings[i]],
        source_embeddings
    )[0]

    ranked_indices = similarities.argsort()[::-1]

    top_indices = ranked_indices[:TOP_K]

    # Buat pasangan document-source
    pairs = [
        (
            document_chunk,
            source_chunks[source_index]
        )
        for source_index in top_indices
    ]

    # Cross Encoder
    cross_scores = cross_encoder.predict(pairs)

    results = []

    for j, source_index in enumerate(top_indices):

        results.append({
            "source_index": source_index,
            "embedding_score": float(similarities[source_index]),
            "cross_score": float(cross_scores[j])
        })

    # Urutkan berdasarkan Cross Encoder
    results.sort(
        key=lambda x: x["cross_score"],
        reverse=True
    )

    print(f"\n{'=' * 60}")
    print(f"FINAL RANKING - DOCUMENT CHUNK {i + 1}")
    print(document_chunk)

    for rank, result in enumerate(results, start=1):

        source_index = result["source_index"]

        print(
            f"\n{rank}. Source {source_index + 1}"
        )

        print(
            f"   MiniLM Cosine : "
            f"{result['embedding_score']:.4f}"
        )

        print(
            f"   Cross Encoder : "
            f"{result['cross_score']:.4f}"
        )

        print(
            f"   Text          : "
            f"{source_chunks[source_index]}"
        )