from __future__ import annotations

import logging
import json
import socket
import uuid
import math
import time
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import transaction, DatabaseError
from django.utils import timezone

from word.models import SemanticIndexState

from .artifacts import (
    build_semantic_artifacts,
    source_digest,
    artifact_file_digest,
    discard_unpublished_artifacts,
    _safe_artifact_path,
    manifest_matches_configuration,
    publish_semantic_manifest,
)
from .signals import request_index_rebuild
from .exceptions import SearchUnavailable, SourceScanLimit

logger = logging.getLogger(__name__)


class SemanticIndexWorker:
    def __init__(self, worker_id: str | None = None):
        self.worker_id = worker_id or f"{socket.gethostname()}-{uuid.uuid4().hex[:12]}"
        self._last_reconciled = None
        self._reconcile_seconds = float(settings.SEMANTIC_SEARCH_RECONCILE_SECONDS)
        if (
            not math.isfinite(self._reconcile_seconds)
            or not 0 <= self._reconcile_seconds <= 300
        ):
            raise ValueError(
                "SEMANTIC_SEARCH_RECONCILE_SECONDS must be between 0 and 300"
            )

    @staticmethod
    def _artifacts_require_rebuild(expected_revision: int, current_source: str) -> bool:
        artifact_dir = Path(settings.SEMANTIC_SEARCH_DATA_DIR)
        try:
            manifest = json.loads(
                (artifact_dir / "manifest.json").read_text(encoding="utf-8")
            )
            return not (
                manifest_matches_configuration(manifest)
                and manifest.get("revision") == expected_revision
                and manifest["entries_sha256"] == current_source
                and artifact_file_digest(
                    _safe_artifact_path(artifact_dir, manifest["entries_file"])
                )
                == current_source
                and artifact_file_digest(
                    _safe_artifact_path(artifact_dir, manifest["index_file"])
                )
                == manifest["index_sha256"]
            )
        except (KeyError, OSError, TypeError, ValueError, SearchUnavailable):
            return True

    def _claim(self, force: bool) -> int | None:
        try:
            return self._claim_checked(force)
        except (DatabaseError, SourceScanLimit):
            # Leave ready on a failed reconciliation only if the DB itself is
            # unavailable; otherwise fail closed until a retry verifies source.
            request_index_rebuild()
            raise

    def _claim_checked(self, force: bool) -> int | None:
        if force:
            # Unlike best-effort post-commit signals, an explicit force must not
            # report success when the database invalidation failed.
            request_index_rebuild(strict=True)

        now_monotonic = time.monotonic()
        reconcile = (
            force
            or self._last_reconciled is None
            or now_monotonic - self._last_reconciled >= self._reconcile_seconds
        )
        previous_built = None
        artifacts_stale = False
        if reconcile:
            current_source = source_digest()
            previous_built = (
                SemanticIndexState.objects.filter(singleton_key=1)
                .values_list("built_revision", flat=True)
                .first()
            )
            # Hash files outside a database transaction: large FAISS files must
            # not hold SQLite read locks while they are checked.
            artifacts_stale = previous_built is None or self._artifacts_require_rebuild(
                previous_built, current_source
            )
            self._last_reconciled = now_monotonic
        with transaction.atomic():
            (
                state,
                created,
            ) = SemanticIndexState.objects.select_for_update().get_or_create(
                singleton_key=1
            )
            now = timezone.now()
            lease_is_active = (
                state.lease_owner
                and state.lease_owner != self.worker_id
                and state.lease_expires_at
                and state.lease_expires_at > now
            )
            if lease_is_active:
                return None

            if (
                not created
                and reconcile
                and (artifacts_stale or state.built_revision != previous_built)
                and state.requested_revision <= state.built_revision
            ):
                state.requested_revision += 1
                state.requested_at = timezone.now()
                state.status = SemanticIndexState.Status.PENDING

            if state.requested_revision <= state.built_revision:
                return None

            state.status = SemanticIndexState.Status.BUILDING
            state.started_at = now
            state.lease_owner = self.worker_id
            state.lease_expires_at = now + timedelta(
                seconds=settings.SEMANTIC_SEARCH_WORKER_LEASE_SECONDS
            )
            state.last_error = ""
            state.save()
            return state.requested_revision

    def _finish(self, target_revision: int, manifest: dict) -> bool:
        with transaction.atomic():
            # select_for_update is ineffective on SQLite. Acquire its writer
            # reservation before reading the source, keeping that snapshot and
            # publication/state commit indivisible with respect to DB writers.
            owned = SemanticIndexState.objects.filter(
                singleton_key=1, lease_owner=self.worker_id
            ).update(lease_owner=self.worker_id)
            if owned != 1:
                raise RuntimeError("semantic index worker lost its lease")
            state = SemanticIndexState.objects.select_for_update().get(singleton_key=1)
            if state.lease_owner != self.worker_id:
                raise RuntimeError("semantic index worker lost its lease")
            if manifest["entries_sha256"] != source_digest():
                state.requested_revision = max(
                    state.requested_revision, target_revision + 1
                )
                state.status = SemanticIndexState.Status.PENDING
                state.lease_owner = ""
                state.lease_expires_at = None
                state.save()
                return False
            publish_semantic_manifest(manifest)
            state.built_revision = max(state.built_revision, target_revision)
            state.completed_at = timezone.now()
            state.lease_owner = ""
            state.lease_expires_at = None
            state.last_error = ""
            state.status = (
                SemanticIndexState.Status.PENDING
                if state.requested_revision > target_revision
                else SemanticIndexState.Status.READY
            )
            state.save()
            return True

    def _fail(self, error: Exception) -> None:
        with transaction.atomic():
            state = SemanticIndexState.objects.select_for_update().get(singleton_key=1)
            if state.lease_owner == self.worker_id:
                state.status = SemanticIndexState.Status.FAILED
                state.lease_owner = ""
                state.lease_expires_at = None
                state.last_error = str(error)[:4000]
                state.save()

    def run_once(self, *, force: bool = False) -> bool:
        target_revision = self._claim(force)
        if target_revision is None:
            return False

        logger.info(
            "building semantic index revision %s with worker %s",
            target_revision,
            self.worker_id,
        )
        try:
            manifest = build_semantic_artifacts(target_revision, publish=False)
            if not self._finish(target_revision, manifest):
                discard_unpublished_artifacts(manifest)
                return False
        except Exception as exc:
            self._fail(exc)
            logger.exception("semantic index revision %s failed", target_revision)
            raise
        logger.info(
            "published semantic index revision %s with %s entries",
            target_revision,
            manifest["entry_count"],
        )
        return True
