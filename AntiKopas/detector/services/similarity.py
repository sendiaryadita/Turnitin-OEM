from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# Model utama AntiKopas
model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


def calculate_similarity(text1, text2):
    """
    Menghitung semantic similarity antara dua teks.
    """

    embeddings = model.encode(
        [text1, text2],
        normalize_embeddings=True
    )

    score = cosine_similarity(
        embeddings[0].reshape(1, -1),
        embeddings[1].reshape(1, -1)
    )[0][0]

    return float(score)


def compare_chunks(chunks, comparison_text, threshold=0.7):
    """
    Membandingkan setiap chunk dengan satu teks pembanding.
    """

    results = []

    for chunk in chunks:
        score = calculate_similarity(
            chunk["text"],
            comparison_text
        )

        results.append({
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            "similarity_score": score,
            "is_match": score >= threshold
        })

    return results


def compare_multiple_sources(chunks, sources, threshold=0.7):
    """
    Membandingkan setiap chunk dengan banyak sumber
    dan mengambil sumber dengan similarity tertinggi.
    """

    results = []

    for chunk in chunks:

        best_match = None

        for source in sources:

            # Lewati sumber yang tidak memiliki teks
            if not source.get("text"):
                continue

            score = calculate_similarity(
                chunk["text"],
                source["text"]
            )

            if (
                best_match is None
                or score > best_match["similarity_score"]
            ):
                best_match = {
                    "source_id": source.get("source_id"),
                    "title": source.get("title"),
                    "year": source.get("year"),
                    "doi": source.get("doi"),
                    "url": source.get("url"),
                    "similarity_score": score
                }

        if best_match:
            best_match["is_match"] = (
                best_match["similarity_score"] >= threshold
            )

        results.append({
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            "best_match": best_match
        })

    return results


def calculate_similarity_index(results):
    """
    Menghitung rata-rata similarity dari chunk yang match.
    """

    matched_scores = []

    for result in results:

        match = result["best_match"]

        if match and match["is_match"]:
            matched_scores.append(
                match["similarity_score"]
            )

    if not matched_scores:
        return 0.0

    return sum(matched_scores) / len(matched_scores)

def rank_sources(chunks, sources, max_results=20):
    source_results = []

    for source in sources:
        if not source.get("text"):
            continue

        best_score = 0.0

        for chunk in chunks:
            score = calculate_similarity(
                chunk["text"],
                source["text"]
            )

            if score > best_score:
                best_score = score

        source_results.append({
            "source_id": source.get("source_id"),
            "title": source.get("title"),
            "year": source.get("year"),
            "doi": source.get("doi"),
            "url": source.get("url"),
            "similarity_score": best_score
        })

    source_results.sort(
        key=lambda x: x["similarity_score"],
        reverse=True
    )

    return source_results[:max_results]