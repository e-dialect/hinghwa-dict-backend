import json
import os
import tempfile
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError
from django.test import TestCase

from word.models import Word


class RelativeGraphImportCommandTests(TestCase):
    def catalog_path(self, entries):
        catalog = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        )
        json.dump({"entries": entries}, catalog, ensure_ascii=False)
        catalog.close()
        self.addCleanup(lambda: os.unlink(catalog.name))
        return catalog.name

    @staticmethod
    def confirmed(word="测试亲属", **overrides):
        entry = {
            "word": word,
            "status": "confirmed",
            "definition": "测试释义。",
            "standard_ipa": "a533",
            "standard_pinyin": "a1",
            "evidence": "人工核对的词典第 1 页",
        }
        entry.update(overrides)
        return entry

    def run_command(self, *args):
        output = StringIO()
        call_command("import_relative_graph_entries", *args, "--json", stdout=output)
        return json.loads(output.getvalue())

    def run_conflicting_apply(self, *args):
        output = StringIO()
        with self.assertRaises(CommandError) as raised:
            call_command(
                "import_relative_graph_entries", *args, "--json", stdout=output
            )
        self.assertIn("no entries were written", str(raised.exception))
        return json.loads(output.getvalue())

    def apply_args(self, entries, contributor):
        return (
            "--catalog",
            self.catalog_path(entries),
            "--apply",
            "--contributor-id",
            str(contributor.pk),
        )

    def test_default_dry_run_does_not_create(self):
        report = self.run_command("--catalog", self.catalog_path([self.confirmed()]))

        self.assertEqual(report["mode"], "dry-run")
        self.assertEqual([item["word"] for item in report["created"]], ["测试亲属"])
        self.assertFalse(Word.objects.filter(word="测试亲属").exists())

    def test_apply_creates_hidden_word_with_existing_contributor(self):
        contributor = User.objects.create_user("relative-importer")

        report = self.run_command(*self.apply_args([self.confirmed()], contributor))

        word = Word.objects.get(word="测试亲属")
        self.assertEqual(report["created"][0]["id"], word.id)
        self.assertFalse(word.visibility)
        self.assertEqual(word.contributor, contributor)

    def test_repeating_apply_is_idempotent_after_model_normalization(self):
        contributor = User.objects.create_user("repeat-importer")
        args = self.apply_args([self.confirmed()], contributor)

        first = self.run_command(*args)
        second = self.run_command(*args)

        self.assertEqual(len(first["created"]), 1)
        self.assertEqual(len(second["existing"]), 1)
        self.assertEqual(
            second["existing"][0]["reason"], "matching word already exists"
        )
        self.assertEqual(Word.objects.filter(word="测试亲属").count(), 1)

    def test_catalog_conflict_blocks_all_candidate_writes(self):
        contributor = User.objects.create_user("atomic-importer")
        Word.objects.create(
            word="冲突词",
            definition="原释义。",
            contributor=contributor,
            standard_ipa="other",
            standard_pinyin="other",
        )

        report = self.run_conflicting_apply(
            *self.apply_args(
                [
                    self.confirmed("候选新词"),
                    self.confirmed("冲突词"),
                ],
                contributor,
            )
        )

        self.assertEqual(len(report["conflict"]), 1)
        self.assertEqual(report["created"], [])
        self.assertEqual([item["word"] for item in report["blocked"]], ["候选新词"])
        self.assertFalse(Word.objects.filter(word="候选新词").exists())

    def test_database_error_during_apply_rolls_back_prior_creates(self):
        contributor = User.objects.create_user("rollback-importer")
        entries = [self.confirmed("首个候选"), self.confirmed("第二个候选")]
        original_create = Word.objects.create
        calls = 0

        def fail_on_second_create(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise IntegrityError("simulated write failure")
            return original_create(**kwargs)

        with patch.object(Word.objects, "create", side_effect=fail_on_second_create):
            with self.assertRaises(IntegrityError):
                self.run_command(*self.apply_args(entries, contributor))

        self.assertFalse(
            Word.objects.filter(word__in=["首个候选", "第二个候选"]).exists()
        )

    def test_duplicate_catalog_words_are_conflicts_and_write_nothing(self):
        contributor = User.objects.create_user("duplicate-importer")
        entry = self.confirmed("重复词")

        report = self.run_conflicting_apply(
            *self.apply_args([entry, dict(entry)], contributor)
        )

        self.assertEqual(len(report["conflict"]), 2)
        self.assertFalse(Word.objects.filter(word="重复词").exists())

    def test_malformed_confirmed_entry_is_reported_without_writes(self):
        contributor = User.objects.create_user("invalid-importer")
        report = self.run_conflicting_apply(
            *self.apply_args(
                [
                    self.confirmed("有效候选"),
                    self.confirmed("无效词", tags=[]),
                ],
                contributor,
            )
        )

        self.assertIn("tags", report["conflict"][0]["reason"])
        self.assertEqual(report["created"], [])
        self.assertFalse(Word.objects.filter(word="有效候选").exists())

    def test_json_fields_and_model_max_lengths_are_validated(self):
        contributor = User.objects.create_user("schema-importer")
        report = self.run_conflicting_apply(
            *self.apply_args(
                [
                    self.confirmed("有效候选"),
                    self.confirmed("坏普通话", mandarin="not-json"),
                    self.confirmed("非字符串列表", mandarin="[1]"),
                    self.confirmed("坏标签", tags='{"tag": "value"}'),
                    self.confirmed("空状态", status=""),
                    self.confirmed("w" * 61),
                    self.confirmed("坏IPA", standard_ipa="a" * 101),
                    self.confirmed("坏拼音", standard_pinyin="a" * 101),
                ],
                contributor,
            )
        )

        self.assertEqual(len(report["conflict"]), 7)
        self.assertTrue(any("mandarin" in row["reason"] for row in report["conflict"]))
        self.assertTrue(any("tags" in row["reason"] for row in report["conflict"]))
        self.assertTrue(any("status" in row["reason"] for row in report["conflict"]))
        self.assertTrue(
            any("standard_ipa" in row["reason"] for row in report["conflict"])
        )
        self.assertTrue(
            any("standard_pinyin" in row["reason"] for row in report["conflict"])
        )
        self.assertFalse(
            Word.objects.filter(word__in=["有效候选", "坏普通话"]).exists()
        )

    def test_pending_and_existing_markers_never_create_words(self):
        contributor = User.objects.create_user("pending-importer")
        existing_word = Word.objects.create(
            word="阿丈", definition="待人工核对。", contributor=contributor
        )
        report = self.run_command(
            *self.apply_args(
                [
                    {"word": "待核词", "status": "pending", "reason": "缺少读音来源"},
                    {
                        "word": "阿丈",
                        "status": "existing",
                        "database_id": existing_word.pk,
                        "reason": "需人工校对",
                    },
                ],
                contributor,
            )
        )

        self.assertEqual(report["pending"][0]["word"], "待核词")
        self.assertEqual(report["existing"][0]["word"], "阿丈")
        self.assertEqual(Word.objects.filter(word="阿丈").count(), 1)
        self.assertFalse(Word.objects.filter(word="待核词").exists())

    def test_existing_marker_with_stale_snapshot_id_is_a_conflict(self):
        contributor = User.objects.create_user("stale-importer")
        existing_word = Word.objects.create(
            word="阿丈", definition="待人工核对。", contributor=contributor
        )

        report = self.run_conflicting_apply(
            *self.apply_args(
                [
                    self.confirmed("不得部分写入"),
                    {
                        "word": "阿丈",
                        "status": "existing",
                        "database_id": existing_word.pk + 10,
                        "reason": "快照已有",
                    },
                ],
                contributor,
            )
        )

        self.assertEqual(report["existing"], [])
        self.assertEqual(report["conflict"][0]["word"], "阿丈")
        self.assertIn("no longer exists", report["conflict"][0]["reason"])
        self.assertEqual([row["word"] for row in report["blocked"]], ["不得部分写入"])
        self.assertFalse(Word.objects.filter(word="不得部分写入").exists())

    def test_existing_marker_id_for_different_word_is_a_conflict(self):
        contributor = User.objects.create_user("mismatch-importer")
        other_word = Word.objects.create(
            word="别的词", definition="释义。", contributor=contributor
        )

        report = self.run_command(
            "--catalog",
            self.catalog_path(
                [
                    {
                        "word": "阿丈",
                        "status": "existing",
                        "database_id": other_word.pk,
                        "reason": "快照已有",
                    }
                ]
            ),
        )

        self.assertEqual(report["existing"], [])
        self.assertIn("belongs to", report["conflict"][0]["reason"])

    def test_apply_requires_a_real_existing_contributor(self):
        with self.assertRaises(CommandError):
            self.run_command(
                "--catalog",
                self.catalog_path([self.confirmed()]),
                "--apply",
                "--contributor-id",
                "999999",
            )

    def test_apply_requires_contributor_id(self):
        with self.assertRaises(CommandError):
            self.run_command(
                "--catalog", self.catalog_path([self.confirmed()]), "--apply"
            )
