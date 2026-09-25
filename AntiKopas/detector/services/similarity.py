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
    Membandingkan setiap chunk dengan banyak sumber.
    """

    results = []

    for chunk in chunks:

        best_match = None

        for source in sources:

            score = calculate_similarity(
                chunk["text"],
                source["text"]
            )

            if (
                best_match is None
                or score > best_match["similarity_score"]
            ):
                best_match = {
                    "source_id": source["source_id"],
                    "title": source["title"],
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