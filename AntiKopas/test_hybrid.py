from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer


# Load model semantic similarity
model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


def semantic_similarity(text1, text2):
    embeddings = model.encode([text1, text2])

    score = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    return float(score)


def lexical_similarity(text1, text2):
    vectorizer = TfidfVectorizer()

    tfidf = vectorizer.fit_transform([
        text1,
        text2
    ])

    score = cosine_similarity(
        tfidf[0:1],
        tfidf[1:2]
    )[0][0]

    return float(score)


def hybrid_similarity(
    text1,
    text2,
    semantic_weight=0.7,
    lexical_weight=0.3
):
    semantic_score = semantic_similarity(text1, text2)
    lexical_score = lexical_similarity(text1, text2)

    hybrid_score = (
        semantic_weight * semantic_score
        + lexical_weight * lexical_score
    )

    return {
        "semantic_score": semantic_score,
        "lexical_score": lexical_score,
        "hybrid_score": hybrid_score
    }


# =========================
# TEST
# =========================

text1 = """
Penggunaan media sosial secara berlebihan dapat memberikan dampak terhadap kondisi remaja.
"""

text2 = """
Proses fotosintesis pada tumbuhan membutuhkan cahaya matahari dan menghasilkan oksigen.
"""

result = hybrid_similarity(text1, text2)

print("\n=== HASIL HYBRID SIMILARITY ===")
print(f"Semantic Score : {result['semantic_score']:.4f}")
print(f"Lexical Score  : {result['lexical_score']:.4f}")
print(f"Hybrid Score   : {result['hybrid_score']:.4f}")