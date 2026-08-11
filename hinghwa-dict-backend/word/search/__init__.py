"""In-process semantic retrieval for the word Django application."""

from .exceptions import SearchUnavailable


def semantic_search_word_ids(
    query: str,
    *,
    allowed_ids: set[int] | None = None,
    limit: int = 200,
) -> list[int]:
    from .service import semantic_search_word_ids as search

    return search(query, allowed_ids=allowed_ids, limit=limit)


__all__ = ["SearchUnavailable", "semantic_search_word_ids"]
