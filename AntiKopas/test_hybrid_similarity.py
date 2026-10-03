import sys
import os

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from detector.services.hybrid_similarity import (
    calculate_hybrid_similarity
)


pairs = [

    (
        "Kecerdasan buatan dapat membantu meningkatkan proses pembelajaran mahasiswa.",
        "Artificial intelligence dapat digunakan untuk meningkatkan proses belajar mahasiswa."
    ),

    (
        "Kecerdasan buatan dapat membantu meningkatkan proses pembelajaran mahasiswa.",
        "Penggunaan teknologi digital memberikan kemudahan bagi mahasiswa dalam mengakses informasi akademik."
    ),

    (
        "Kecerdasan buatan dapat membantu meningkatkan proses pembelajaran mahasiswa.",
        "Sistem informasi rumah sakit digunakan untuk mengelola data pasien."
    ),

    (
        "Penelitian ini menggunakan metode machine learning untuk melakukan klasifikasi data.",
        "Penelitian menggunakan algoritma pembelajaran mesin untuk mengelompokkan data."
    ),

    (
        "Sistem informasi akademik membantu mahasiswa mengakses jadwal perkuliahan.",
        "Sistem informasi akademik digunakan untuk membantu mahasiswa memperoleh jadwal perkuliahan."
    )
]


print("=" * 60)
print("HYBRID SIMILARITY TEST")
print("=" * 60)


for i, (document, source) in enumerate(
    pairs,
    start=1
):

    result = calculate_hybrid_similarity(
        document,
        source
    )

    print(f"\nPAIR {i}")
    print("-" * 60)

    print(
        f"MiniLM Score : "
        f"{result['minilm_score']:.4f}"
    )

    if result["cross_score"] is None:

        print(
            "Cross Score  : SKIPPED"
        )

    else:

        print(
            f"Cross Score  : "
            f"{result['cross_score']:.4f}"
        )

    print(
        f"Matched      : "
        f"{result['matched']}"
    )