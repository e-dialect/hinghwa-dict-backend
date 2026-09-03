import hashlib
import json
import tempfile
from pathlib import Path
from unittest import mock

import numpy as np
from django.contrib.auth.models import User
from django.test import RequestFactory, SimpleTestCase, TestCase, TransactionTestCase

from user.models import UserInfo
from word.models import SemanticIndexState, Word
from word.search.artifacts import (
    ArtifactBundle,
    ArtifactRepository,
    build_semantic_artifacts,
)
from word.search.exceptions import SearchUnavailable
from word.search.llm import DeepSeekQueryParser
from word.search.matcher import IntentClassifier, SearchMatcher
from word.search.signals import request_index_rebuild
from word.search.worker import SemanticIndexWorker
from word.word.views import searchWords


class FakeEncoder:
    dimension = 4

    def encode_entries(self, entries):
        rows = list(entries)
        result = np.zeros((len(rows), self.dimension), dtype=np.float32)
        for index in range(len(rows)):
            result[index, index % self.dimension] = 1
        return result

    def encode_query(self, query):
        return np.array([1, 0, 0, 0], dtype=np.float32)


class FakeIndex:
    def __init__(self, positions):
        self.positions = positions

    def search(self, query, count):
        selected = self.positions[:count]
        return (
            np.array([[1.0] * len(selected)], dtype=np.float32),
            np.array([selected], dtype=np.int64),
        )


class NullLLMParser:
    def rewrite(self, query):
        return None


class RecordingLLMParser:
    def __init__(self, rewritten):
        self.rewritten = rewritten
        self.queries = []

    def rewrite(self, query):
        self.queries.append(query)
        return self.rewritten


class FailingEncoder(FakeEncoder):
    def encode_entries(self, entries):
        raise RuntimeError("encoding failed")


class ArtifactBuildTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("semantic-artifact-user")

    def test_build_exports_only_visible_words_with_real_ids(self):
        visible = Word.objects.create(
            word="郎罢",
            definition="爸爸",
            mandarin='["爸爸"]',
            standard_pinyin="nɔŋ2 ma5",
            standard_ipa="nɔŋ ma",
            contributor=self.user,
            visibility=True,
        )
        Word.objects.create(
            word="未审核",
            definition="不可见",
            contributor=self.user,
            visibility=False,
        )

        with tempfile.TemporaryDirectory() as directory:
            manifest = build_semantic_artifacts(
                7, encoder=FakeEncoder(), data_dir=directory
            )
            entries_path = Path(directory) / manifest["entries_file"]
            entries_bytes = entries_path.read_bytes()
            entries = json.loads(entries_bytes)

            self.assertEqual(manifest["revision"], 7)
            self.assertEqual(manifest["entry_count"], 1)
            self.assertEqual(entries[0]["id"], visible.id)
            self.assertEqual(entries[0]["mandarin"], ["爸爸"])
            self.assertEqual(
                manifest["entries_sha256"], hashlib.sha256(entries_bytes).hexdigest()
            )
            index_bytes = (Path(directory) / manifest["index_file"]).read_bytes()
            self.assertEqual(
                manifest["index_sha256"], hashlib.sha256(index_bytes).hexdigest()
            )

    def test_failed_rebuild_preserves_previous_manifest(self):
        Word.objects.create(
            word="郎罢",
            definition="爸爸",
            contributor=self.user,
            visibility=True,
        )
        with tempfile.TemporaryDirectory() as directory:
            first = build_semantic_artifacts(
                1, encoder=FakeEncoder(), data_dir=directory
            )
            manifest_path = Path(directory) / "manifest.json"
            before = manifest_path.read_bytes()

            with self.assertRaisesRegex(RuntimeError, "encoding failed"):
                build_semantic_artifacts(
                    2, encoder=FailingEncoder(), data_dir=directory
                )

            self.assertEqual(manifest_path.read_bytes(), before)
            self.assertEqual(
                ArtifactRepository(directory).load().manifest["generation"],
                first["generation"],
            )

    def test_corrupt_index_is_rejected(self):
        Word.objects.create(
            word="郎罢",
            definition="爸爸",
            contributor=self.user,
            visibility=True,
        )
        with tempfile.TemporaryDirectory() as directory:
            manifest = build_semantic_artifacts(
                1, encoder=FakeEncoder(), data_dir=directory
            )
            index_path = Path(directory) / manifest["index_file"]
            index_path.write_bytes(index_path.read_bytes() + b"corrupt")
            with self.assertRaisesRegex(SearchUnavailable, "checksum"):
                ArtifactRepository(directory).load()

    def test_model_configuration_change_requires_a_rebuild(self):
        Word.objects.create(
            word="郎罢",
            definition="爸爸",
            contributor=self.user,
            visibility=True,
        )
        with tempfile.TemporaryDirectory() as directory:
            build_semantic_artifacts(1, encoder=FakeEncoder(), data_dir=directory)
            with self.settings(SEMANTIC_SEARCH_MODEL_REVISION="different-revision"):
                with self.assertRaisesRegex(SearchUnavailable, "stale"):
                    ArtifactRepository(directory).load()


class MatcherTests(SimpleTestCase):
    def make_matcher(self, entries, positions=None):
        bundle = ArtifactBundle(
            manifest={"revision": 1},
            entries=entries,
            index=FakeIndex(positions or list(range(len(entries)))),
        )
        return SearchMatcher(
            bundle,
            encoder=FakeEncoder(),
            llm_parser=NullLLMParser(),
        )

    def test_exact_match_preserves_duplicate_word_ids_and_filter(self):
        matcher = self.make_matcher(
            [
                {"id": 10, "word": "郎罢"},
                {"id": 11, "word": "郎罢"},
                {"id": 12, "word": "其他"},
            ]
        )
        self.assertEqual(matcher.search("郎罢", allowed_ids={11, 12}, limit=200), [11])

    def test_semantic_results_keep_faiss_order_and_allowed_ids(self):
        matcher = self.make_matcher(
            [
                {"id": 10, "word": "甲"},
                {"id": 11, "word": "乙"},
                {"id": 12, "word": "丙"},
            ],
            positions=[2, 0, 1],
        )
        self.assertEqual(
            matcher.search("爸爸怎么说", allowed_ids={10, 12}, limit=2), [12, 10]
        )

    def test_phonetic_routes_and_ranks_pinyin(self):
        matcher = self.make_matcher(
            [
                {"id": 1, "word": "甲", "standard_pinyin": "nɔŋ2ma5"},
                {"id": 2, "word": "乙", "standard_pinyin": "nong2ma5"},
            ]
        )
        self.assertEqual(IntentClassifier().classify("nong2ma5"), "pinyin")
        self.assertEqual(matcher.search("nong2ma5", limit=2)[0], 2)

    def test_tone_mark_pinyin_and_common_ipa_are_recognized(self):
        classifier = IntentClassifier()
        self.assertEqual(classifier.classify("pó"), "pinyin")
        self.assertEqual(classifier.classify("pəŋ"), "ipa")

    def test_mixed_query_uses_optional_rewriter_for_semantic_part(self):
        parser = RecordingLLMParser("爸爸")
        bundle = ArtifactBundle(
            manifest={"revision": 1},
            entries=[{"id": 1, "word": "甲", "standard_pinyin": "ba5"}],
            index=FakeIndex([0]),
        )
        matcher = SearchMatcher(bundle, encoder=FakeEncoder(), llm_parser=parser)
        self.assertEqual(matcher.search("爸爸 ba5"), [1])
        self.assertEqual(parser.queries, ["爸爸 ba5"])

    def test_result_limit_is_capped_at_200(self):
        entries = [{"id": index, "word": "相同"} for index in range(1, 251)]
        matcher = self.make_matcher(entries)
        self.assertEqual(len(matcher.search("相同", limit=1000)), 200)


class DeepSeekQueryParserTests(SimpleTestCase):
    @mock.patch("requests.post")
    def test_disabled_parser_never_calls_network(self, post):
        with self.settings(SEMANTIC_SEARCH_LLM_ENABLED=False):
            self.assertIsNone(DeepSeekQueryParser().rewrite("爸爸怎么说"))
        post.assert_not_called()

    @mock.patch("requests.post")
    def test_parser_accepts_only_structured_keywords(self, post):
        response = mock.Mock()
        response.json.return_value = {
            "choices": [{"message": {"content": '{"keywords":["爸爸"]}'}}]
        }
        post.return_value = response
        with self.settings(
            SEMANTIC_SEARCH_LLM_ENABLED=True,
            SEMANTIC_SEARCH_LLM_API_KEY="test-key",
            SEMANTIC_SEARCH_LLM_BASE_URL="https://example.invalid",
            SEMANTIC_SEARCH_LLM_MODEL="test-model",
            SEMANTIC_SEARCH_LLM_TIMEOUT_SECONDS=0.1,
        ):
            self.assertEqual(DeepSeekQueryParser().rewrite("爸爸怎么说"), "爸爸")

    @mock.patch("requests.post")
    def test_malformed_response_falls_back_locally(self, post):
        response = mock.Mock()
        response.json.return_value = {"choices": [{"message": {"content": "not-json"}}]}
        post.return_value = response
        with self.settings(
            SEMANTIC_SEARCH_LLM_ENABLED=True,
            SEMANTIC_SEARCH_LLM_API_KEY="test-key",
            SEMANTIC_SEARCH_LLM_BASE_URL="https://example.invalid",
            SEMANTIC_SEARCH_LLM_MODEL="test-model",
            SEMANTIC_SEARCH_LLM_TIMEOUT_SECONDS=0.1,
        ):
            self.assertIsNone(DeepSeekQueryParser().rewrite("爸爸怎么说"))

    @mock.patch("requests.post")
    def test_enabled_parser_without_key_never_calls_network(self, post):
        with self.settings(
            SEMANTIC_SEARCH_LLM_ENABLED=True,
            SEMANTIC_SEARCH_LLM_API_KEY="",
        ):
            self.assertIsNone(DeepSeekQueryParser().rewrite("爸爸怎么说"))
        post.assert_not_called()


class SignalTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user("semantic-signal-user")

    def test_only_search_source_changes_request_a_revision(self):
        word = Word.objects.create(
            word="郎罢",
            definition="爸爸",
            contributor=self.user,
            visibility=True,
        )
        state = SemanticIndexState.objects.get(singleton_key=1)
        created_revision = state.requested_revision

        word.views += 1
        word.save()
        state.refresh_from_db()
        self.assertEqual(state.requested_revision, created_revision)

        word.definition = "父亲"
        word.save()
        state.refresh_from_db()
        self.assertEqual(state.requested_revision, created_revision + 1)

        word.visibility = False
        word.save(update_fields=["visibility"])
        state.refresh_from_db()
        self.assertEqual(state.requested_revision, created_revision + 2)

        word.delete()
        state.refresh_from_db()
        self.assertEqual(state.requested_revision, created_revision + 3)


class WorkerTests(TransactionTestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.settings_override = self.settings(
            SEMANTIC_SEARCH_DATA_DIR=self.temporary_directory.name,
            SEMANTIC_SEARCH_WORKER_LEASE_SECONDS=60,
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        SemanticIndexState.objects.create(singleton_key=1)

    @mock.patch("word.search.worker.build_semantic_artifacts")
    @mock.patch("word.search.worker.publish_semantic_manifest")
    def test_initial_build_marks_index_ready(self, publish, build):
        build.return_value = {"entry_count": 0}
        self.assertTrue(SemanticIndexWorker(worker_id="first").run_once())
        publish.assert_called_once_with(build.return_value)
        state = SemanticIndexState.objects.get(singleton_key=1)
        self.assertEqual(state.status, SemanticIndexState.Status.READY)
        self.assertEqual(state.built_revision, state.requested_revision)
        self.assertEqual(state.lease_owner, "")

    @mock.patch("word.search.worker.build_semantic_artifacts")
    def test_active_lease_prevents_a_second_worker(self, build):
        first = SemanticIndexWorker(worker_id="first")
        self.assertEqual(first._claim(False), 1)
        self.assertFalse(SemanticIndexWorker(worker_id="second").run_once())
        build.assert_not_called()

    @mock.patch("word.search.worker.build_semantic_artifacts")
    @mock.patch("word.search.worker.publish_semantic_manifest")
    def test_worker_coalesces_a_change_during_build(self, publish, build):
        first_build = True

        def build_once(revision, **kwargs):
            nonlocal first_build
            if first_build:
                first_build = False
                request_index_rebuild()
            return {"entry_count": 1}

        build.side_effect = build_once
        worker = SemanticIndexWorker(worker_id="test-worker")
        self.assertTrue(worker.run_once())
        state = SemanticIndexState.objects.get(singleton_key=1)
        self.assertEqual(state.status, SemanticIndexState.Status.PENDING)
        self.assertEqual(state.built_revision, 1)
        self.assertEqual(state.requested_revision, 2)

        self.assertTrue(worker.run_once())
        state.refresh_from_db()
        self.assertEqual(state.status, SemanticIndexState.Status.READY)
        self.assertEqual(state.built_revision, 2)
        self.assertEqual(publish.call_count, 2)

    @mock.patch("word.search.worker.build_semantic_artifacts")
    @mock.patch("word.search.worker.publish_semantic_manifest")
    def test_worker_that_lost_its_lease_cannot_publish(self, publish, build):
        def steal_lease(revision, **kwargs):
            state = SemanticIndexState.objects.get(singleton_key=1)
            state.lease_owner = "second"
            state.save(update_fields=["lease_owner"])
            return {"entry_count": 0}

        build.side_effect = steal_lease
        with self.assertRaisesRegex(RuntimeError, "lost its lease"):
            SemanticIndexWorker(worker_id="first").run_once()
        publish.assert_not_called()
        state = SemanticIndexState.objects.get(singleton_key=1)
        self.assertEqual(state.built_revision, 0)
        self.assertEqual(state.lease_owner, "second")

    @mock.patch("word.search.worker.build_semantic_artifacts")
    def test_worker_records_failure_without_advancing_revision(self, build):
        build.side_effect = RuntimeError("model unavailable")
        worker = SemanticIndexWorker(worker_id="test-worker")
        with self.assertRaises(RuntimeError):
            worker.run_once()
        state = SemanticIndexState.objects.get(singleton_key=1)
        self.assertEqual(state.status, SemanticIndexState.Status.FAILED)
        self.assertEqual(state.built_revision, 0)
        self.assertIn("model unavailable", state.last_error)

    @mock.patch("word.search.worker.build_semantic_artifacts")
    @mock.patch("word.search.worker.publish_semantic_manifest")
    def test_worker_retries_a_failed_revision(self, publish, build):
        build.side_effect = [RuntimeError("temporary"), {"entry_count": 0}]
        worker = SemanticIndexWorker(worker_id="test-worker")
        with self.assertRaisesRegex(RuntimeError, "temporary"):
            worker.run_once()
        self.assertTrue(worker.run_once())
        state = SemanticIndexState.objects.get(singleton_key=1)
        self.assertEqual(state.status, SemanticIndexState.Status.READY)
        self.assertEqual(state.built_revision, 1)
        publish.assert_called_once_with({"entry_count": 0})


class SearchWordsIntegrationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user("semantic-view-user")
        UserInfo.objects.create(user=self.user, nickname="tester")
        self.first = Word.objects.create(
            word="甲",
            definition="第一",
            contributor=self.user,
            visibility=True,
            tags='["家庭"]',
        )
        self.second = Word.objects.create(
            word="乙",
            definition="第二",
            contributor=self.user,
            visibility=True,
            tags='["其他"]',
        )

    @mock.patch("word.word.views.semantic_search_word_ids")
    def test_endpoint_keeps_ranked_ids_and_response_shape(self, search):
        search.return_value = [self.second.id, self.first.id]
        response = searchWords(self.factory.get("/words", {"search": "查询"}))
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["words"], [self.second.id, self.first.id])
        self.assertEqual(
            [item["id"] for item in payload["result"]],
            [self.second.id, self.first.id],
        )

    @mock.patch("word.word.views.semantic_search_word_ids")
    def test_unavailable_index_uses_legacy_search(self, search):
        search.side_effect = SearchUnavailable("pending")
        response = searchWords(self.factory.get("/words", {"search": "第一"}))
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["words"][0], self.first.id)

    @mock.patch("word.word.views.semantic_search_word_ids")
    def test_blank_search_behaves_like_unfiltered_list(self, search):
        response = searchWords(self.factory.get("/words", {"search": "   "}))
        payload = json.loads(response.content)
        search.assert_not_called()
        self.assertEqual(set(payload["words"]), {self.first.id, self.second.id})

    @mock.patch("word.word.views.semantic_search_word_ids")
    def test_filters_are_applied_before_semantic_ranking(self, search):
        search.side_effect = lambda query, allowed_ids, limit: list(allowed_ids)
        response = searchWords(
            self.factory.get(
                "/words",
                {
                    "search": "查询",
                    "contributor": str(self.user.id),
                    "tags": "家庭",
                },
            )
        )
        payload = json.loads(response.content)
        self.assertEqual(payload["words"], [self.first.id])
        self.assertEqual(search.call_args.kwargs["allowed_ids"], {self.first.id})
        self.assertEqual(search.call_args.kwargs["limit"], 200)

    @mock.patch("word.word.views.semantic_search_word_ids")
    def test_empty_semantic_result_does_not_fall_back(self, search):
        search.return_value = []
        response = searchWords(self.factory.get("/words", {"search": "不存在"}))
        payload = json.loads(response.content)
        self.assertEqual(payload, {"result": [], "words": []})
