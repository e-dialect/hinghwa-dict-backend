from typing import List, Dict
from .base_matcher import BaseMatcher
from src.data_loader import exact_match_search, get_full_df


class DialectWordMatcher(BaseMatcher):
    """
    方言词精准匹配器：封装 exact_match_search
    返回与现有 demo 行为一致的结果格式
    """
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.df = get_full_df()

    def match(self, query: str, top_k: int = 5) -> List[Dict]:
        if not query:
            return []
        # 按原有逻辑，对于方言查询优先做 exact_match_search
        results = []
        # exact_match_search 接受单个关键词或多个，保持一致调用
        for kw in [query]:
            res = exact_match_search(kw)
            if res:
                results.extend(res)

        # 去重（按方言词）
        seen = set()
        unique = []
        from src.data_loader import FIELD_MAPPING
        for it in results:
            w = it.get(FIELD_MAPPING["dialect_word"], None)
            if w and w not in seen:
                seen.add(w)
                unique.append(it)

        return unique[:top_k]
