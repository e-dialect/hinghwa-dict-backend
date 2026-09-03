from __future__ import annotations

from django.db import DatabaseError

from word.models import SemanticIndexState

from .artifacts import manifest_matches_configuration, repository
from .encoder import BGEEncoder
from .exceptions import SearchUnavailable
from .llm import DeepSeekQueryParser
from .matcher import SearchMatcher

_encoder = BGEEncoder()
_llm_parser = DeepSeekQueryParser()


def _get_ready_revision() -> int:
    try:
        state = SemanticIndexState.objects.get(singleton_key=1)
    except (SemanticIndexState.DoesNotExist, DatabaseError) as exc:
        raise SearchUnavailable("semantic index state is unavailable") from exc
    if (
        state.status != SemanticIndexState.Status.READY
        or state.built_revision < state.requested_revision
    ):
        raise SearchUnavailable(
            f"semantic index is {state.status} at "
            f"{state.built_revision}/{state.requested_revision}"
        )
    return state.built_revision


def semantic_search_word_ids(
    query: str,
    *,
    allowed_ids: set[int] | None = None,
    limit: int = 200,
) -> list[int]:
    limit = min(max(limit, 0), 200)
    ready_revision = _get_ready_revision()
    bundle = repository.load()
    if not manifest_matches_configuration(bundle.manifest):
        raise SearchUnavailable("semantic index model configuration is stale")
    if bundle.manifest.get("revision") != ready_revision:
        raise SearchUnavailable("semantic index files do not match database state")
    return SearchMatcher(
        bundle,
        encoder=_encoder,
        llm_parser=_llm_parser,
    ).search(query, allowed_ids=allowed_ids, limit=limit)
