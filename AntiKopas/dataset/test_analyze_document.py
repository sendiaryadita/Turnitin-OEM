import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from detector.services.document_analyzer import analyze_document


document_text = """
Kecerdasan buatan dapat membantu meningkatkan proses pembelajaran mahasiswa.
Sistem pembelajaran berbasis AI dapat memberikan materi yang sesuai dengan kebutuhan mahasiswa.
Teknologi ini juga dapat membantu dosen menganalisis aktivitas pembelajaran.
"""


source_texts = [
    """
    Artificial intelligence dapat digunakan untuk meningkatkan proses belajar mahasiswa.
    Sistem pembelajaran adaptif dapat memberikan materi sesuai kebutuhan dan kemampuan mahasiswa.
    """,

    """
    Sistem informasi akademik membantu mahasiswa memperoleh jadwal kuliah,
    informasi mata kuliah, dan informasi akademik lainnya.
    """,

    """
    Rumah sakit menggunakan sistem informasi untuk mengelola data pasien
    dan pelayanan kesehatan.
    """
]


print("=" * 60)
print("DOCUMENT ANALYSIS TEST")
print("=" * 60)

results = analyze_document(
    document_text,
    source_texts
)

for result in results:

    print("\n" + "-" * 60)

    print("CHUNK :", result["chunk_index"])
    print("SOURCE:", result["source_index"])

    print("\nText:")
    print(result["chunk_text"])

    print("\nMiniLM Score :", round(result["minilm_score"], 4))

    if result["cross_score"] is not None:
        print(
            "Cross Score  :",
            round(result["cross_score"], 4)
        )
    else:
        print("Cross Score  : SKIPPED")

    print("Matched      :", result["matched"])