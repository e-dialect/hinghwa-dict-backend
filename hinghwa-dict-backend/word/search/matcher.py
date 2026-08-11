from __future__ import annotations

import re
import unicodedata
from collections import defaultdict

import numpy as np

from .artifacts import ArtifactBundle
from .encoder import BGEEncoder
from .llm import DeepSeekQueryParser

_PHONETIC_SEPARATOR = re.compile(r"[\s'’`\-_.]+")
_PINYIN_TONE_CHARACTERS = set("āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ")


def _has_chinese(text: str) -> bool:
    return any(
        "\u3400" <= char <= "\u9fff" or 0x20000 <= ord(char) <= 0x2FA1F for char in text
    )


def _normalize_phonetic(text: str) -> str:
    normalized = text.casefold().replace("u:", "ü").replace("v", "ü")
    decomposed = unicodedata.normalize("NFD", normalized)
    without_tones = "".join(
        char for char in decomposed if unicodedata.category(char) != "Mn"
    )
    return _PHONETIC_SEPARATOR.sub("", without_tones)


def _has_ipa(text: str) -> bool:
    return any(
        "\u0250" <= char <= "\u02ff" or "\u1d00" <= char <= "\u1d7f" for char in text
    )


def _mixed_phonetic_query(text: str) -> str:
    return "".join(
        char
        for char in text
        if (char.isascii() and (char.isalpha() or char.isdigit()))
        or char in _PINYIN_TONE_CHARACTERS
    )


class IntentClassifier:
    def classify(self, query: str) -> str:
        has_chinese = _has_chinese(query)
        has_ipa = _has_ipa(query)
        has_ascii = bool(re.search(r"[a-zA-ZüÜvV]", query))
        has_pinyin_tone = any(char in _PINYIN_TONE_CHARACTERS for char in query)
        if has_chinese and (has_ascii or has_ipa):
            return "mixed"
        if has_ipa:
            return "ipa"
        if (has_ascii or has_pinyin_tone) and not has_chinese:
            return "pinyin"
        return "text"


class SearchMatcher:
    def __init__(
        self,
        bundle: ArtifactBundle,
        *,
        encoder: BGEEncoder,
        llm_parser: DeepSeekQueryParser,
    ):
        self.bundle = bundle
        self.encoder = encoder
        self.llm_parser = llm_parser
        self.classifier = IntentClassifier()
        self._exact_words = defaultdict(list)
        for entry in bundle.entries:
            self._exact_words[entry.get("word", "").casefold()].append(entry["id"])

    def search(
        self,
        query: str,
        *,
        allowed_ids: set[int] | None = None,
        limit: int = 200,
    ) -> list[int]:
        normalized_query = query.strip()
        if not normalized_query or limit <= 0:
            return []
        limit = min(limit, 200)
        if allowed_ids is not None and not allowed_ids:
            return []

        exact_ids = self._filter_ids(
            self._exact_words.get(normalized_query.casefold(), []), allowed_ids
        )
        if exact_ids:
            return exact_ids[:limit]

        intent = self.classifier.classify(normalized_query)
        ranked_ids: list[int] = []
        if intent == "pinyin":
            ranked_ids.extend(
                self._phonetic_search(
                    normalized_query, "standard_pinyin", allowed_ids, limit
                )
            )
        elif intent == "ipa":
            ranked_ids.extend(
                self._phonetic_search(
                    normalized_query, "standard_ipa", allowed_ids, limit
                )
            )
        elif intent == "mixed":
            phonetic_query = _mixed_phonetic_query(normalized_query)
            if phonetic_query:
                ranked_ids.extend(
                    self._phonetic_search(
                        phonetic_query, "standard_pinyin", allowed_ids, limit
                    )
                )
            rewritten = self.llm_parser.rewrite(normalized_query)
            ranked_ids.extend(
                self._semantic_search(rewritten or normalized_query, allowed_ids, limit)
            )
        else:
            substring_ids = [
                entry["id"]
                for entry in self.bundle.entries
                if normalized_query.casefold() in entry.get("word", "").casefold()
            ]
            ranked_ids.extend(self._filter_ids(substring_ids, allowed_ids))
            rewritten = self.llm_parser.rewrite(normalized_query)
            ranked_ids.extend(
                self._semantic_search(rewritten or normalized_query, allowed_ids, limit)
            )

        return self._deduplicate(ranked_ids, limit)

    @staticmethod
    def _filter_ids(ids: list[int], allowed_ids: set[int] | None) -> list[int]:
        if allowed_ids is None:
            return list(ids)
        return [word_id for word_id in ids if word_id in allowed_ids]

    @staticmethod
    def _deduplicate(ids: list[int], limit: int) -> list[int]:
        seen = set()
        result = []
        for word_id in ids:
            if word_id in seen:
                continue
            seen.add(word_id)
            result.append(word_id)
            if len(result) >= limit:
                break
        return result

    def _phonetic_search(
        self,
        query: str,
        field_name: str,
        allowed_ids: set[int] | None,
        limit: int,
    ) -> list[int]:
        import Levenshtein

        normalized_query = _normalize_phonetic(query)
        if not normalized_query:
            return []
        scored = []
        for position, entry in enumerate(self.bundle.entries):
            word_id = entry["id"]
            if allowed_ids is not None and word_id not in allowed_ids:
                continue
            candidate = _normalize_phonetic(entry.get(field_name, ""))
            if not candidate:
                continue
            distance = Levenshtein.distance(normalized_query, candidate)
            similarity = 1 - distance / max(len(normalized_query), len(candidate))
            if similarity >= 0.45:
                scored.append((similarity, -position, word_id))
        scored.sort(reverse=True)
        return [word_id for _, _, word_id in scored[:limit]]

    def _semantic_search(
        self,
        query: str,
        allowed_ids: set[int] | None,
        limit: int,
    ) -> list[int]:
        if not self.bundle.entries:
            return []
        query_vector = np.ascontiguousarray(
            self.encoder.encode_query(query).reshape(1, -1), dtype=np.float32
        )
        candidate_count = (
            len(self.bundle.entries)
            if allowed_ids is not None
            else min(limit, len(self.bundle.entries))
        )
        _, positions = self.bundle.index.search(query_vector, candidate_count)
        ranked = []
        for position in positions[0]:
            if position < 0:
                continue
            word_id = self.bundle.entries[int(position)]["id"]
            if allowed_ids is None or word_id in allowed_ids:
                ranked.append(word_id)
                if len(ranked) >= limit:
                    break
        return ranked
