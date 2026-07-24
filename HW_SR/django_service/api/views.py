from __future__ import annotations

import json
from typing import Any, Dict, Optional

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

_MANAGER: Optional[Any] = None


def get_manager() -> Any:
    global _MANAGER
    if _MANAGER is None:
        # Delay heavy imports until first real query to keep Django boot lightweight.
        from demo import ExtensibleFusionQueryManager

        _MANAGER = ExtensibleFusionQueryManager()
    return _MANAGER


def _load_data_helpers() -> tuple[Any, Any, Any]:
    from src.data_loader import get_word_word_dto_by_id, get_word_word_dtos_by_word
    from src.result_formatter import format_result

    return get_word_word_dto_by_id, get_word_word_dtos_by_word, format_result


def _with_cors(response: JsonResponse) -> JsonResponse:
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def _json_response(status_code: int, payload: Dict[str, Any]) -> JsonResponse:
    return _with_cors(JsonResponse(payload, status=status_code, json_dumps_params={"ensure_ascii": False}))


def _options_response() -> HttpResponse:
    response = HttpResponse(status=204)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def _extract_query_text(request: HttpRequest) -> str:
    if request.method == "GET":
        return request.GET.get("query", "").strip()

    raw_body = request.body.decode("utf-8", errors="ignore").strip()
    if not raw_body:
        return ""

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return ""

    return str(payload.get("query", "")).strip()


def _dto_to_api_payload(dto: Dict[str, Any]) -> Dict[str, Any]:
    _, _, format_result = _load_data_helpers()
    return {
        "ok": True,
        "query_key": dto.get("id"),
        "query_type": "id",
        "query_id": dto.get("id"),
        "count": 1,
        "results": [dto],
        "formatted": format_result([dto]),
    }


def _dto_list_to_api_payload(query_key: str, dtos: list[Dict[str, Any]], query_type: str) -> Dict[str, Any]:
    _, _, format_result = _load_data_helpers()
    return {
        "ok": True,
        "query_key": query_key,
        "query_type": query_type,
        "count": len(dtos),
        "results": dtos,
        "formatted": format_result(dtos),
    }


@require_http_methods(["GET", "OPTIONS"])
def health_view(request: HttpRequest) -> JsonResponse:
    if request.method == "OPTIONS":
        return _options_response()
    return _json_response(200, {"ok": True, "message": "service running"})


@require_http_methods(["GET", "OPTIONS"])
def query_by_id_view(request: HttpRequest, word_id: int) -> JsonResponse:
    if request.method == "OPTIONS":
        return _options_response()

    try:
        get_word_word_dto_by_id, _, _ = _load_data_helpers()
        dto = get_word_word_dto_by_id(word_id)
    except Exception as exc:
        return _json_response(503, {"ok": False, "error": f"服务依赖未就绪: {exc}"})

    if dto is None:
        return _json_response(404, {"ok": False, "error": f"未找到 id={word_id} 对应的词条"})

    return _json_response(200, _dto_to_api_payload(dto))


@require_http_methods(["GET", "OPTIONS"])
def query_by_word_view(request: HttpRequest, word: str) -> JsonResponse:
    if request.method == "OPTIONS":
        return _options_response()

    query_word = str(word).strip()
    if not query_word:
        return _json_response(400, {"ok": False, "error": "word 路径参数不能为空"})

    try:
        _, get_word_word_dtos_by_word, _ = _load_data_helpers()
        dtos = get_word_word_dtos_by_word(query_word)
    except Exception as exc:
        return _json_response(503, {"ok": False, "error": f"服务依赖未就绪: {exc}"})

    if dtos:
        return _json_response(200, _dto_list_to_api_payload(query_word, dtos, "word"))

    try:
        result = get_manager().query_detail(query_word)
    except Exception as exc:
        return _json_response(503, {"ok": False, "error": f"检索服务暂不可用: {exc}"})

    return _json_response(200, {"ok": True, "query_key": query_word, "query_type": "general", **result})


@require_http_methods(["GET", "POST", "OPTIONS"])
def query_view(request: HttpRequest, query: str = "") -> JsonResponse:
    if request.method == "OPTIONS":
        return _options_response()

    query_text = query.strip() or _extract_query_text(request)
    if not query_text:
        return _json_response(400, {"ok": False, "error": "query 参数或路径参数不能为空"})

    try:
        result = get_manager().query_detail(query_text)
    except Exception as exc:
        return _json_response(503, {"ok": False, "error": f"检索服务暂不可用: {exc}"})

    return _json_response(200, {"ok": True, **result})