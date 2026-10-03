from sentence_transformers import CrossEncoder


MODEL_PATH = "models/antikopas-cross-encoder"


model = CrossEncoder(
    MODEL_PATH,
    num_labels=1,
    max_length=512
)


pairs = [

    # 1. Sangat mirip
    (
        "Kecerdasan buatan dapat membantu meningkatkan proses pembelajaran mahasiswa.",
        "Artificial intelligence dapat digunakan untuk meningkatkan proses belajar mahasiswa."
    ),

    # 2. Topik sama tetapi isi berbeda
    (
        "Kecerdasan buatan dapat membantu meningkatkan proses pembelajaran mahasiswa.",
        "Penggunaan teknologi digital memberikan kemudahan bagi mahasiswa dalam mengakses informasi akademik."
    ),

    # 3. Tidak berhubungan
    (
        "Kecerdasan buatan dapat membantu meningkatkan proses pembelajaran mahasiswa.",
        "Sistem informasi rumah sakit digunakan untuk mengelola data pasien."
    ),

    # 4. Parafrase
    (
        "Penelitian ini menggunakan metode machine learning untuk melakukan klasifikasi data.",
        "Penelitian menggunakan algoritma pembelajaran mesin untuk mengelompokkan data."
    ),

    # 5. Hampir sama
    (
        "Sistem informasi akademik membantu mahasiswa mengakses jadwal perkuliahan.",
        "Sistem informasi akademik digunakan untuk membantu mahasiswa memperoleh jadwal perkuliahan."
    ),
]


print("=" * 60)
print("TEST MODEL ANTIKOPAS")
print("=" * 60)


scores = model.predict(pairs)


for i, score in enumerate(scores):

    print(f"\nPasangan {i + 1}")
    print("-" * 60)

    print("Text A:")
    print(pairs[i][0])

    print("\nText B:")
    print(pairs[i][1])

    print(f"\nRaw score: {float(score):.4f}")