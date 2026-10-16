
"""
AntiKopas - Cloudflare BGE-M3 Embedding Service

Menggantikan fungsi embedding MiniLM secara bertahap.

- Menggunakan Cloudflare Workers AI REST API
- Mendukung banyak teks (batch)
- Mengembalikan PyTorch Tensor
- Kompatibel dengan sentence_transformers.util.cos_sim
- Tidak mengubah Academic CrossEncoder V2
"""

import os
import time

import numpy as np
import requests
import torch


class CloudflareBGEEmbedding:

    MODEL = "@cf/baai/bge-m3"
    EMBEDDING_DIMENSION = 1024

    # Batasi jumlah teks per request supaya
    # proses dokumen besar lebih terkendali.
    MAX_BATCH_SIZE = 12

    RETRYABLE_STATUS = {
        429, 500, 502, 503, 504
    }

    def __init__(self):
        print(
            "[AntiKopas] Cloudflare BGE-M3 "
            "embedding service siap."
        )

    def _get_credentials(self):

        account_id = os.getenv(
            "CLOUDFLARE_ACCOUNT_ID", ""
        ).strip()

        api_token = os.getenv(
            "CLOUDFLARE_API_TOKEN", ""
        ).strip()

        if not account_id or not api_token:
            raise RuntimeError(
                "Cloudflare belum dikonfigurasi. "
                "Isi CLOUDFLARE_ACCOUNT_ID dan "
                "CLOUDFLARE_API_TOKEN pada "
                "environment terminal Django."
            )

        return account_id, api_token

    def _request_batch(self, texts):

        account_id, api_token = (
            self._get_credentials()
        )

        url = (
            "https://api.cloudflare.com/client/v4/"
            f"accounts/{account_id}/ai/run/"
            f"{self.MODEL}"
        )

        headers = {
            "Authorization": (
                f"Bearer {api_token}"
            ),
            "Content-Type": "application/json",
        }

        # Retry sekali untuk kesalahan sementara.
        for attempt in range(2):

            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json={"text": texts},
                    timeout=(10, 60),
                )

            except requests.RequestException as error:
                if attempt == 0:
                    time.sleep(2)
                    continue

                raise RuntimeError(
                    "Gagal menghubungi Cloudflare: "
                    + type(error).__name__
                ) from error

            if (
                response.status_code
                in self.RETRYABLE_STATUS
                and attempt == 0
            ):
                print(
                    "[BGE-M3] Gangguan sementara. "
                    "Mengulang request..."
                )
                time.sleep(2)
                continue

            if not response.ok:
                raise RuntimeError(
                    "Cloudflare Workers AI gagal. "
                    f"HTTP {response.status_code}. "
                    "Periksa token, izin, kuota, "
                    "dan layanan Cloudflare."
                )

            try:
                payload = response.json()
            except ValueError as error:
                raise RuntimeError(
                    "Respons Cloudflare bukan JSON."
                ) from error

            if not payload.get("success", False):
                raise RuntimeError(
                    "Cloudflare mengembalikan "
                    "status success=false."
                )

            result = payload.get("result", {})

            if not isinstance(result, dict):
                raise RuntimeError(
                    "Format result Cloudflare "
                    "tidak valid."
                )

            vectors = result.get("data")

            if (
                not isinstance(vectors, list)
                or len(vectors) != len(texts)
            ):
                raise RuntimeError(
                    "Jumlah embedding Cloudflare "
                    "tidak sesuai dengan jumlah teks."
                )

            try:
                array = np.asarray(
                    vectors,
                    dtype=np.float32,
                )
            except (ValueError, TypeError) as error:
                raise RuntimeError(
                    "Embedding Cloudflare "
                    "tidak dapat dibaca."
                ) from error

            if (
                array.ndim != 2
                or array.shape[0] != len(texts)
                or array.shape[1]
                != self.EMBEDDING_DIMENSION
            ):
                raise RuntimeError(
                    "Dimensi embedding tidak sesuai. "
                    f"Didapat: {array.shape}"
                )

            if not np.isfinite(array).all():
                raise RuntimeError(
                    "Embedding mengandung nilai "
                    "NaN atau infinity."
                )

            return array

        raise RuntimeError(
            "Request Cloudflare gagal "
            "setelah percobaan ulang."
        )

    def encode(
        self,
        texts,
        batch_size=16,
        convert_to_tensor=True,
        show_progress_bar=False,
    ):
        """
        Antarmuka kompatibel dengan penggunaan
        SentenceTransformer.encode() di
        full_pipeline.py.

        Keluaran:
        - torch.Tensor jika convert_to_tensor=True
        - numpy.ndarray jika False
        """

        single_text = isinstance(texts, str)

        if single_text:
            texts = [texts]

        texts = list(texts)

        if not texts:
            raise ValueError(
                "Daftar teks untuk embedding kosong."
            )

        if any(
            not isinstance(text, str)
            or not text.strip()
            for text in texts
        ):
            raise ValueError(
                "Setiap input embedding harus "
                "berupa teks yang tidak kosong."
            )

        effective_batch_size = min(
            max(1, int(batch_size)),
            self.MAX_BATCH_SIZE,
        )

        all_vectors = []

        total_batches = (
            len(texts) + effective_batch_size - 1
        ) // effective_batch_size

        print(
            f"[BGE-M3] Memproses {len(texts)} teks "
            f"dalam {total_batches} batch."
        )

        for start in range(
            0,
            len(texts),
            effective_batch_size,
        ):

            batch = texts[
                start:start + effective_batch_size
            ]

            vectors = self._request_batch(batch)

            all_vectors.append(vectors)

            batch_number = (
                start // effective_batch_size
            ) + 1

            print(
                f"[BGE-M3] Batch "
                f"{batch_number}/{total_batches} "
                "berhasil."
            )

        embeddings = np.concatenate(
            all_vectors,
            axis=0,
        )

        if convert_to_tensor:
            output = torch.from_numpy(
                embeddings
            )
        else:
            output = embeddings

        if single_text:
            return output[0]

        return output
