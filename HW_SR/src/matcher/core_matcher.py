from typing import List, Dict
from .base_matcher import BaseMatcher
from src.query_rewriter import parse_query
from src.vector_db import core_search


class CoreMatcher(BaseMatcher):
    """
    封装原先 demo 中的 parse_query + core_search 行为
    负责普通话/释义与方言词的统一调度（保留原有逻辑）
    """
    def __init__(self, debug: bool = False):
        self.debug = debug

    def match(self, query: str, top_k: int = 5) -> List[Dict]:
        if not query:
            return []
        parsed = parse_query(query)
        results = core_search(parsed)
        return results[:top_k]
