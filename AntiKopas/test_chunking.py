from detector.services.chunking import split_into_chunks


text = """
Regulasi emosi merupakan kemampuan seseorang dalam mengatur dan
mengendalikan respons emosional ketika menghadapi berbagai situasi.
Kemampuan ini penting bagi remaja karena pada masa perkembangan
tersebut individu mengalami berbagai perubahan emosional dan sosial.
Regulasi emosi yang baik membantu seseorang menghadapi tekanan,
menyelesaikan masalah, dan berinteraksi dengan lingkungan secara lebih baik.
"""


chunks = split_into_chunks(
    text,
    max_words=20
)


for chunk in chunks:
    print("\n====================")
    print("Chunk ID:", chunk["chunk_id"])
    print("Text:", chunk["text"])