
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
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
import torch


class CloudflareBGEEmbedding:

    MODEL = "@cf/baai/bge-m3"
    EMBEDDING_DIMENSION = 1024

    # Batasi jumlah teks per request supaya
    # proses dokumen besar lebih terkendali.
    MAX_BATCH_SIZE = 12
    MAX_CONCURRENT_BATCHES = 2

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
        progress_callback=None,
        progress_label="Embedding teks",
        embedding_cache=None,
    ):
        """
        Antarmuka kompatibel dengan penggunaan
        SentenceTransformer.encode() di
        full_pipeline.py.

        Keluaran:
        - torch.Tensor jika convert_to_tensor=True
        - numpy.ndarray jika False

        progress_callback bersifat opsional. Jika diberikan,
        callback menerima dictionary progres setelah setiap batch
        berhasil. Tanpa callback, perilaku lama tetap sama.

        embedding_cache opsional harus dibuat baru untuk setiap scan.
        Hanya teks yang belum tersedia di cache dikirim ke API.
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

        # Cache diberikan oleh satu proses scan, bukan disimpan lintas user.
        # Teks identik menggunakan kembali vektor tanpa mengubah isinya.
        requested_texts = texts
        if embedding_cache is not None:
            texts = list(dict.fromkeys(
                text for text in texts if text not in embedding_cache
            ))

        if not texts:
            embeddings = np.stack([
                embedding_cache[text] for text in requested_texts
            ])
            output = torch.from_numpy(embeddings) if convert_to_tensor else embeddings
            return output[0] if single_text else output

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

        batches = [
            texts[start:start + effective_batch_size]
            for start in range(0, len(texts), effective_batch_size)
        ]
        executor = ThreadPoolExecutor(
            max_workers=min(self.MAX_CONCURRENT_BATCHES, total_batches)
        )
        try:
            # map mempertahankan urutan input meski request selesai tidak berurutan.
            vectors_by_batch = executor.map(self._request_batch, batches)
            for batch_number, vectors in enumerate(vectors_by_batch, start=1):
                all_vectors.append(vectors)
                self._report_batch_progress(
                    batch_number, total_batches,
                    min(batch_number * effective_batch_size, len(texts)),
                    len(texts), progress_callback, progress_label,
                )
        finally:
            executor.shutdown(wait=True, cancel_futures=True)

        embeddings = np.concatenate(all_vectors, axis=0)
        if embedding_cache is not None:
            embedding_cache.update(zip(texts, embeddings))
            embeddings = np.stack([
                embedding_cache[text] for text in requested_texts
            ])

        output = torch.from_numpy(embeddings) if convert_to_tensor else embeddings
        return output[0] if single_text else output

    def _report_batch_progress(
        self, batch_number, total_batches, completed_items,
        total_items, progress_callback, progress_label,
    ):

        print(
            f"[BGE-M3] Batch "
            f"{batch_number}/{total_batches} "
            "berhasil."
        )

        # Callback tetap berurutan dan dijalankan di thread pemanggil.
        if callable(progress_callback):
            progress_data = {
                "event": "embedding_batch_completed",
                "stage": str(progress_label),
                "completed_batches": batch_number,
                "total_batches": total_batches,
                "completed_items": completed_items,
                "total_items": total_items,
                "fraction": completed_items / total_items,
            }
            try:
                progress_callback(progress_data)
            except Exception as error:
                print(
                    "[BGE-M3] Peringatan: callback progress gagal:",
                    type(error).__name__,
                )
