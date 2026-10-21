from concurrent.futures import ThreadPoolExecutor
import sys
from threading import Barrier, Event, Lock
from types import ModuleType
from unittest import mock

import numpy as np
from django.test import SimpleTestCase

from word.search.encoder import BGEEncoder


class BGEEncoderTests(SimpleTestCase):
    def test_concurrent_cold_queries_construct_model_once(self):
        encoder = BGEEncoder()
        start = Barrier(3)
        entered = Event()
        both_queries_entered_model_lookup = Event()
        release = Event()
        calls = []
        call_lock = Lock()
        lookup_count = 0
        original_lookup = encoder._get_model

        def observed_lookup():
            nonlocal lookup_count
            with call_lock:
                lookup_count += 1
                if lookup_count == 2:
                    both_queries_entered_model_lookup.set()
            return original_lookup()

        encoder._get_model = observed_lookup

        class Model:
            def encode(self, texts, **_kwargs):
                return np.zeros((len(texts), BGEEncoder.dimension))

        model = Model()

        def construct(*_args, **_kwargs):
            with call_lock:
                calls.append(1)
            entered.set()
            if not release.wait(timeout=5):
                raise TimeoutError("test model constructor was not released")
            return model

        module = ModuleType("sentence_transformers")
        module.SentenceTransformer = construct

        def query():
            start.wait(timeout=5)
            return encoder.encode_query("冷启动并发")

        with mock.patch.dict(sys.modules, {"sentence_transformers": module}):
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(query)
                second = pool.submit(query)
                try:
                    start.wait(timeout=5)
                    self.assertTrue(entered.wait(timeout=5))
                    self.assertTrue(both_queries_entered_model_lookup.wait(timeout=5))
                    self.assertEqual(len(calls), 1)
                finally:
                    release.set()
                self.assertEqual(first.result(timeout=5).shape, (encoder.dimension,))
                self.assertEqual(second.result(timeout=5).shape, (encoder.dimension,))
        self.assertEqual(len(calls), 1)
        self.assertIs(encoder._model, model)

    def test_failed_model_construction_can_retry(self):
        encoder = BGEEncoder()

        class Model:
            def encode(self, texts, **_kwargs):
                return np.zeros((len(texts), BGEEncoder.dimension))

        model = Model()
        constructor = mock.Mock(side_effect=[RuntimeError("cold load failed"), model])
        module = ModuleType("sentence_transformers")
        module.SentenceTransformer = constructor
        with mock.patch.dict(sys.modules, {"sentence_transformers": module}):
            with self.assertRaisesRegex(RuntimeError, "cold load failed"):
                encoder.encode_query("first attempt")
            self.assertIsNone(encoder._model)
            self.assertEqual(
                encoder.encode_query("second attempt").shape,
                (encoder.dimension,),
            )
        self.assertEqual(constructor.call_count, 2)
        self.assertIs(encoder._model, model)

    def test_configured_batch_size_is_passed_to_model(self):
        for batch_size in (32, 8):
            with self.subTest(batch_size=batch_size):
                model = mock.Mock()
                model.encode.return_value = np.zeros((1, BGEEncoder.dimension))
                with self.settings(SEMANTIC_SEARCH_ENCODING_BATCH_SIZE=batch_size):
                    # Construct under the override so initialization validates
                    # and captures the deployment's selected batch size.
                    encoder = BGEEncoder()
                    with mock.patch.object(encoder, "_get_model", return_value=model):
                        result = encoder._encode_texts(["test"])

                self.assertEqual(result.shape, (1, encoder.dimension))
                self.assertEqual(
                    model.encode.call_args.kwargs["batch_size"], batch_size
                )

    def test_invalid_batch_size_is_rejected(self):
        for batch_size in (0, -1, 33, True, 8.0, "8"):
            with self.subTest(batch_size=batch_size):
                with self.settings(SEMANTIC_SEARCH_ENCODING_BATCH_SIZE=batch_size):
                    with self.assertRaisesRegex(ValueError, "integer between 1 and 32"):
                        BGEEncoder()
