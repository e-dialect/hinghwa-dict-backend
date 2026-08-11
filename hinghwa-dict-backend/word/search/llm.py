from __future__ import annotations

import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class DeepSeekQueryParser:
    """Optional query rewriter; disabled unless explicitly configured."""

    def rewrite(self, query: str) -> str | None:
        if not settings.SEMANTIC_SEARCH_LLM_ENABLED:
            return None
        if not settings.SEMANTIC_SEARCH_LLM_API_KEY:
            logger.warning("semantic LLM parser is enabled without an API key")
            return None

        import requests

        prompt = (
            "Extract only the dictionary-search keywords from the user's query. "
            'Return strict JSON in the form {"keywords":["keyword"]}. '
            "Do not include Markdown or additional fields."
        )
        try:
            response = requests.post(
                f"{settings.SEMANTIC_SEARCH_LLM_BASE_URL.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.SEMANTIC_SEARCH_LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.SEMANTIC_SEARCH_LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": query},
                    ],
                    "temperature": 0,
                    "max_tokens": 100,
                },
                timeout=(1.0, settings.SEMANTIC_SEARCH_LLM_TIMEOUT_SECONDS),
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            parsed = json.loads(content)
            if not isinstance(parsed, dict) or set(parsed) != {"keywords"}:
                raise ValueError("response must contain only keywords")
            keywords = parsed.get("keywords")
            if not isinstance(keywords, list):
                raise ValueError("keywords must be a list")
            normalized = [
                keyword.strip()[:100]
                for keyword in keywords
                if isinstance(keyword, str) and keyword.strip()
            ][:10]
            return " ".join(normalized) or None
        except (KeyError, TypeError, ValueError, requests.RequestException):
            logger.warning(
                "semantic LLM parser failed; using the local query", exc_info=True
            )
            return None
