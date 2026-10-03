import torch
from .text_overlap import calculate_text_overlap

from sentence_transformers import SentenceTransformer, CrossEncoder, util

from .document_analyzer import chunk_text
from .openalex import search_literature


# =========================
# MODEL
# =========================

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CROSS_ENCODER_MODEL = "models/antikopas-cross-encoder"


# =========================
# CONFIG
# =========================
OPENALEX_PER_PAGE = 10
TOP_K = 3

# Threshold hasil pengujian dataset
CROSS_THRESHOLD = -1.90


# =========================
# LOAD MODEL
# =========================

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

cross_encoder = CrossEncoder(
    CROSS_ENCODER_MODEL,
    num_labels=1,
    max_length=512
)


# =========================
# MAIN PIPELINE
# =========================

def analyze_with_openalex(document_text, document_title=None):

    # 1. Pecah dokumen menjadi beberapa chunk
    chunks = chunk_text(document_text)

    document_results = []

    # Proses setiap chunk
    for chunk_index, chunk in enumerate(chunks, start=1):

        # ==================================
        # 2. SEARCH OPENALEX
        # ==================================

        literature = search_literature(
            chunk,
            per_page=OPENALEX_PER_PAGE
        )

        # ==================================
        # 2A. FILTER SELF-MATCH
        # ==================================

        if document_title:
            normalized_title = (
                document_title
                .strip()
                .lower()
            )

            literature = [
                item
                for item in literature
                if (
                    item.get("title", "")
                    .strip()
                    .lower()
                    != normalized_title
                )
            ]

        # Hanya gunakan literature yang mempunyai text
        literature = [
            item
            for item in literature
            if item.get("text")
        ]

        # Kalau tidak ada literature
        if not literature:
            document_results.append({
                "chunk_index": chunk_index,
                "chunk_text": chunk,
                "matches": []
            })
            continue

        # ==================================
        # 3. MINI-LM RETRIEVAL
        # ==================================

        source_texts = [
            item["text"]
            for item in literature
        ]

        # Embedding chunk dokumen
        chunk_embedding = embedding_model.encode(
            chunk,
            convert_to_tensor=True
        )

        # Embedding semua literature
        source_embeddings = embedding_model.encode(
            source_texts,
            convert_to_tensor=True
        )

        # Cosine similarity
        similarity_scores = util.cos_sim(
            chunk_embedding,
            source_embeddings
        )[0]

        # ==================================
        # 4. AMBIL TOP-K
        # ==================================

        top_k = min(
            TOP_K,
            len(literature)
        )

        top_scores, top_indices = torch.topk(
            similarity_scores,
            k=top_k
        )

        candidates = []
        pairs = []

        for score, index in zip(
            top_scores,
            top_indices
        ):

            index = int(index)

            item = literature[index]

            candidates.append({
                "item": item,
                "minilm_score": float(score)
            })

            # Pair untuk Cross Encoder
            pairs.append(
                (
                    chunk,
                    item["text"]
                )
            )

        # ==================================
        # 5. CROSS ENCODER
        # ==================================

        cross_scores = cross_encoder.predict(
            pairs
        )

        # ==================================
        # 6. GABUNGKAN HASIL
        # ==================================

        matches = []

        for candidate, cross_score in zip(
            candidates,
            cross_scores
        ):

            item = candidate["item"]

        cross_score = float(cross_score)

        is_matched = cross_score >= CROSS_THRESHOLD

        matches.append({
            "openalex_id": item.get("source_id"),
            "title": item.get("title"),
            "year": item.get("year"),
            "doi": item.get("doi"),
            "url": item.get("url"),
            "minilm_score": candidate["minilm_score"],
            "cross_score": cross_score,
            "overlap_score": 0.0,
            "matched": is_matched
        })
        # ==================================
        # 7. URUTKAN BERDASARKAN
        # CROSS ENCODER
        # ==================================

        matches.sort(
            key=lambda x: x["cross_score"],
            reverse=True
        )

        # ==================================
        # 8. SIMPAN HASIL CHUNK
        # ==================================

        document_results.append({
            "chunk_index": chunk_index,
            "chunk_text": chunk,
            "matches": matches
        })

    # ==================================
    # 9. RETURN SEMUA HASIL
    # ==================================

    return document_results