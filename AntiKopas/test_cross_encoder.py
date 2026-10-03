from sentence_transformers import CrossEncoder
import torch

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L6-v2"

print("Loading model...")

model = CrossEncoder(
    MODEL_NAME,
    activation_fn=torch.nn.Sigmoid()
)

print("Model berhasil dimuat!\n")


pairs = [
    (
        "Kecerdasan buatan dapat membantu meningkatkan proses pembelajaran mahasiswa.",
        "Artificial intelligence dapat digunakan untuk meningkatkan kegiatan belajar mahasiswa."
    ),
    (
        "Kecerdasan buatan dapat membantu meningkatkan proses pembelajaran mahasiswa.",
        "Sistem informasi rumah sakit digunakan untuk mengelola data pasien."
    ),
    (
        "Penelitian ini menggunakan metode machine learning untuk klasifikasi data.",
        "Penelitian menggunakan algoritma pembelajaran mesin untuk mengelompokkan data."
    )
]


scores = model.predict(pairs)

print("=== HASIL CROSS ENCODER ===")

for i, score in enumerate(scores):
    print(f"\nPasangan {i + 1}")
    print(f"Text A : {pairs[i][0]}")
    print(f"Text B : {pairs[i][1]}")
    print(f"Score  : {score:.4f}")