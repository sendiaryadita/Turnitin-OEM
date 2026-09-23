from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

teks1 = "Media sosial dapat meningkatkan motivasi belajar siswa."

teks2 = "Penggunaan media sosial mampu meningkatkan semangat belajar peserta didik."

embedding1 = model.encode(teks1)
embedding2 = model.encode(teks2)

similarity = model.similarity(
    embedding1,
    embedding2
)

print("Similarity:", similarity.item())