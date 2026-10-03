import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import torch
from sentence_transformers import SentenceTransformer, CrossEncoder, util

from detector.services.openalex import search_literature


# ============================================================
# CONFIG
# ============================================================

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CROSS_ENCODER_MODEL = "models/antikopas-cross-encoder"

TOP_K = 5


# ============================================================
# INPUT
# ============================================================

query = input("\nMasukkan teks yang ingin dianalisis:\n> ").strip()

if not query:
    print("Teks tidak boleh kosong.")
    exit()


# ============================================================
# LOAD MODELS
# ============================================================

print("\n" + "=" * 60)
print("LOAD MINILM")
print("=" * 60)

embedding_model = SentenceTransformer(EMBEDDING_MODEL)

print("MiniLM berhasil dimuat.")


print("\n" + "=" * 60)
print("LOAD FINE-TUNED CROSS ENCODER")
print("=" * 60)

cross_encoder = CrossEncoder(
    CROSS_ENCODER_MODEL,
    num_labels=1,
    max_length=512
)

print("Cross Encoder berhasil dimuat.")


# ============================================================
# OPENALEX
# ============================================================

print("\n" + "=" * 60)
print("SEARCH OPENALEX")
print("=" * 60)

literature = search_literature(
    query,
    per_page=20
)

print(f"Ditemukan {len(literature)} literatur.")


# ============================================================
# FILTER LITERATURE
# ============================================================

literature_with_text = [
    item
    for item in literature
    if item.get("text")
]

print(f"Literatur dengan text: {len(literature_with_text)}")


if not literature_with_text:
    print("Tidak ada literatur yang memiliki text.")
    exit()


# ============================================================
# MINILM RETRIEVAL
# ============================================================

print("\n" + "=" * 60)
print("TAHAP 1 - MINILM RETRIEVAL")
print("=" * 60)

query_embedding = embedding_model.encode(
    query,
    convert_to_tensor=True
)

source_texts = [
    item["text"]
    for item in literature_with_text
]

source_embeddings = embedding_model.encode(
    source_texts,
    convert_to_tensor=True
)

similarities = util.cos_sim(
    query_embedding,
    source_embeddings
)[0]


# ============================================================
# TOP K
# ============================================================

top_k = min(TOP_K, len(literature_with_text))

top_results = torch.topk(
    similarities,
    k=top_k
)


print(f"\nTop {top_k} kandidat dari MiniLM:\n")

candidates = []

for rank, index in enumerate(top_results.indices, start=1):

    index = index.item()
    mini_score = top_results.values[rank - 1].item()

    item = literature_with_text[index]

    candidates.append({
        "item": item,
        "mini_score": mini_score
    })

    print(
        f"{rank}. "
        f"{item.get('title', 'Tanpa judul')} "
        f"| MiniLM: {mini_score:.4f}"
    )


# ============================================================
# CROSS ENCODER
# ============================================================

print("\n" + "=" * 60)
print("TAHAP 2 - FINE-TUNED CROSS ENCODER")
print("=" * 60)

pairs = []

for candidate in candidates:

    source_text = candidate["item"]["text"]

    pairs.append(
        (
            query,
            source_text
        )
    )


cross_scores = cross_encoder.predict(pairs)

cross_scores = [
    float(score)
    for score in cross_scores
]


# ============================================================
# FINAL RANKING
# ============================================================

results = []

for candidate, cross_score in zip(
    candidates,
    cross_scores
):

    results.append({
        "title": candidate["item"].get(
            "title",
            "Tanpa judul"
        ),
        "year": candidate["item"].get(
            "year",
            "-"
        ),
        "doi": candidate["item"].get(
            "doi",
            "-"
        ),
        "mini_score": candidate["mini_score"],
        "cross_score": cross_score
    })


results.sort(
    key=lambda x: x["cross_score"],
    reverse=True
)


# ============================================================
# OUTPUT
# ============================================================

print("\n" + "=" * 60)
print("FINAL RANKING")
print("=" * 60)

for rank, result in enumerate(
    results,
    start=1
):

    print(f"\n{rank}. {result['title']}")
    print(f"   Tahun     : {result['year']}")
    print(f"   DOI       : {result['doi']}")
    print(
        f"   MiniLM    : "
        f"{result['mini_score']:.4f}"
    )
    print(
        f"   CrossEnc  : "
        f"{result['cross_score']:.4f}"
    )