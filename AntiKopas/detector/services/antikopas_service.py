
from .full_pipeline import analyze_with_openalex
from .similarity_index import calculate_similarity_index


def analyze_antikopas(document_text, document_title=None):

    # 1. Jalankan MiniLM, Cross Encoder, dan OpenAlex
    document_results = analyze_with_openalex(
        document_text,
        document_title
    )

    # 2. Hitung kemiripan total dan per jurnal
    index_result = calculate_similarity_index(
        document_results
    )

    # 3. Kembalikan hasil untuk views.py
    return {
        # Format lama agar tetap kompatibel
        "similarity_index": index_result["similarity_index"],
        "total_chunks": index_result["total_chunks"],
        "matched_chunks": index_result["matched_chunks"],
        "chunks": document_results,

        # Format baru AntiKopas
        "total_similarity": index_result["total_similarity"],
        "source_similarities": index_result["source_similarities"],
    }
