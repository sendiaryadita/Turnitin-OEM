def calculate_similarity_index(document_results):
    total_chunks = len(document_results)

    if total_chunks == 0:
        return {
            "total_chunks": 0,
            "matched_chunks": 0,
            "similarity_index": 0
        }

    matched_chunks = sum(
        1
        for chunk in document_results
        if any(match.get("matched") for match in chunk.get("matches", []))
    )

    similarity_index = (matched_chunks / total_chunks) * 100

    return {
        "total_chunks": total_chunks,
        "matched_chunks": matched_chunks,
        "similarity_index": round(similarity_index, 2)
    }