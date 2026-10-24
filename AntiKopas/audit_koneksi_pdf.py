
"""
AK_08.1 - Diagnosis koneksi PDF jurnal

Tidak mengubah backend.
Tidak memakai Cloudflare.
Tidak menyimpan PDF ke disk.
"""

import time

import requests

from detector.services.openalex import PDF_HEADERS


PDF_URL = "https://arxiv.org/pdf/1706.03762"

MAX_BYTES = 6 * 1024 * 1024


def main():
    print("=" * 55)
    print("ANTIKOPAS - DIAGNOSIS URL PDF")
    print("=" * 55)

    start = time.perf_counter()

    try:
        with requests.get(
            PDF_URL,
            headers=PDF_HEADERS,
            timeout=(5, 12),
            stream=True,
            allow_redirects=False,
        ) as response:

            print("HTTP Status:", response.status_code)

            print(
                "Content-Type:",
                response.headers.get("Content-Type"),
            )

            print(
                "Content-Length:",
                response.headers.get("Content-Length"),
            )

            if response.is_redirect:
                print(
                    "Status: REDIRECT"
                )
                print(
                    "Lokasi tujuan:",
                    response.headers.get("Location"),
                )
                return

            if response.status_code != 200:
                print(
                    "Status: SERVER MENOLAK REQUEST"
                )
                return

            chunks = []
            total_bytes = 0

            for chunk in response.iter_content(
                chunk_size=65536
            ):
                if not chunk:
                    continue

                total_bytes += len(chunk)

                if total_bytes > MAX_BYTES:
                    print(
                        "Status: PDF MELEBIHI 6 MB"
                    )
                    return

                chunks.append(chunk)

            pdf_data = b"".join(chunks)

            print(
                "Ukuran respons:",
                round(len(pdf_data) / 1024, 2),
                "KB",
            )

            if not pdf_data.lstrip().startswith(b"%PDF-"):
                print(
                    "Status: RESPONS BUKAN FILE PDF"
                )
                return

            print("Status download: PDF VALID")

            import pymupdf

            with pymupdf.open(
                stream=pdf_data,
                filetype="pdf",
            ) as document:

                print(
                    "Jumlah halaman:",
                    len(document),
                )

                print(
                    "Karakter halaman pertama:",
                    len(document[0].get_text()),
                )

                if len(document) > 1:
                    print(
                        "Karakter halaman kedua:",
                        len(document[1].get_text()),
                    )

    except requests.exceptions.ConnectTimeout:
        print("Status: CONNECT TIMEOUT")

    except requests.exceptions.ReadTimeout:
        print("Status: READ TIMEOUT")

    except requests.exceptions.ConnectionError as error:
        print("Status: CONNECTION ERROR")
        print("Detail:", str(error)[:350])

    except requests.exceptions.RequestException as error:
        print("Status: REQUEST ERROR")
        print("Detail:", str(error)[:350])

    except Exception as error:
        print("Status: ERROR LAIN")
        print("Jenis:", type(error).__name__)
        print("Detail:", str(error)[:350])

    finally:
        print(
            "Waktu total:",
            round(time.perf_counter() - start, 2),
            "detik",
        )


if __name__ == "__main__":
    main()
