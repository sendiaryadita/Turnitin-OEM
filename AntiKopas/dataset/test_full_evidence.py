import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from detector.services.full_pipeline import analyze_with_openalex


document_text = """
Kecerdasan buatan dapat membantu meningkatkan proses pembelajaran mahasiswa.
Sistem pembelajaran berbasis AI dapat memberikan materi yang sesuai dengan kebutuhan mahasiswa.
Teknologi ini juga dapat membantu dosen menganalisis aktivitas pembelajaran.
"""


print("=" * 60)
print("ANTIKOPAS EVIDENCE TEST")
print("=" * 60)


results = analyze_with_openalex(
    document_text
)


for result in results:

    print("\n" + "=" * 60)
    print(
        f"CHUNK {result['chunk_index']}"
    )
    print("=" * 60)

    print(result["chunk_text"])

    print("\nMATCHES:")

    for rank, match in enumerate(
        result["matches"],
        start=1
    ):

        print("\n" + "-" * 60)

        print("Rank :", rank)
        print("Title:", match["title"])
        print("Year :", match["year"])
        print("DOI  :", match["doi"])
        print("URL  :", match["url"])

        print(
            "MiniLM:",
            round(
                match["minilm_score"],
                4
            )
        )

        print(
            "Cross:",
            round(
                match["cross_score"],
                4
            )
        )

        print(
            "Matched:",
            match["matched"]
        )