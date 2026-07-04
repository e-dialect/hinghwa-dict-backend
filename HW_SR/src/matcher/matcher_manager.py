from typing import List, Dict
from .ipa_matcher import IPAMatcher
from .dialect_matcher import DialectWordMatcher
from .core_matcher import CoreMatcher
from .pinyin_matcher import PinyinMatcher


class MatcherManager:
    """
    全系统匹配器统一调度管理器
    所有上层业务（demo/main）仅通过此类调用所有匹配功能
    实现解耦、统一管理、方便扩展
    """
    def __init__(self):
        # ====================== 已实现模块 ======================
        self.ipa_matcher = IPAMatcher()
        # 方言词与原始查询（普通话/释义）匹配器
        self.dialect_word_matcher = DialectWordMatcher()
        self.core_matcher = CoreMatcher()
        # 拼音匹配器
        self.pinyin_matcher = PinyinMatcher()

        # ====================== 未来预留模块（空接口占位，无需实现） ======================
        # 后续新增：语义向量检索匹配器
        # self.semantic_matcher = SemanticMatcher()

    def ipa_query(self, query: str, top_k: int = 3) -> List[Dict]:
        """IPA查询统一入口（精准+模糊全部包含）"""
        return self.ipa_matcher.match(query, top_k)

    def dialect_word_query(self, query: str, top_k: int = 3) -> List[Dict]:
        """方言词精准查询入口（封装 exact_match_search）"""
        return self.dialect_word_matcher.match(query, top_k)

    def core_query(self, query: str, top_k: int = 5) -> List[Dict]:
        """原始查询统一入口（parse_query + core_search）"""
        return self.core_matcher.match(query, top_k)

    def pinyin_query(self, query: str, top_k: int = 3) -> List[Dict]:
        """拼音查询统一入口"""
        return self.pinyin_matcher.match(query, top_k)

    # ====================== 未来预留统一接口（严格对齐BaseMatcher） ======================
    # def semantic_query(self, query: str, top_k: int = 3) -> List[Dict]:
    #     return self.semantic_matcher.match(query, top_k)