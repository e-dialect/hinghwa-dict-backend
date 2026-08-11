from __future__ import annotations

import logging

from django.db import DatabaseError, transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from word.models import SemanticIndexState, Word

logger = logging.getLogger(__name__)

SEARCH_SOURCE_FIELDS = (
    "word",
    "definition",
    "annotation",
    "mandarin",
    "standard_ipa",
    "standard_pinyin",
    "visibility",
)


def request_index_rebuild() -> None:
    """Coalesce source changes into a monotonically increasing revision."""
    try:
        with transaction.atomic():
            state, _ = SemanticIndexState.objects.select_for_update().get_or_create(
                singleton_key=1
            )
            state.requested_revision += 1
            state.requested_at = timezone.now()
            if state.status != SemanticIndexState.Status.BUILDING:
                state.status = SemanticIndexState.Status.PENDING
            state.save(update_fields=["requested_revision", "requested_at", "status"])
    except DatabaseError:
        # Migrations and first-time setup can import models before this table exists.
        logger.debug("semantic index state is not ready", exc_info=True)


@receiver(pre_save, sender=Word)
def record_search_source_change(
    sender, instance, raw=False, update_fields=None, **kwargs
):
    if raw:
        instance._semantic_source_changed = False
        return
    if instance.pk is None:
        instance._semantic_source_changed = True
        return
    if update_fields is not None and not set(update_fields).intersection(
        SEARCH_SOURCE_FIELDS
    ):
        instance._semantic_source_changed = False
        return

    previous = (
        sender.objects.filter(pk=instance.pk).values(*SEARCH_SOURCE_FIELDS).first()
    )
    instance._semantic_source_changed = previous is None or any(
        previous[field] != getattr(instance, field) for field in SEARCH_SOURCE_FIELDS
    )


@receiver(post_save, sender=Word)
def enqueue_search_rebuild_after_save(sender, instance, raw=False, **kwargs):
    if not raw and getattr(instance, "_semantic_source_changed", False):
        transaction.on_commit(request_index_rebuild)


@receiver(post_delete, sender=Word)
def enqueue_search_rebuild_after_delete(sender, instance, **kwargs):
    transaction.on_commit(request_index_rebuild)
