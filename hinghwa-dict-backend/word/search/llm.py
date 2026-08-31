from __future__ import annotations

import json
import logging
import re

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
            "你是中文词典搜索重写器。请从用户输入中提取最关键的检索词，返回严格 JSON。"
            '格式必须是 {"keywords":["keyword1","keyword2"]}。'
            "只返回 JSON，不要 Markdown，不要解释，不要额外字段。"
            "如果没法提取，就返回 {\"keywords\":[]}。"
        )
        try:
            payload = {
                "model": settings.SEMANTIC_SEARCH_LLM_MODEL,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query},
                ],
                "temperature": 0,
                "max_tokens": 100,
            }
            enable_thinking = bool(
                "reasoner" in settings.SEMANTIC_SEARCH_LLM_MODEL.lower()
                or "r1" in settings.SEMANTIC_SEARCH_LLM_MODEL.lower()
            )
            attempts = [payload]
            if enable_thinking:
                attempts.append({**payload, "extra_body": {"chat_template_kwargs": {"enable_thinking": False}}})
            else:
                attempts.append({**payload, "extra_body": {"chat_template_kwargs": {"enable_thinking": False}}})

            last_error = None
            for attempt in attempts:
                try:
                    response = requests.post(
                        f"{settings.SEMANTIC_SEARCH_LLM_BASE_URL.rstrip('/')}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.SEMANTIC_SEARCH_LLM_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json=attempt,
                        timeout=(1.0, settings.SEMANTIC_SEARCH_LLM_TIMEOUT_SECONDS),
                    )
                    response.raise_for_status()
                    content = response.json()["choices"][0]["message"]["content"].strip()

                    if content.startswith("```"):
                        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.I)
                        content = re.sub(r"\s*```$", "", content, flags=re.S)

                    match = re.search(r"\{.*\}", content, flags=re.S)
                    if match:
                        content = match.group(0)

                    parsed = json.loads(content)
                    if not isinstance(parsed, dict) or "keywords" not in parsed:
                        raise ValueError("response must include a keywords field")
                    keywords = parsed.get("keywords")
                    if not isinstance(keywords, list):
                        raise ValueError("keywords must be a list")
                    normalized = [
                        str(keyword).strip()[:100]
                        for keyword in keywords
                        if isinstance(keyword, str) and keyword.strip()
                    ][:10]
                    return " ".join(normalized) or None
                except requests.HTTPError as exc:
                    last_error = exc
                    if exc.response is not None and exc.response.status_code in {400, 422}:
                        continue
                    raise
                except (KeyError, TypeError, ValueError, requests.RequestException) as exc:
                    last_error = exc
                    continue

            raise last_error or ValueError("LLM parsing failed")
        except (KeyError, TypeError, ValueError, requests.RequestException):
            logger.warning(
                "semantic LLM parser failed; using the local query", exc_info=True
            )
            return None
