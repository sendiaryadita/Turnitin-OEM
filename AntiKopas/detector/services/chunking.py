import re


def chunk_text(text, sentences_per_chunk=3):
    """
    Memecah teks menjadi beberapa text block.
    Setiap block terdiri dari beberapa kalimat.
    """

    # Bersihkan spasi berlebih
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    # Pecah berdasarkan akhir kalimat
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks = []

    for i in range(0, len(sentences), sentences_per_chunk):
        chunk = " ".join(sentences[i:i + sentences_per_chunk]).strip()

        if chunk:
            chunks.append({
                "chunk_id": len(chunks) + 1,
                "text": chunk
            })

    return chunks