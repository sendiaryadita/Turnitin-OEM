"""Regresi optimasi embedding; tidak memakai API atau database."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, get_ident
from unittest import TestCase
from unittest.mock import patch

import numpy as np
import requests
import torch

from .services.cloudflare_embeddings import CloudflareBGEEmbedding


class EmbeddingPerformanceTests(TestCase):
    def setUp(self):
        self.model = CloudflareBGEEmbedding()

    @staticmethod
    def vectors(texts):
        return np.asarray([
            [float(sum(text.encode("utf-8")))] * 1024 for text in texts
        ], dtype=np.float32)

    def test_parallel_batches_preserve_order_and_progress_thread(self):
        both_started = Barrier(2)
        second_completed = Event()
        caller_thread = get_ident()
        callbacks = []

        def request(batch):
            both_started.wait(timeout=5)
            if batch == ["first"]:
                self.assertTrue(second_completed.wait(timeout=5))
            else:
                second_completed.set()
            return self.vectors(batch)

        def progress(data):
            self.assertEqual(get_ident(), caller_thread)
            callbacks.append(data)

        with patch.object(self.model, "_request_batch", side_effect=request):
            actual = self.model.encode(
                ["first", "second"], batch_size=1,
                convert_to_tensor=False, progress_callback=progress,
            )
        np.testing.assert_array_equal(actual, self.vectors(["first", "second"]))
        self.assertEqual([item["fraction"] for item in callbacks], [0.5, 1.0])

    def test_rebuild_reuses_unchanged_text_and_restores_duplicates(self):
        cache = {}
        initial = ["abstract A", "abstract B", "abstract A"]
        rebuilt = ["new full text", "abstract B", "new full text"]
        with patch.object(self.model, "_request_batch", side_effect=self.vectors) as request:
            initial_vectors = self.model.encode(
                initial, embedding_cache=cache, convert_to_tensor=False,
            )
            actual = self.model.encode(rebuilt, embedding_cache=cache)
            np.testing.assert_array_equal(initial_vectors, self.vectors(initial))
            np.testing.assert_array_equal(actual.numpy(), self.vectors(rebuilt))
            self.assertEqual(request.call_args_list[0].args[0], initial[:2])
            self.assertEqual(request.call_args_list[1].args[0], ["new full text"])
            request.reset_mock()
            self.model.encode(rebuilt, embedding_cache=cache)
            request.assert_not_called()

    def test_cache_is_not_retained_by_model_between_scans(self):
        with patch.object(self.model, "_request_batch", side_effect=self.vectors) as request:
            self.model.encode(["same text"], embedding_cache={})
            self.model.encode(["same text"], embedding_cache={})
        self.assertEqual(request.call_count, 2)

    def test_concurrent_scans_keep_their_own_vectors(self):
        ready = Barrier(2)

        def scan(private_text):
            cache = {}
            ready.wait(timeout=5)
            result = self.model.encode(["shared", private_text], embedding_cache=cache)
            return result, cache

        with patch.object(self.model, "_request_batch", side_effect=self.vectors):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(scan, ["private A", "private B"]))
        for (result, cache), private_text in zip(results, ["private A", "private B"]):
            np.testing.assert_array_equal(result.numpy(), self.vectors(["shared", private_text]))
            self.assertEqual(set(cache), {"shared", private_text})
        self.assertIsNot(results[0][1], results[1][1])

    def test_single_text_tensor_and_batch_limit_remain_supported(self):
        with patch.object(self.model, "_request_batch", side_effect=self.vectors) as request:
            vector = self.model.encode("single")
            self.assertIsInstance(vector, torch.Tensor)
            self.assertEqual(tuple(vector.shape), (1024,))
            result = self.model.encode([str(i) for i in range(25)], batch_size=100)
            self.assertEqual(tuple(result.shape), (25, 1024))
            self.assertTrue(all(len(call.args[0]) <= 12 for call in request.call_args_list))

    def test_failed_batch_never_returns_partial_results_or_updates_cache(self):
        cache = {}

        def request(batch):
            if batch == ["fail"]:
                raise RuntimeError("Cloudflare unavailable")
            return self.vectors(batch)

        with patch.object(self.model, "_request_batch", side_effect=request):
            with self.assertRaisesRegex(RuntimeError, "Cloudflare unavailable"):
                self.model.encode(["ok", "fail"], batch_size=1, embedding_cache=cache)
        self.assertEqual(cache, {})

    def test_callback_failure_does_not_change_embeddings(self):
        with patch.object(self.model, "_request_batch", side_effect=self.vectors):
            actual = self.model.encode(
                ["text"], convert_to_tensor=False,
                progress_callback=lambda _: 1 / 0,
            )
        np.testing.assert_array_equal(actual, self.vectors(["text"]))

    def test_input_validation_remains_strict(self):
        for texts in [[], [""], ["  "], [None]]:
            with self.subTest(texts=texts), self.assertRaises(ValueError):
                self.model.encode(texts)

    def test_api_retry_and_invalid_vector_validation_remain_enabled(self):
        payload = {"success": True, "result": {"data": self.vectors(["text"]).tolist()}}
        with patch.object(self.model, "_get_credentials", return_value=("account", "token")), \
                patch("detector.services.cloudflare_embeddings.time.sleep"), \
                patch("detector.services.cloudflare_embeddings.requests.post") as post:
            post.side_effect = [requests.ConnectionError(), type("Response", (), {
                "status_code": 200, "ok": True, "json": lambda self: payload,
            })()]
            np.testing.assert_array_equal(self.model._request_batch(["text"]), self.vectors(["text"]))
            self.assertEqual(post.call_count, 2)
            post.side_effect = None
            post.return_value.json.return_value = {"success": True, "result": {"data": [[0.0]]}}
            with self.assertRaisesRegex(RuntimeError, "Dimensi embedding"):
                self.model._request_batch(["text"])
