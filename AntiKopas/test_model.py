from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


def similarity(text1, text2):
    embeddings = model.encode([text1, text2])

    score = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    return float(score)


tests = [
    {
        "name": "Sangat Mirip",
        "text1": "Penggunaan media sosial secara berlebihan dapat memberikan dampak terhadap kondisi remaja.",
        "text2": "Penggunaan media sosial secara berlebihan dapat memberikan dampak terhadap kondisi remaja."
    },
    {
        "name": "Hampir Sama",
        "text1": "Penggunaan media sosial secara berlebihan dapat memberikan dampak terhadap kondisi remaja.",
        "text2": "Penggunaan media sosial yang berlebihan dapat memberikan dampak terhadap kondisi remaja."
    },
    {
        "name": "Parafrase",
        "text1": "Penggunaan media sosial secara berlebihan dapat memberikan dampak terhadap kondisi remaja.",
        "text2": "Pemakaian platform digital yang terlalu sering dapat memengaruhi kondisi kehidupan anak muda."
    },
    {
        "name": "Topik Berkaitan",
        "text1": "Penggunaan media sosial secara berlebihan dapat memberikan dampak terhadap kondisi remaja.",
        "text2": "Remaja yang menggunakan teknologi digital perlu memiliki kemampuan literasi informasi."
    },
    {
        "name": "Tidak Berkaitan",
        "text1": "Penggunaan media sosial secara berlebihan dapat memberikan dampak terhadap kondisi remaja.",
        "text2": "Proses fotosintesis pada tumbuhan membutuhkan cahaya matahari dan menghasilkan oksigen."
    }
]


print("\n=== TEST MODEL ANTI KOPAS ===")

for test in tests:
    score = similarity(
        test["text1"],
        test["text2"]
    )

    print(f"{test['name']:<20} : {score:.4f}")