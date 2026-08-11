from __future__ import annotations

import logging
import json
import socket
import uuid
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from word.models import SemanticIndexState

from .artifacts import (
    build_semantic_artifacts,
    manifest_matches_configuration,
    publish_semantic_manifest,
)
from .signals import request_index_rebuild

logger = logging.getLogger(__name__)


class SemanticIndexWorker:
    def __init__(self, worker_id: str | None = None):
        self.worker_id = worker_id or f"{socket.gethostname()}-{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _artifacts_require_rebuild(expected_revision: int) -> bool:
        artifact_dir = Path(settings.SEMANTIC_SEARCH_DATA_DIR)
        try:
            manifest = json.loads(
                (artifact_dir / "manifest.json").read_text(encoding="utf-8")
            )
            return not (
                manifest_matches_configuration(manifest)
                and manifest.get("revision") == expected_revision
                and (artifact_dir / manifest["entries_file"]).is_file()
                and (artifact_dir / manifest["index_file"]).is_file()
            )
        except (KeyError, OSError, TypeError, ValueError):
            return True

    def _claim(self, force: bool) -> int | None:
        if force:
            request_index_rebuild()

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
                and self._artifacts_require_rebuild(state.built_revision)
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

    def _finish(self, target_revision: int, manifest: dict) -> None:
        with transaction.atomic():
            state = SemanticIndexState.objects.select_for_update().get(singleton_key=1)
            if state.lease_owner != self.worker_id:
                raise RuntimeError("semantic index worker lost its lease")
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
            self._finish(target_revision, manifest)
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
