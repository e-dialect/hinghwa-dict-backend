"""Worker recovery tests use synthetic rows, real SQLite and CPU FAISS only."""

import hashlib
from concurrent.futures import ThreadPoolExecutor
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest import mock

from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command, CommandError
from django.db import DatabaseError, connection
from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone

from HinghwaDict.database import sqlite_database_path
from word.models import SemanticIndexState, Word
from word.search.artifacts import (
    build_semantic_artifacts,
    source_digest,
    artifact_file_digest,
)
from word.search.signals import request_index_rebuild
from word.search.worker import SemanticIndexWorker
from word.search.exceptions import SourceScanLimit
from word.test_semantic_search import FakeEncoder


class CanonicalSQLiteTests(SimpleTestCase):
    def test_source_deadline_covers_empty_input_and_iteration_termination(self):
        for entries, ticks in [((), [0, 10]), (({"id": 1},), [0, 1, 10])]:
            with self.subTest(entries=entries), self.settings(
                SEMANTIC_SEARCH_SOURCE_SCAN_SECONDS=2
            ), mock.patch(
                "word.search.artifacts.iter_visible_entries", return_value=iter(entries)
            ), mock.patch(
                "word.search.artifacts.time.monotonic", side_effect=ticks
            ):
                with self.assertRaises(SourceScanLimit):
                    source_digest()

    def test_file_deadline_covers_empty_file_and_eof_termination(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "synthetic"
            for content, ticks in [(b"", [0, 10]), (b"synthetic", [0, 1, 10])]:
                target.write_bytes(content)
                with self.subTest(content=content), self.settings(
                    SEMANTIC_SEARCH_SOURCE_SCAN_SECONDS=2
                ), mock.patch(
                    "word.search.artifacts.time.monotonic", side_effect=ticks
                ):
                    with self.assertRaises(SourceScanLimit):
                        artifact_file_digest(target)

    def test_default_is_unchanged_and_custom_paths_are_absolute_canonical(self):
        self.assertEqual(sqlite_database_path("", "/legacy"), "/legacy/db.sqlite3")
        with self.assertRaises(ImproperlyConfigured):
            sqlite_database_path("relative.sqlite3", "/legacy")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "actual").mkdir()
            (root / "alias").symlink_to(root / "actual", target_is_directory=True)
            self.assertEqual(
                sqlite_database_path(str(root / "alias/db.sqlite3"), "/legacy"),
                str((root / "actual/db.sqlite3").resolve()),
            )

    def test_killed_wal_writer_requires_its_complete_directory_for_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = root / "sqlite"
            live.mkdir()
            database = live / "db.sqlite3"
            with sqlite3.connect(database) as db:
                db.execute("CREATE TABLE synthetic(value INTEGER)")
            code = """
import os, signal, sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA wal_autocheckpoint=0')
conn.execute('INSERT INTO synthetic VALUES (42)')
conn.commit()
os.kill(os.getpid(), signal.SIGKILL)
"""
            result = subprocess.run([sys.executable, "-c", code, str(database)])
            self.assertEqual(result.returncode, -signal.SIGKILL)
            self.assertTrue(Path(str(database) + "-wal").is_file())
            main_only = root / "main-only.sqlite3"
            shutil.copyfile(database, main_only)
            restored = root / "restored"
            shutil.copytree(live, restored)
            with sqlite3.connect(main_only) as db:
                self.assertEqual(
                    db.execute("SELECT count(*) FROM synthetic").fetchone(), (0,)
                )
            with sqlite3.connect(restored / "db.sqlite3") as db:
                self.assertEqual(
                    db.execute("SELECT value FROM synthetic").fetchall(), [(42,)]
                )
                self.assertEqual(
                    db.execute("PRAGMA integrity_check").fetchone(), ("ok",)
                )


class WorkerReconciliationTests(TransactionTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.override = self.settings(
            SEMANTIC_SEARCH_DATA_DIR=self.directory.name,
            SEMANTIC_SEARCH_RECONCILE_SECONDS=0,
        )
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.encoder = mock.patch(
            "word.search.artifacts.BGEEncoder", return_value=FakeEncoder()
        )
        self.encoder.start()
        self.addCleanup(self.encoder.stop)
        self.user = User.objects.create_user("worker-readiness-synthetic")
        self.word = Word.objects.create(
            contributor=self.user,
            word="synthetic",
            definition="before",
            visibility=True,
        )
        self.worker = SemanticIndexWorker("reconciler")

    def manifest(self):
        return json.loads((Path(self.directory.name) / "manifest.json").read_text())

    def assert_ready_for_source(self):
        state = SemanticIndexState.objects.get(pk=1)
        self.assertEqual(state.status, SemanticIndexState.Status.READY)
        self.assertEqual(state.built_revision, state.requested_revision)
        self.assertEqual(self.manifest()["entries_sha256"], source_digest())
        self.assertEqual(state.lease_owner, "")

    def test_bulk_and_legacy_sql_changes_are_reconciled_without_signals(self):
        self.assertTrue(self.worker.run_once())
        first = self.manifest()
        Word.objects.filter(pk=self.word.pk).update(definition="bulk edit")
        self.assertTrue(self.worker.run_once())
        self.assert_ready_for_source()
        self.assertNotEqual(first["generation"], self.manifest()["generation"])
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE word_word SET word=%s WHERE id=%s",
                ["legacy edit", self.word.pk],
            )
        self.assertTrue(self.worker.run_once())
        self.assert_ready_for_source()
        Word.objects.filter(pk=self.word.pk).update(visibility=False)
        self.assertTrue(self.worker.run_once())
        self.assertEqual(self.manifest()["entry_count"], 0)
        self.assert_ready_for_source()
        Word.objects.bulk_create(
            [
                Word(contributor=self.user, word="bulk-created-one", visibility=True),
                Word(contributor=self.user, word="bulk-created-two", visibility=True),
            ]
        )
        self.assertTrue(self.worker.run_once())
        self.assertEqual(self.manifest()["entry_count"], 2)
        self.assert_ready_for_source()

    def test_signal_database_error_does_not_lose_a_committed_word_edit(self):
        self.assertTrue(self.worker.run_once())
        with mock.patch(
            "word.search.signals.SemanticIndexState.objects.select_for_update",
            side_effect=DatabaseError("synthetic lock"),
        ):
            self.word.definition = "committed despite missed signal"
            self.word.save()
        self.assertEqual(
            Word.objects.get(pk=self.word.pk).definition, self.word.definition
        )
        self.assertTrue(self.worker.run_once())
        self.assert_ready_for_source()

    def test_explicit_force_db_error_and_noop_are_not_success(self):
        with mock.patch(
            "word.search.signals.SemanticIndexState.objects.select_for_update",
            side_effect=DatabaseError("synthetic lock"),
        ):
            with self.assertRaises(DatabaseError):
                self.worker.run_once(force=True)
        busy_worker = SemanticIndexWorker("other-active-worker")
        self.assertIsNotNone(busy_worker._claim(False))
        with self.assertRaisesRegex(CommandError, "did not complete"):
            call_command("semantic_index_worker", once=True, force=True)

    def test_bulk_change_during_build_never_publishes_the_old_snapshot(self):
        self.assertTrue(self.worker.run_once())
        first = self.manifest()
        request_index_rebuild(strict=True)
        real_build = build_semantic_artifacts
        database_name = connection.settings_dict["NAME"]

        def concurrent_legacy_write(revision, **kwargs):
            manifest = real_build(revision, **kwargs)

            def legacy_writer():
                with sqlite3.connect(database_name, uri=True) as db:
                    db.execute(
                        "UPDATE word_word SET definition=? WHERE id=?",
                        ("changed during encoding", self.word.pk),
                    )

            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(legacy_writer).result(timeout=5)
            return manifest

        with mock.patch(
            "word.search.worker.build_semantic_artifacts",
            side_effect=concurrent_legacy_write,
        ):
            self.assertFalse(self.worker.run_once())
        self.assertEqual(self.manifest(), first)
        self.assertEqual(
            SemanticIndexState.objects.get(pk=1).status,
            SemanticIndexState.Status.PENDING,
        )
        self.assertTrue(self.worker.run_once())
        self.assert_ready_for_source()

    def test_finish_holds_sqlite_writer_reservation_until_publication(self):
        self.assertTrue(self.worker.run_once())
        request_index_rebuild(strict=True)
        original_digest = source_digest
        blocked = []

        def attempt_legacy_write():
            legacy = sqlite3.connect(
                connection.settings_dict["NAME"], uri=True, timeout=0
            )
            try:
                with self.assertRaises(sqlite3.OperationalError):
                    legacy.execute(
                        "UPDATE word_word SET definition=? WHERE id=?",
                        ("racing", self.word.pk),
                    )
                blocked.append(True)
            finally:
                legacy.close()
            return original_digest()

        # The source read inside _finish occurs after an actual SQL write lock.
        with mock.patch("word.search.worker.source_digest") as digest:
            digest.side_effect = lambda: (
                attempt_legacy_write()
                if connection.in_atomic_block
                else original_digest()
            )
            self.assertTrue(self.worker.run_once())
        self.assertEqual(blocked, [True])
        self.assert_ready_for_source()

    def test_corrupt_files_and_restart_are_reconciled(self):
        self.assertTrue(self.worker.run_once())
        previous = self.manifest()
        index = Path(self.directory.name) / previous["index_file"]
        index.write_bytes(index.read_bytes() + b"synthetic corruption")
        restarted = SemanticIndexWorker("restarted")
        self.assertTrue(restarted.run_once())
        self.assertNotEqual(previous["generation"], self.manifest()["generation"])
        self.assert_ready_for_source()

    def test_source_hash_matches_actual_canonical_artifact_and_ignores_views(self):
        self.assertTrue(self.worker.run_once())
        manifest = self.manifest()
        content = (Path(self.directory.name) / manifest["entries_file"]).read_bytes()
        self.assertEqual(source_digest(), hashlib.sha256(content).hexdigest())
        Word.objects.filter(pk=self.word.pk).update(views=100)
        self.assertFalse(self.worker.run_once())
        self.assertEqual(self.manifest(), manifest)

    def test_poll_interval_avoids_full_scan_on_every_idle_poll(self):
        with self.settings(SEMANTIC_SEARCH_RECONCILE_SECONDS=30):
            worker = SemanticIndexWorker("periodic")
            with mock.patch("word.search.worker.time.monotonic", return_value=0):
                self.assertTrue(worker.run_once())
            Word.objects.filter(pk=self.word.pk).update(
                definition="unobserved until deadline"
            )
            with mock.patch(
                "word.search.worker.time.monotonic", return_value=29
            ), mock.patch("word.search.worker.source_digest") as digest:
                self.assertFalse(worker.run_once())
                digest.assert_not_called()
            with mock.patch("word.search.worker.time.monotonic", return_value=30):
                self.assertTrue(worker.run_once())
        self.assert_ready_for_source()

    def test_expired_killed_worker_lease_can_be_reclaimed(self):
        first = SemanticIndexWorker("killed")
        self.assertIsNotNone(first._claim(False))
        self.assertFalse(self.worker.run_once())
        SemanticIndexState.objects.filter(pk=1).update(
            lease_expires_at=timezone.now() - timedelta(seconds=1)
        )
        self.assertTrue(self.worker.run_once())
        self.assert_ready_for_source()

    def test_reconciliation_time_budget_failure_invalidates_instead_of_trusting_ready(
        self,
    ):
        self.assertTrue(self.worker.run_once())
        with mock.patch(
            "word.search.worker.source_digest",
            side_effect=SourceScanLimit("synthetic budget"),
        ):
            with self.assertRaises(SourceScanLimit):
                self.worker.run_once()
        self.assertEqual(
            SemanticIndexState.objects.get(pk=1).status,
            SemanticIndexState.Status.PENDING,
        )
        self.assertTrue(self.worker.run_once())
        self.assert_ready_for_source()

    def test_fingerprint_covers_every_encoded_field_and_visibility(self):
        self.assertTrue(self.worker.run_once())
        for field, value in [
            ("word", "改词"),
            ("definition", "新释义"),
            ("annotation", "附注"),
            ("mandarin", '["甲","乙"]'),
            ("standard_ipa", "ŋa"),
            ("standard_pinyin", "nga2"),
        ]:
            before = self.manifest()
            Word.objects.filter(pk=self.word.pk).update(**{field: value})
            self.assertTrue(self.worker.run_once(), field)
            self.assertNotEqual(
                before["entries_sha256"], self.manifest()["entries_sha256"], field
            )
            self.assert_ready_for_source()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM word_word WHERE id=%s", [self.word.pk])
        self.assertTrue(self.worker.run_once())
        self.assertEqual(self.manifest()["entry_count"], 0)

    def test_invalid_reconciliation_intervals_cannot_disable_detection(self):
        for value in [float("inf"), float("nan"), -1, 301]:
            with self.settings(SEMANTIC_SEARCH_RECONCILE_SECONDS=value):
                with self.assertRaises(ValueError):
                    SemanticIndexWorker("invalid")

    def test_large_file_checksums_do_not_hold_a_sqlite_transaction(self):
        self.assertTrue(self.worker.run_once())
        calls = []

        def check_outside_transaction(path):
            self.assertFalse(connection.in_atomic_block)
            calls.append(path)
            return artifact_file_digest(path)

        with mock.patch(
            "word.search.worker.artifact_file_digest",
            side_effect=check_outside_transaction,
        ):
            self.assertFalse(self.worker.run_once())
        self.assertEqual(len(calls), 2)
