
import os
import math
import time
import requests

from sentence_transformers import SentenceTransformer


# ==========================================
# ANTIKOPAS - PERBANDINGAN EMBEDDING
# MiniLM Lokal vs Cloudflare BGE-M3
# ==========================================

MINILM_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BGE_MODEL = "@cf/baai/bge-m3"

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")


# ==========================================
# 1. DATA PENGUJIAN
# ==========================================

TEXTS = [
    (
        "Penggunaan kecerdasan buatan membantu "
        "mahasiswa memahami materi perkuliahan."
    ),
    (
        "Teknologi AI mendukung proses belajar "
        "mahasiswa agar lebih mudah memahami pelajaran."
    ),
    (
        "Petani menggunakan sistem irigasi "
        "untuk meningkatkan produksi tanaman padi."
    ),
    (
        "Pemanfaatan artificial intelligence "
        "dapat meningkatkan kemandirian mahasiswa "
        "dalam kegiatan pembelajaran."
    ),
    (
        "Ekosistem terumbu karang menyediakan "
        "habitat bagi berbagai jenis ikan laut."
    ),
]

# Pasangan indeks teks yang dibandingkan.
# Indeks dimulai dari 0.
TEST_PAIRS = [
    ("AI vs parafrasa AI", 0, 1),
    ("AI vs pembelajaran mandiri", 0, 3),
    ("AI vs pertanian", 0, 2),
    ("AI vs ekosistem laut", 0, 4),
]


# ==========================================
# 2. COSINE SIMILARITY
# ==========================================

def cosine_similarity(vector_a, vector_b):
    if len(vector_a) != len(vector_b):
        raise ValueError(
            "Dimensi vektor dalam satu model berbeda."
        )

    dot_product = sum(
        float(a) * float(b)
        for a, b in zip(vector_a, vector_b)
    )

    norm_a = math.sqrt(
        sum(float(x) ** 2 for x in vector_a)
    )

    norm_b = math.sqrt(
        sum(float(x) ** 2 for x in vector_b)
    )

    if norm_a == 0 or norm_b == 0:
        raise ValueError(
            "Embedding memiliki panjang vektor nol."
        )

    return dot_product / (norm_a * norm_b)


# ==========================================
# 3. EMBEDDING MINILM LOKAL
# ==========================================

def get_minilm_embeddings(texts):
    print("\n[MiniLM] Memuat model lokal...")

    model = SentenceTransformer(MINILM_MODEL)

    print("[MiniLM] Menghasilkan embedding...")

    start = time.perf_counter()

    embeddings = model.encode(
        texts,
        batch_size=8,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    duration = time.perf_counter() - start

    print("[MiniLM] Berhasil.")
    print("[MiniLM] Dimensi:", len(embeddings[0]))
    print(f"[MiniLM] Waktu encoding: {duration:.2f} detik")

    return embeddings, duration


# ==========================================
# 4. EMBEDDING CLOUDFLARE BGE-M3
# ==========================================

def get_bge_embeddings(texts):
    if not ACCOUNT_ID or not API_TOKEN:
        raise ValueError(
            "CLOUDFLARE_ACCOUNT_ID dan "
            "CLOUDFLARE_API_TOKEN belum terisi."
        )

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{ACCOUNT_ID}/ai/run/{BGE_MODEL}"
    )

    print("\n[BGE-M3] Menghubungi Cloudflare...")

    start = time.perf_counter()

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json",
        },
        json={"text": texts},
        timeout=90,
    )

    duration = time.perf_counter() - start

    print("[BGE-M3] HTTP Status:", response.status_code)

    if not response.ok:
        raise RuntimeError(
            "Cloudflare gagal memproses request. "
            f"HTTP {response.status_code}. "
            "Periksa izin token, kuota, dan Account ID."
        )

    payload = response.json()

    if not payload.get("success", False):
        raise RuntimeError(
            "Cloudflare mengembalikan error: "
            + str(payload.get("errors", []))
        )

    embeddings = payload.get("result", {}).get("data")

    if not isinstance(embeddings, list):
        raise ValueError(
            "Respons Cloudflare tidak memiliki data embedding."
        )

    if len(embeddings) != len(texts):
        raise ValueError(
            "Jumlah embedding BGE-M3 tidak sesuai "
            "dengan jumlah teks."
        )

    if not all(
        isinstance(vector, list) and vector
        for vector in embeddings
    ):
        raise ValueError(
            "Ada embedding BGE-M3 yang kosong "
            "atau formatnya tidak sesuai."
        )

    print("[BGE-M3] Berhasil.")
    print("[BGE-M3] Dimensi:", len(embeddings[0]))
    print(f"[BGE-M3] Waktu API: {duration:.2f} detik")

    return embeddings, duration


# ==========================================
# 5. HASIL PERBANDINGAN
# ==========================================

def main():
    print("=" * 72)
    print("ANTIKOPAS - MINILM VS CLOUDFLARE BGE-M3")
    print("=" * 72)

    print("Jumlah teks:", len(TEXTS))
    print("Jumlah pasangan uji:", len(TEST_PAIRS))

    # Menguji MiniLM lebih dulu.
    minilm_vectors, minilm_time = get_minilm_embeddings(
        TEXTS
    )

    # Menguji BGE-M3 dengan teks yang SAMA.
    bge_vectors, bge_time = get_bge_embeddings(
        TEXTS
    )

    print("\n" + "=" * 72)
    print("HASIL PERBANDINGAN COSINE SIMILARITY")
    print("=" * 72)

    print(
        f"{'Pasangan':<31}"
        f"{'MiniLM':>12}"
        f"{'BGE-M3':>12}"
    )

    print("-" * 72)

    results = {}

    for label, index_a, index_b in TEST_PAIRS:
        mini_score = cosine_similarity(
            minilm_vectors[index_a],
            minilm_vectors[index_b],
        )

        bge_score = cosine_similarity(
            bge_vectors[index_a],
            bge_vectors[index_b],
        )

        results[label] = {
            "minilm": mini_score,
            "bge": bge_score,
        }

        print(
            f"{label:<31}"
            f"{mini_score:>12.4f}"
            f"{bge_score:>12.4f}"
        )

    print("-" * 72)

    print("\nWAKTU PENGUJIAN")
    print(f"MiniLM encoding : {minilm_time:.2f} detik")
    print(f"BGE-M3 API      : {bge_time:.2f} detik")

    # Bandingkan pemisahan skor antara
    # pasangan relevan dan berbeda topik.
    relevant_labels = [
        "AI vs parafrasa AI",
        "AI vs pembelajaran mandiri",
    ]

    unrelated_labels = [
        "AI vs pertanian",
        "AI vs ekosistem laut",
    ]

    print("\n" + "=" * 72)
    print("PEMISAHAN SKOR RELEVAN VS TIDAK RELEVAN")
    print("=" * 72)

    for model_key, model_label in [
        ("minilm", "MiniLM"),
        ("bge", "BGE-M3"),
    ]:
        relevant_average = sum(
            results[label][model_key]
            for label in relevant_labels
        ) / len(relevant_labels)

        unrelated_average = sum(
            results[label][model_key]
            for label in unrelated_labels
        ) / len(unrelated_labels)

        gap = relevant_average - unrelated_average

        print(f"\n{model_label}")
        print(
            f"Rata-rata relevan       : "
            f"{relevant_average:.4f}"
        )
        print(
            f"Rata-rata berbeda topik : "
            f"{unrelated_average:.4f}"
        )
        print(f"Selisih                 : {gap:.4f}")

        if gap > 0:
            print(
                "Hasil: pasangan relevan memiliki "
                "rata-rata skor lebih tinggi."
            )
        else:
            print(
                "Hasil: model belum memisahkan "
                "pasangan uji dengan baik."
            )

    print("\n" + "=" * 72)
    print("CATATAN")
    print("=" * 72)

    print(
        "1. Skor cosine bukan persentase plagiarisme."
    )
    print(
        "2. Skor MiniLM dan BGE-M3 memiliki "
        "distribusi yang berbeda."
    )
    print(
        "3. Threshold MiniLM 0.65 tidak otomatis "
        "berlaku untuk BGE-M3."
    )
    print(
        "4. Ini uji awal, bukan evaluasi "
        "akurasi model secara menyeluruh."
    )
    print(
        "5. Academic CrossEncoder V2 tidak diubah."
    )


if __name__ == "__main__":
    try:
        main()

    except requests.exceptions.Timeout:
        print("\nERROR: Cloudflare timeout.")

    except requests.exceptions.RequestException as error:
        print(
            "\nERROR koneksi:",
            type(error).__name__,
        )

    except Exception as error:
        print(
            "\nERROR:",
            type(error).__name__,
            str(error),
        )
