import requests
from sentence_transformers import SentenceTransformer

# ==========================================
# 1. LOAD MODEL MINILM
# ==========================================

print("Memuat model MiniLM...")

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

print("Model berhasil dimuat!\n")


# ==========================================
# 2. INPUT JUDUL MAHASISWA
# ==========================================

judul_mahasiswa = input("Masukkan judul karya tulis: ")

print("\nMencari artikel di OpenAlex...")


# ==========================================
# 3. REQUEST KE OPENALEX
# ==========================================

url = "https://api.openalex.org/works"

params = {
    "search": judul_mahasiswa,
    "per-page": 10
}

response = requests.get(url, params=params)


# ==========================================
# 4. CEK RESPONSE
# ==========================================

if response.status_code != 200:
    print("Gagal mengakses OpenAlex.")
    print("Status:", response.status_code)
    print(response.text)
    exit()


data = response.json()

print(f"Ditemukan {data['meta']['count']} artikel.")
print("Menampilkan 10 artikel pertama.\n")


# ==========================================
# 5. EMBEDDING JUDUL MAHASISWA
# ==========================================

embedding_mahasiswa = model.encode(judul_mahasiswa)


# ==========================================
# 6. BANDINKAN DENGAN JUDUL ARTIKEL
# ==========================================

hasil = []

for article in data["results"]:

    judul_artikel = article.get("title")

    if not judul_artikel:
        continue

    # Buat embedding judul artikel
    embedding_artikel = model.encode(judul_artikel)

    # Hitung similarity
    similarity = model.similarity(
        embedding_mahasiswa,
        embedding_artikel
    ).item()

    hasil.append({
        "title": judul_artikel,
        "similarity": similarity,
        "year": article.get("publication_year"),
        "doi": article.get("doi"),
        "openalex_id": article.get("id")
    })


# ==========================================
# 7. URUTKAN
# ==========================================

hasil.sort(
    key=lambda x: x["similarity"],
    reverse=True
)


# ==========================================
# 8. TAMPILKAN HASIL
# ==========================================

print("=" * 80)
print("HASIL ANALISIS KEMIRIPAN")
print("=" * 80)

for i, article in enumerate(hasil, start=1):

    print(f"\n{i}. {article['title']}")
    print(f"   Similarity : {article['similarity']:.4f}")
    print(f"   Tahun      : {article['year']}")
    print(f"   DOI        : {article['doi']}")
    print(f"   OpenAlex   : {article['openalex_id']}")

print("\n" + "=" * 80)