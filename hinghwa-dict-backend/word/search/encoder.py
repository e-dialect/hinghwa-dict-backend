from __future__ import annotations

from typing import Iterable

import numpy as np
from django.conf import settings


class BGEEncoder:
    """Lazy, CPU-oriented encoder for dictionary entries and search queries."""

    dimension = 512

    def __init__(self):
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                settings.SEMANTIC_SEARCH_MODEL_NAME,
                revision=settings.SEMANTIC_SEARCH_MODEL_REVISION,
                cache_folder=settings.SEMANTIC_SEARCH_MODEL_CACHE,
                trust_remote_code=False,
            )
        return self._model

    def _encode_texts(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        non_empty_positions = [index for index, text in enumerate(texts) if text]
        result = np.zeros((len(texts), self.dimension), dtype=np.float32)
        if not non_empty_positions:
            return result

        vectors = self._get_model().encode(
            [texts[index] for index in non_empty_positions],
            batch_size=32,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        result[non_empty_positions] = np.asarray(vectors, dtype=np.float32)
        return result

    def encode_entries(self, entries: Iterable[dict]) -> np.ndarray:
        rows = list(entries)
        semantic_texts = []
        words = []
        pinyin = []
        ipa = []
        for row in rows:
            semantic_texts.append(
                "\n".join(
                    part
                    for part in [
                        " ".join(row.get("mandarin", [])),
                        row.get("definition", ""),
                        row.get("annotation", ""),
                    ]
                    if part
                )
            )
            words.append(row.get("word", ""))
            pinyin.append(row.get("standard_pinyin", ""))
            ipa.append(row.get("standard_ipa", ""))

        vectors = (
            self._encode_texts(semantic_texts) * 0.60
            + self._encode_texts(words) * 0.30
            + self._encode_texts(pinyin) * 0.05
            + self._encode_texts(ipa) * 0.05
        )
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        np.divide(vectors, norms, out=vectors, where=norms > 1e-6)
        return vectors.astype(np.float32, copy=False)

    def encode_query(self, query: str) -> np.ndarray:
        return self._encode_texts([query.strip()])[0]
