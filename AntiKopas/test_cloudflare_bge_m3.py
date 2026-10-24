
import os
import math
import requests


# ==========================================
# ANTIKOPAS - TEST CLOUDFLARE BGE-M3
# Tidak mengubah pipeline utama
# ==========================================

MODEL = "@cf/baai/bge-m3"

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")


def cosine_similarity(vector_a, vector_b):
    if len(vector_a) != len(vector_b):
        raise ValueError("Dimensi embedding berbeda.")

    dot_product = sum(
        a * b for a, b in zip(vector_a, vector_b)
    )

    norm_a = math.sqrt(sum(x * x for x in vector_a))
    norm_b = math.sqrt(sum(x * x for x in vector_b))

    if norm_a == 0 or norm_b == 0:
        raise ValueError("Embedding kosong atau nol.")

    return dot_product / (norm_a * norm_b)


def main():
    if not ACCOUNT_ID or not API_TOKEN:
        print(
            "ERROR: Environment variable "
            "CLOUDFLARE_ACCOUNT_ID dan "
            "CLOUDFLARE_API_TOKEN wajib diisi."
        )
        return

    # Contoh kalimat mirip dan berbeda topik
    texts = [
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
    ]

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{ACCOUNT_ID}/ai/run/{MODEL}"
    )

    print("=" * 55)
    print("ANTIKOPAS - CLOUDFLARE BGE-M3 TEST")
    print("=" * 55)
    print("Model:", MODEL)
    print("Jumlah teks:", len(texts))
    print("Menghubungi Cloudflare Workers AI...")

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {API_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"text": texts},
            timeout=90,
        )

        print("HTTP Status:", response.status_code)

        if not response.ok:
            print("Request gagal.")
            print("Periksa token, izin Workers AI, dan Account ID.")
            print("Detail:", response.text[:600])
            return

        payload = response.json()

        if not payload.get("success", False):
            print("Cloudflare mengembalikan error:")
            print(payload.get("errors", []))
            return

        result = payload.get("result", {})
        embeddings = result.get("data", [])

        if len(embeddings) != 3:
            print("Format embedding tidak sesuai.")
            print("Jumlah embedding:", len(embeddings))
            return

        print("\nBerhasil mendapatkan embedding!")
        print("Dimensi embedding:", len(embeddings[0]))

        similar_score = cosine_similarity(
            embeddings[0], embeddings[1]
        )

        different_score = cosine_similarity(
            embeddings[0], embeddings[2]
        )

        print("\n" + "=" * 55)
        print("HASIL COSINE SIMILARITY")
        print("=" * 55)

        print("\nA. AI untuk pembelajaran")
        print("B. Teknologi AI membantu belajar")
        print(f"Skor A vs B: {similar_score:.4f}")

        print("\nA. AI untuk pembelajaran")
        print("C. Irigasi dan tanaman padi")
        print(f"Skor A vs C: {different_score:.4f}")

        print("\n" + "=" * 55)

        if similar_score > different_score:
            print("HASIL: Pasangan relevan memiliki skor lebih tinggi.")
        else:
            print("HASIL: Perlu evaluasi lebih lanjut.")

        print(
            "\nCatatan: skor cosine bukan "
            "persentase plagiarisme."
        )

    except requests.exceptions.Timeout:
        print("ERROR: Request Cloudflare timeout.")

    except requests.exceptions.RequestException as error:
        print("ERROR koneksi:", type(error).__name__)

    except (ValueError, TypeError, KeyError) as error:
        print("ERROR pemrosesan respons:", str(error))


if __name__ == "__main__":
    main()
