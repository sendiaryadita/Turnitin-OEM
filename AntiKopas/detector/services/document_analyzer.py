import re


def chunk_text(text, max_sentences=10):
    """
    Memecah dokumen berdasarkan kalimat.
    Maksimal 3 kalimat per chunk.
    """

    if not text:
        return []

    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)

    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    chunks = []

    for i in range(0, len(sentences), max_sentences):
        chunk = " ".join(sentences[i:i + max_sentences])
        chunks.append(chunk)

    return chunks


def analyze_document(document_text, source_texts):
    """
    Membandingkan seluruh chunk dokumen
    dengan kumpulan sumber.

    Return:
    [
        {
            "chunk_index": 1,
            "chunk_text": "...",
            "matches": [
                {
                    "source_index": 1,
                    "source_text": "...",
                    "minilm_score": 0.72,
                    "cross_score": 7.31,
                    "matched": True
                }
            ]
        }
    ]
    """

    from .hybrid_similarity import calculate_hybrid_similarity

    chunks = chunk_text(document_text)

    document_results = []

    for chunk_index, chunk in enumerate(chunks, start=1):

        matches = []

        for source_index, source_text in enumerate(
            source_texts,
            start=1
        ):

            if not source_text:
                continue

            result = calculate_hybrid_similarity(
                chunk,
                source_text
            )

            matches.append({
                "source_index": source_index,
                "source_text": source_text,
                "minilm_score": result["minilm_score"],
                "cross_score": result["cross_score"],
                "matched": result["matched"],
            })

        # Urutkan dari Cross Encoder tertinggi
        matches.sort(
            key=lambda x: (
                x["cross_score"]
                if x["cross_score"] is not None
                else float("-inf")
            ),
            reverse=True
        )

        document_results.append({
            "chunk_index": chunk_index,
            "chunk_text": chunk,
            "matches": matches
        })

    return document_results
