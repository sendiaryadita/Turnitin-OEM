def split_into_chunks(text, max_words=100):
    """
    Membagi teks menjadi beberapa chunk berdasarkan jumlah kata.
    """

    words = text.split()

    chunks = []

    for i in range(0, len(words), max_words):
        chunk_words = words[i:i + max_words]

        chunks.append({
            "chunk_id": len(chunks) + 1,
            "text": " ".join(chunk_words)
        })

    return chunks