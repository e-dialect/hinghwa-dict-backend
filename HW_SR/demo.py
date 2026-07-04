import argparse
import hashlib
import json
import logging
import os
import re
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Set
from urllib.parse import parse_qs, unquote, urlparse

from src.data_loader import FIELD_MAPPING, get_word_word_dto_by_id
from src.matcher import MatcherManager
from src.pre_intent_classifier import PreIntentClassifier
from src.result_formatter import format_result
from src.utils.common_utils import clean_ipa_str

# ========== 日志屏蔽 ==========
warnings.filterwarnings("ignore")
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

# ========== 全局配置 ==========
ENABLE_IPA_MATCH = True
INPUT_RECOGNITION_MODE = "strict"

# ========== 缓存路径配置（自动创建，不用管）==========
CACHE_DIR = "cache"
IPA_CHAR_CACHE = os.path.join(CACHE_DIR, "ipa_chars.json")
DATASET_SIGNATURE = os.path.join(CACHE_DIR, "dataset_signature.txt")

# ========== 全局统一匹配管理器（新架构核心）==========
matcher_manager: Optional[MatcherManager] = None

# ========== 前置意图分类器 ==========
intent_classifier: Optional[PreIntentClassifier] = None


def get_matcher_manager() -> MatcherManager:
    global matcher_manager
    if matcher_manager is None:
        matcher_manager = MatcherManager()
    return matcher_manager


def get_intent_classifier() -> PreIntentClassifier:
    global intent_classifier
    if intent_classifier is None:
        intent_classifier = PreIntentClassifier()
    return intent_classifier


# ========== 模块化意图提取器（未来扩展用） ==========
class IntentExtractor:
    """
    模块化意图提取器：模糊/拼音/IPA 通用
    用于从混合输入中提取核心内容
    """

    @staticmethod
    def extract_ipa(user_input: str) -> Optional[str]:
        return None

    @staticmethod
    def extract_pinyin(user_input: str) -> Optional[str]:
        return None


# ========== 动态 IPA 识别器 ==========
class DynamicIPARecognizer:
    def __init__(self, valid_ipa_chars: set, known_ipa_forms: Optional[Set[str]] = None):
        self.valid_ipa_chars = valid_ipa_chars
        self.known_ipa_forms = known_ipa_forms or set()
        self.basic_chars = set("abcdefghijklmnopqrstuvwxyz0123456789 ")
        self.ipa_special_chars = set("ɒɔøœŋɬʔβɛɯɾʃʂʈɖʐʑŋɱɳ")

    def _strip_phonetic_marks(self, text: str) -> str:
        return re.sub(r"[\d\s'’`]+", "", text.strip().lower())

    def is_ipa_input(self, user_input: str) -> bool:
        s = user_input.strip()
        if not s:
            return False

        if re.search(r"[\u4e00-\u9fa5]", s):
            return False

        for c in s:
            if c not in self.basic_chars and c not in self.valid_ipa_chars:
                return False

        normalized = self._strip_phonetic_marks(s)

        if normalized in self.known_ipa_forms:
            return True

        if any(c.isdigit() for c in s):
            return True

        if any(c in self.ipa_special_chars for c in s):
            return True

        return False


class DynamicPinyinRecognizer:
    def __init__(self):
        self.initials = (
            "zh",
            "ch",
            "sh",
            "b",
            "p",
            "m",
            "f",
            "d",
            "t",
            "n",
            "l",
            "g",
            "k",
            "h",
            "j",
            "q",
            "x",
            "r",
            "z",
            "c",
            "s",
            "y",
            "w",
        )
        self.finals = (
            "iang",
            "iong",
            "uang",
            "ueng",
            "iao",
            "ian",
            "ing",
            "uai",
            "uan",
            "uen",
            "ong",
            "ang",
            "eng",
            "ai",
            "ei",
            "ao",
            "ou",
            "an",
            "en",
            "ia",
            "ie",
            "iu",
            "ua",
            "uo",
            "ui",
            "un",
            "ve",
            "üe",
            "a",
            "o",
            "e",
            "i",
            "u",
            "v",
            "ü",
            "er",
            "ê",
        )
        self._finals_sorted = sorted(set(self.finals), key=len, reverse=True)
        self._initials_sorted = sorted(set(self.initials), key=len, reverse=True)

    def _normalize(self, text: str) -> str:
        return re.sub(r"[\d\s'’`]+", "", text.strip().lower())

    def _is_valid_syllable(self, syllable: str) -> bool:
        if not syllable:
            return False
        for initial in self._initials_sorted:
            if syllable.startswith(initial):
                tail = syllable[len(initial) :]
                return tail in self._finals_sorted
        return syllable in self._finals_sorted

    def is_pinyin_input(self, user_input: str) -> bool:
        s = self._normalize(user_input)
        if not s:
            return False

        if re.search(r"[\u4e00-\u9fa5]", s):
            return False
        if re.search(r"[ɒɔøœŋɬʔβɛɯɾʃʂʈɖʐʑ]", s):
            return False
        if not re.fullmatch(r"[a-züv]+", s):
            return False

        memo = {}

        def can_parse(start: int) -> bool:
            if start == len(s):
                return True
            if start in memo:
                return memo[start]

            for end in range(min(len(s), start + 6), start, -1):
                chunk = s[start:end]
                if self._is_valid_syllable(chunk) and can_parse(end):
                    memo[start] = True
                    return True

            memo[start] = False
            return False

        return can_parse(0)


# ========== 缓存工具类（保留，优化性能）==========
class IPACharCache:
    def __init__(self, all_ipa_list):
        self.all_ipa_list = all_ipa_list

    def _get_dataset_signature(self) -> str:
        try:
            content = "|".join(self.all_ipa_list)
            return hashlib.md5(content.encode("utf-8")).hexdigest()
        except Exception:
            return "unknown"

    def load(self) -> Optional[Set[str]]:
        os.makedirs(CACHE_DIR, exist_ok=True)
        if not os.path.exists(IPA_CHAR_CACHE) or not os.path.exists(DATASET_SIGNATURE):
            return None

        with open(DATASET_SIGNATURE, "r", encoding="utf-8") as f:
            cached_sig = f.read().strip()
        if cached_sig != self._get_dataset_signature():
            return None

        with open(IPA_CHAR_CACHE, "r", encoding="utf-8") as f:
            return set(json.load(f))

    def save(self, chars: Set[str]):
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(IPA_CHAR_CACHE, "w", encoding="utf-8") as f:
            json.dump(list(chars), f, ensure_ascii=False)
        with open(DATASET_SIGNATURE, "w", encoding="utf-8") as f:
            f.write(self._get_dataset_signature())

    def get_chars(self) -> Set[str]:
        cached = self.load()
        if cached is not None:
            return cached

        chars = set()
        for ipa in self.all_ipa_list:
            for c in ipa:
                chars.add(c)
        self.save(chars)
        return chars


# ========== 可扩展融合查询管理器==========
class ExtensibleFusionQueryManager:
    def __init__(self):
        self.original_enabled = True
        self.ipa_enabled = ENABLE_IPA_MATCH
        self.ipa_recognizer = None
        self.pinyin_recognizer = DynamicPinyinRecognizer()
        self.known_ipa_forms = set()

        if self.ipa_enabled:
            try:
                self.ipa_matcher = get_matcher_manager()

                all_ipa = self.ipa_matcher.ipa_matcher.all_ipa_list
                tone_free_ipa = getattr(
                    self.ipa_matcher.ipa_matcher,
                    "all_tone_free_ipa_list",
                    [],
                )
                self.known_ipa_forms = {
                    self._strip_route_marks(item) for item in all_ipa + tone_free_ipa
                }
                cache = IPACharCache(all_ipa)
                self.valid_ipa_chars = cache.get_chars()
                self.ipa_recognizer = DynamicIPARecognizer(
                    self.valid_ipa_chars,
                    self.known_ipa_forms,
                )
            except Exception as e:
                print(f"IPA 模块加载失败：{e}")
                self.ipa_enabled = False

    @staticmethod
    def _strip_route_marks(text: str) -> str:
        return re.sub(r"[\d\s'’`]+", "", str(text).strip().lower())

    def _route_query(self, user_input: str) -> str:
        if re.search(r"[\u4e00-\u9fa5]", user_input):
            return "original"

        if self.ipa_enabled and self.ipa_recognizer and self.ipa_recognizer.is_ipa_input(user_input):
            return "ipa"

        if self.pinyin_recognizer.is_pinyin_input(user_input):
            return "pinyin"

        return "original"

    def query_detail(self, user_input: str) -> Dict[str, Any]:
        """统一查询入口：返回可直接用于 API 的结构化结果"""
        classification = get_intent_classifier().classify(user_input)
        intent = classification["intent"]
        confidence = classification["confidence"]

        print(f"[意图识别] 类型: {intent}, 置信度: {confidence:.2f}")

        if intent == "dialect":
            results = self._dialect_query_items(user_input)
        elif intent == "ipa":
            results = self._ipa_query_items(user_input)
        elif intent == "pinyin":
            results = self._pinyin_query_items(user_input)
        elif intent == "pinyin_llm":
            pinyin_parts = classification.get("pinyin_parts", [])
            results = self._pinyin_llm_query_items(user_input, pinyin_parts)
        elif intent == "mixed":
            results = self._mixed_query_items(user_input)
        else:
            results = self._original_query_items(user_input)

        adapted_results = self._adapt(results)
        return {
            "query": user_input,
            "intent": intent,
            "confidence": confidence,
            "count": len(adapted_results),
            "results": adapted_results,
            "formatted": format_result(adapted_results),
        }

    def query(self, user_input: str) -> str:
        """兼容原有 CLI 入口，仍然返回格式化文本"""
        return self.query_detail(user_input)["formatted"]

    def _ipa_query_items(self, user_input: str) -> List[Dict]:
        """
        新版 IPA 查询：
        自动支持 → 简易发音精准 + 标准IPA精准 + 模糊匹配
        """
        res = self.ipa_matcher.ipa_query(user_input, top_k=5)
        if res:
            return res
        return []

    def _original_query_items(self, user_input: str) -> List[Dict]:
        return self.ipa_matcher.core_query(user_input)

    def _dialect_query_items(self, user_input: str) -> List[Dict]:
        """方言词查询路径"""
        return get_matcher_manager().dialect_word_query(user_input, top_k=5) or []

    def _pinyin_query_items(self, user_input: str) -> List[Dict]:
        """拼音查询路径"""
        return get_matcher_manager().pinyin_query(user_input, top_k=5) or []

    def _pinyin_llm_query_items(self, user_input: str, pinyin_parts: List[str]) -> List[Dict]:
        """
        拼音LLM查询路径：处理方言词+拼音组合查询

        处理逻辑：
        1. 提取方言词部分和拼音部分
        2. 分别进行匹配
        3. 合并并去重结果
        4. 如果拼音匹配失败，降级到原始文本查询

        例如："郎ba5" → 分别查询"郎"和"ba5"，合并结果
        """
        results = []

        if not pinyin_parts:
            print("[降级处理] 未提取到拼音片段，使用原始查询路径")
            return self._original_query_items(user_input)

        seen_parts = set()
        for part in pinyin_parts:
            if part in seen_parts:
                continue
            seen_parts.add(part)

            if any(char >= "\u4e00" and char <= "\u9fa5" for char in part):
                chinese_part = "".join([c for c in part if c >= "\u4e00" and c <= "\u9fa5"])
                pinyin_part = "".join([c for c in part if c < "\u4e00" or c > "\u9fa5"])

                if chinese_part:
                    dialect_res = get_matcher_manager().dialect_word_query(chinese_part, top_k=5)
                    results.extend(dialect_res)

                if pinyin_part:
                    pinyin_res = get_matcher_manager().pinyin_query(pinyin_part, top_k=5)
                    results.extend(pinyin_res)
            else:
                pinyin_res = get_matcher_manager().pinyin_query(part, top_k=5)
                results.extend(pinyin_res)

        seen_words = set()
        unique_results = []
        for res in results:
            dialect_word = res.get("方言词", "")
            if dialect_word and dialect_word not in seen_words:
                seen_words.add(dialect_word)
                unique_results.append(res)

        if unique_results:
            return unique_results

        print("[降级处理] 拼音匹配失败，使用原始查询路径")
        return self._original_query_items(user_input)

    def _mixed_query_items(self, user_input: str) -> List[Dict]:
        """
        混合查询路径：同时包含中文和拼音的查询

        处理逻辑：
        1. 先尝试原始文本查询
        2. 如果结果不足，尝试拼音查询
        3. 合并去重结果
        """
        results = []

        core_res = self.ipa_matcher.core_query(user_input)
        results.extend(core_res)

        pinyin_parts = get_intent_classifier()._extract_pinyin_parts(user_input)
        if pinyin_parts:
            for part in pinyin_parts:
                if not any(char >= "\u4e00" and char <= "\u9fa5" for char in part):
                    pinyin_res = get_matcher_manager().pinyin_query(part, top_k=3)
                    results.extend(pinyin_res)

        seen_words = set()
        unique_results = []
        for res in results:
            dialect_word = res.get("方言词", "")
            if dialect_word and dialect_word not in seen_words:
                seen_words.add(dialect_word)
                unique_results.append(res)

        if unique_results:
            return unique_results
        return []

    def _adapt(self, res):
        adapted = []
        for item in res:
            dto = get_word_word_dto_by_id(item.get("id"))
            if dto is None:
                dto = {
                    "id": item.get("id"),
                    "word": item.get("方言词", ""),
                    "definition": "",
                    "annotation": "",
                    "mandarin": "",
                    "standard_ipa": item.get("标准发音", ""),
                    "standard_pinyin": item.get("简易发音", ""),
                    "views": 0,
                    "visibility": False,
                    "contributor_id": 0,
                    "tags": "",
                    "方言词": item.get("方言词", ""),
                    "简易发音": item.get("简易发音", ""),
                    "标准发音": item.get("标准发音", ""),
                    "释义注释": item.get("释义注释", ""),
                }
            adapted.append(dto)
        return adapted


class QueryHTTPRequestHandler(BaseHTTPRequestHandler):
    manager: Optional[ExtensibleFusionQueryManager] = None

    @classmethod
    def get_manager(cls) -> ExtensibleFusionQueryManager:
        if cls.manager is None:
            cls.manager = ExtensibleFusionQueryManager()
        return cls.manager

    def _write_json(self, status_code: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        raw_body = self.rfile.read(content_length).decode("utf-8")
        if not raw_body.strip():
            return {}
        try:
            return json.loads(raw_body)
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._write_json(200, {"ok": True, "message": "service running"})
            return

        if parsed.path == "/":
            self._write_json(
                200,
                {
                    "ok": True,
                    "message": "请使用 /query?query=xxx、POST /query 或直接访问 /你的查询词",
                    "examples": ["/query?query=郎", "/郎", "/郎罢"],
                },
            )
            return

        if parsed.path == "/query":
            params = parse_qs(parsed.query)
            query_text = params.get("query", [""])[0].strip()
            if not query_text:
                self._write_json(400, {"ok": False, "error": "query 参数不能为空"})
                return
            self._write_json(200, {"ok": True, **self.get_manager().query_detail(query_text)})
            return

        if parsed.path.startswith("/"):
            raw_query = unquote(parsed.path.lstrip("/")).strip()
            if raw_query:
                self._write_json(200, {"ok": True, **self.get_manager().query_detail(raw_query)})
                return

        self._write_json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/query":
            self._write_json(404, {"ok": False, "error": "not found"})
            return

        payload = self._read_json_body()
        query_text = str(payload.get("query", "")).strip()
        if not query_text:
            self._write_json(400, {"ok": False, "error": "请求体中的 query 不能为空"})
            return

        self._write_json(200, {"ok": True, **self.get_manager().query_detail(query_text)})


def run_server(host: str = "0.0.0.0", port: int = 8088) -> None:
    server = ThreadingHTTPServer((host, port), QueryHTTPRequestHandler)
    print(f"HTTP 服务已启动：http://{host}:{port}")
    print("可用接口：GET /health, GET /query?query=..., POST /query, GET /<query>")
    server.serve_forever()


# ========== main ==========
def main():
    parser = argparse.ArgumentParser(description="莆仙方言精准检索系统")
    parser.add_argument(
        "--mode",
        choices=["serve", "cli"],
        default="serve",
        help="启动模式，serve 为 HTTP 服务，cli 为命令行交互",
    )
    parser.add_argument("--host", default="0.0.0.0", help="HTTP 服务监听地址")
    parser.add_argument("--port", type=int, default=8088, help="HTTP 服务端口")
    args = parser.parse_args()

    if args.mode == "serve":
        run_server(args.host, args.port)
        return

    manager = ExtensibleFusionQueryManager()

    print("=" * 60)
    print("        莆仙方言精准检索系统")
    print("=" * 60)
    print("支持查询：")
    print("1. 方言词查询")
    print("2. 普通话 / 释义查询")
    if ENABLE_IPA_MATCH and manager.ipa_enabled:
        print("3. IPA查询（精准 + 模糊）")
    print("4. 拼音查询")
    print("输入 q/quit 退出\n")

    while True:
        user_input = input("请输入查询：").strip()
        if user_input.lower() in ["q", "quit"]:
            print("再见！")
            break
        if not user_input:
            print("查询不能为空，请重新输入！\n")
            continue

        try:
            formatted_result = manager.query(user_input)
            print("\n" + formatted_result + "\n")
        except Exception as e:
            print(f"出错：{e}\n")


if __name__ == "__main__":
    main()