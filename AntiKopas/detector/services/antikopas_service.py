from .full_pipeline import analyze_with_openalex
from .similarity_index import calculate_similarity_index


def analyze_antikopas(
    document_text,
    document_title=None
):

    document_results = analyze_with_openalex(
        document_text,
        document_title
    )

    index_result = calculate_similarity_index(
        document_results
    )

    return {
        "similarity_index": index_result[
            "similarity_index"
        ],
        "total_chunks": index_result[
            "total_chunks"
        ],
        "matched_chunks": index_result[
            "matched_chunks"
        ],
        "chunks": document_results
    }