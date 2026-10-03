import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from detector.services.antikopas_service import analyze_antikopas


document_text = """
Rumah sakit menggunakan sistem informasi untuk mengelola data pasien.
Sistem tersebut membantu petugas kesehatan dalam mencatat informasi
pasien dan mengelola pelayanan kesehatan.
"""


print("=" * 60)
print("ANTIKOPAS SERVICE TEST")
print("=" * 60)


result = analyze_antikopas(
    document_text
)


print("\nHASIL AKHIR")
print("-" * 60)

print(
    "Similarity Index :",
    result["similarity_index"],
    "%"
)

print(
    "Total Chunk      :",
    result["total_chunks"]
)

print(
    "Matched Chunk    :",
    result["matched_chunks"]
)


print("\nEVIDENCE")
print("-" * 60)


for chunk in result["chunks"]:

    print(
        f"\nChunk {chunk['chunk_index']}"
    )

    print(
        chunk["chunk_text"]
    )

    for match in chunk["matches"][:3]:

        print(
            f"\n  {match['title']}"
        )

        print(
            f"  Tahun  : {match['year']}"
        )

        print(
            f"  DOI    : {match['doi']}"
        )

        print(
            f"  MiniLM : {match['minilm_score']:.4f}"
        )

        print(
            f"  Cross  : {match['cross_score']:.4f}"
        )

        print(
            f"  Match  : {match['matched']}"
        )