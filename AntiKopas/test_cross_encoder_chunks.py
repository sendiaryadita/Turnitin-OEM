from sentence_transformers import CrossEncoder
import torch

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L6-v2"

print("Loading model...")

model = CrossEncoder(
    MODEL_NAME,
    activation_fn=torch.nn.Sigmoid()
)

print("Model berhasil dimuat!\n")


# Simulasi chunk dari dokumen mahasiswa
document_chunks = [
    "Kecerdasan buatan dapat membantu meningkatkan proses pembelajaran mahasiswa melalui sistem pembelajaran yang lebih adaptif.",
    
    "Penelitian ini menggunakan metode machine learning untuk melakukan klasifikasi terhadap data yang telah dikumpulkan.",
    
    "Sistem informasi akademik digunakan untuk membantu mahasiswa dalam mengakses jadwal dan informasi perkuliahan."
]


# Simulasi sumber literatur
source_chunks = [
    "Artificial intelligence dapat digunakan untuk meningkatkan proses belajar mahasiswa melalui pembelajaran adaptif.",
    
    "Algoritma pembelajaran mesin dapat digunakan untuk mengelompokkan dan mengklasifikasikan data penelitian.",
    
    "Sistem informasi akademik membantu mahasiswa memperoleh informasi mengenai jadwal dan kegiatan perkuliahan.",
    
    "Rumah sakit menggunakan sistem informasi untuk mengelola data pasien dan pelayanan kesehatan."
]


# Buat semua pasangan chunk
pairs = []

for doc_chunk in document_chunks:
    for source_chunk in source_chunks:
        pairs.append((doc_chunk, source_chunk))


# Prediksi
scores = model.predict(pairs)


print("=== HASIL CROSS ENCODER CHUNK ===")

index = 0

for i, doc_chunk in enumerate(document_chunks):
    print(f"\n{'=' * 60}")
    print(f"DOKUMEN CHUNK {i + 1}")
    print(f"{doc_chunk}")

    results = []

    for j, source_chunk in enumerate(source_chunks):
        score = float(scores[index])

        results.append({
            "source_index": j + 1,
            "score": score,
            "text": source_chunk
        })

        index += 1

    # Urutkan dari skor tertinggi
    results.sort(key=lambda x: x["score"], reverse=True)

    print("\nRanking sumber:")

    for rank, result in enumerate(results, start=1):
        print(
            f"\n{rank}. Source {result['source_index']}"
            f" | Score: {result['score']:.4f}"
        )
        print(f"   {result['text']}")