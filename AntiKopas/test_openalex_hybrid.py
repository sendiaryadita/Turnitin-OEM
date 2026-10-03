from detector.services.openalex import search_literature

from sentence_transformers import SentenceTransformer, CrossEncoder
from sklearn.metrics.pairwise import cosine_similarity

import torch


# =========================================================
# 1. LOAD MODEL
# =========================================================

print("Loading MiniLM...")

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("MiniLM berhasil dimuat!")

print("Loading Cross Encoder...")

cross_encoder = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L6-v2",
    activation_fn=torch.nn.Sigmoid()
)

print("Cross Encoder berhasil dimuat!\n")


# =========================================================
# 2. INPUT DOKUMEN
# =========================================================

document_chunk = """
Kecerdasan buatan dapat membantu meningkatkan proses
pembelajaran mahasiswa melalui sistem pembelajaran yang
lebih adaptif.
""".strip()

print("=" * 70)
print("DOCUMENT CHUNK")
print("=" * 70)
print(document_chunk)


# =========================================================
# 3. CARI LITERATUR DI OPENALEX
# =========================================================

print("\nMencari literatur di OpenAlex...")

literatures = search_literature(
    "pengaruh penggunaan AI terhadap pembelajaran mahasiswa"
)

print(f"Ditemukan {len(literatures)} literatur.")


# =========================================================
# 4. AMBIL LITERATUR YANG MEMILIKI TEXT
# =========================================================

valid_literatures = []

for literature in literatures:

    text = literature.get("text")

    if text and text.strip():

        valid_literatures.append(literature)


print(
    f"Literatur dengan text: "
    f"{len(valid_literatures)}"
)


if not valid_literatures:
    print("Tidak ada literatur yang memiliki text.")
    exit()


# =========================================================
# 5. EMBEDDING DOCUMENT
# =========================================================

document_embedding = embedding_model.encode(
    [document_chunk],
    normalize_embeddings=True
)


# =========================================================
# 6. EMBEDDING LITERATUR
# =========================================================

source_texts = [
    literature["text"]
    for literature in valid_literatures
]

print("\nMembuat embedding literatur...")

source_embeddings = embedding_model.encode(
    source_texts,
    normalize_embeddings=True
)


# =========================================================
# 7. COSINE SIMILARITY
# =========================================================

similarities = cosine_similarity(
    document_embedding,
    source_embeddings
)[0]


# =========================================================
# 8. TOP-K RETRIEVAL
# =========================================================

TOP_K = min(5, len(valid_literatures))

ranked_indices = similarities.argsort()[::-1]

top_indices = ranked_indices[:TOP_K]


print("\n")
print("=" * 70)
print("TAHAP 1 - RETRIEVAL")
print("=" * 70)

for rank, index in enumerate(top_indices, start=1):

    literature = valid_literatures[index]

    print(f"\n{rank}. {literature.get('title')}")
    print(
        f"Cosine Similarity : "
        f"{similarities[index]:.4f}"
    )
    print(
        f"Tahun             : "
        f"{literature.get('year')}"
    )
    print(
        f"DOI               : "
        f"{literature.get('doi')}"
    )


# =========================================================
# 9. CROSS ENCODER
# =========================================================

pairs = []

for index in top_indices:

    pairs.append(
        (
            document_chunk,
            valid_literatures[index]["text"]
        )
    )


print("\n")
print("=" * 70)
print("TAHAP 2 - CROSS ENCODER")
print("=" * 70)

cross_scores = cross_encoder.predict(pairs)


# =========================================================
# 10. FINAL RANKING
# =========================================================

results = []

for i, index in enumerate(top_indices):

    results.append({
        "index": index,
        "cosine": float(similarities[index]),
        "cross": float(cross_scores[i])
    })


results.sort(
    key=lambda x: x["cross"],
    reverse=True
)


print("\n")
print("=" * 70)
print("FINAL RANKING")
print("=" * 70)


for rank, result in enumerate(results, start=1):

    literature = valid_literatures[
        result["index"]
    ]

    print(f"\n{rank}. {literature.get('title')}")

    print(
        f"MiniLM Cosine : "
        f"{result['cosine']:.4f}"
    )

    print(
        f"Cross Encoder : "
        f"{result['cross']:.4f}"
    )

    print(
        f"Tahun         : "
        f"{literature.get('year')}"
    )

    print(
        f"DOI           : "
        f"{literature.get('doi')}"
    )

    print(
        f"OpenAlex      : "
        f"{literature.get('id')}"
    )