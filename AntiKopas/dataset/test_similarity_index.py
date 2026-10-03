import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from detector.services.similarity_index import calculate_similarity_index


document_results = [
    {
        "chunk_index": 1,
        "chunk_text": "Chunk pertama",
        "matches": [
            {
                "cross_score": 5.2
            }
        ]
    },
    {
        "chunk_index": 2,
        "chunk_text": "Chunk kedua",
        "matches": [
            {
                "cross_score": -2.1
            }
        ]
    },
    {
        "chunk_index": 3,
        "chunk_text": "Chunk ketiga",
        "matches": [
            {
                "cross_score": 4.8
            }
        ]
    },
    {
        "chunk_index": 4,
        "chunk_text": "Chunk keempat",
        "matches": [
            {
                "cross_score": -1.5
            }
        ]
    }
]


result = calculate_similarity_index(
    document_results,
    cross_threshold=0.05
)


print("=" * 60)
print("SIMILARITY INDEX TEST")
print("=" * 60)

print("Total chunk     :", result["total_chunks"])
print("Matched chunk   :", result["matched_chunks"])
print("Similarity Index:", result["similarity_index"], "%")