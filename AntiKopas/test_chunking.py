from detector.services.chunking import chunk_text


text = """
Penggunaan media sosial telah berkembang pesat dalam kehidupan masyarakat.
Media sosial digunakan untuk berkomunikasi dan memperoleh informasi.
Namun penggunaan yang berlebihan dapat memberikan dampak terhadap remaja.

Remaja merupakan kelompok yang cukup aktif menggunakan media sosial.
Penggunaan media sosial secara berlebihan dapat memengaruhi pola tidur.
Selain itu, penggunaan yang terlalu lama dapat mengurangi aktivitas fisik.

Oleh karena itu diperlukan penggunaan media sosial secara bijak.
Orang tua dan lingkungan sekolah juga memiliki peran dalam memberikan edukasi.
"""


chunks = chunk_text(text, sentences_per_chunk=3)


print("\n=== HASIL TEXT CHUNKING ===")

for chunk in chunks:
    print(f"\nChunk {chunk['chunk_id']}")
    print(chunk["text"])