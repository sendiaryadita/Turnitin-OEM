import sys
from pathlib import Path

import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sentence_transformers import SentenceTransformer, CrossEncoder, util

from detector.services.document_analyzer import chunk_text
from detector.services.openalex import search_literature


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CROSS_ENCODER_MODEL = "models/antikopas-cross-encoder"

TOP_K_MINILM = 5


def torch_topk(scores, k):
    values, indices = torch.topk(scores, k=k)
    return values, indices


print("=" * 60)
print("ANTIKOPAS FULL PIPELINE TEST")
print("=" * 60)

print("\nLoading MiniLM...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL)

print("Loading Fine-tuned Cross Encoder...")
cross_encoder = CrossEncoder(
    CROSS_ENCODER_MODEL,
    num_labels=1,
    max_length=512
)

print("Model loaded.")


# ============================================================
# INPUT DOKUMEN
# ============================================================

document_text = """
Kecerdasan buatan merupakan salah satu teknologi yang berkembang pesat
dan mulai digunakan dalam berbagai bidang, termasuk pendidikan.

Dalam proses pembelajaran, kecerdasan buatan dapat membantu mahasiswa
memperoleh materi yang sesuai dengan kebutuhan dan kemampuan mereka.

Sistem pembelajaran berbasis kecerdasan buatan dapat memberikan
rekomendasi materi secara lebih adaptif.

Dengan adanya sistem tersebut, mahasiswa dapat memperoleh pengalaman
belajar yang berbeda sesuai dengan tingkat pemahaman masing-masing.

Selain membantu mahasiswa, kecerdasan buatan juga dapat membantu dosen
dalam menganalisis proses pembelajaran.
"""


# ============================================================
# CHUNKING
# ============================================================

chunks = chunk_text(document_text)

print(f"\nTotal chunk : {len(chunks)}")


# ============================================================
# PROSES SETIAP CHUNK
# ============================================================

for chunk_index, chunk in enumerate(chunks, start=1):

    print("\n" + "=" * 60)
    print(f"CHUNK {chunk_index}")
    print("=" * 60)

    print(chunk)

    # --------------------------------------------------------
    # OPENALEX
    # --------------------------------------------------------

    print("\nMencari literatur di OpenAlex...")

    literature = search_literature(
        chunk,
        per_page=20
    )

    print(f"Ditemukan {len(literature)} literatur.")

    # Ambil hanya literatur yang mempunyai text
    literature_with_text = [
        item
        for item in literature
        if item.get("text")
    ]

    print(
        f"Literatur dengan text: "
        f"{len(literature_with_text)}"
    )

    if not literature_with_text:
        print("Tidak ada literatur dengan text.")
        continue

    # --------------------------------------------------------
    # MINILM
    # --------------------------------------------------------

    source_texts = [
        item["text"]
        for item in literature_with_text
    ]

    chunk_embedding = embedding_model.encode(
        chunk,
        convert_to_tensor=True
    )

    source_embeddings = embedding_model.encode(
        source_texts,
        convert_to_tensor=True
    )

    similarities = util.cos_sim(
        chunk_embedding,
        source_embeddings
    )[0]

    # Ambil index Top-K
    top_k = min(
        TOP_K_MINILM,
        len(literature_with_text)
    )

    top_scores, top_indices = torch_topk(
        similarities,
        top_k
    )

    # --------------------------------------------------------
    # CROSS ENCODER
    # --------------------------------------------------------

    pairs = []

    candidates = []

    for score, index in zip(
        top_scores,
        top_indices
    ):

        index = int(index)

        item = literature_with_text[index]

        candidates.append({
            "item": item,
            "minilm_score": float(score)
        })

        pairs.append(
            (
                chunk,
                item["text"]
            )
        )

    cross_scores = cross_encoder.predict(pairs)

    # --------------------------------------------------------
    # GABUNGKAN HASIL
    # --------------------------------------------------------

    results = []

    for candidate, cross_score in zip(
        candidates,
        cross_scores
    ):

        item = candidate["item"]

        results.append({
            "title": item.get(
                "title",
                "Tanpa judul"
            ),
            "minilm_score": candidate[
                "minilm_score"
            ],
            "cross_score": float(
                cross_score
            )
        })

    # Urutkan berdasarkan Cross Encoder
    results.sort(
        key=lambda x: x["cross_score"],
        reverse=True
    )

    # --------------------------------------------------------
    # OUTPUT FINAL
    # --------------------------------------------------------

    print("\nTOP 5 FINAL")

    for rank, result in enumerate(
        results,
        start=1
    ):

        print(
            f"{rank}. "
            f"{result['title']} | "
            f"MiniLM: "
            f"{result['minilm_score']:.4f} | "
            f"Cross: "
            f"{result['cross_score']:.4f}"
        )


# ============================================================
# HELPER
# ============================================================

def torch_topk(scores, k):
    """
    Mengambil Top-K score dan index.
    """

    import torch

    values, indices = torch.topk(
        scores,
        k=k
    )

    return values, indices