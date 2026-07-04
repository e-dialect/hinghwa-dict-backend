"""拼音匹配器

实现BaseMatcher接口，支持拼音查询方言词
"""
from typing import List, Dict
from .base_matcher import BaseMatcher
from src.data_loader import get_full_df, FIELD_MAPPING
from src.pinyin_to_ipa import pinyin_to_ipa, generate_candidates, parse_pinyin
from .ipa_constants import CONFUSION_MAP, MATCH_WEIGHTS


class PinyinMatcher(BaseMatcher):
    """
    拼音匹配器：支持拼音查询方言词
    
    匹配流程：
    1. 解析用户输入的拼音
    2. 生成候选词（支持声调容错）
    3. 直接匹配发音索引
    4. 转换为IPA后调用IPA匹配器
    5. 合并结果并去重
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.df = get_full_df()
        
        # 初始化IPA匹配器（用于复用模糊匹配能力）
        from .ipa_matcher import IPAMatcher
        self.ipa_matcher = IPAMatcher(debug=debug)
        
        # 构建发音索引
        self.pron_index = {}
        self._build_pron_index()
    
    def _build_pron_index(self):
        """构建发音到词条的索引"""
        for _, row in self.df.iterrows():
            row_dict = row.to_dict()
            dialect_word = row_dict.get(FIELD_MAPPING["dialect_word"], "").strip()
            simple_pron = row_dict.get(FIELD_MAPPING["simple_pron"], "").strip()
            standard_pron = row_dict.get(FIELD_MAPPING["standard_pron"], "").strip()
            
            # 将发音作为索引
            if simple_pron and simple_pron != "nan":
                pron_key = simple_pron.lower().replace(" ", "")
                if pron_key not in self.pron_index:
                    self.pron_index[pron_key] = []
                self.pron_index[pron_key].append(row_dict)
            
            if standard_pron and standard_pron != "nan":
                pron_key = standard_pron.lower().replace(" ", "")
                if pron_key not in self.pron_index:
                    self.pron_index[pron_key] = []
                self.pron_index[pron_key].append(row_dict)
    
    def match(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        统一匹配接口
        
        :param query: 用户输入的拼音查询串
        :param top_k: 返回结果数量
        :return: 结构化结果列表
        """
        if not query:
            return []
        
        if self.debug:
            print(f"\n=== 拼音匹配开始 ===")
            print(f"原始输入: {query}")
        
        all_results = []
        
        # 1. 直接发音匹配
        direct_results = self._direct_pron_match(query)
        if self.debug:
            print(f"[拼音匹配] 直接匹配结果: {len(direct_results)}条")
        all_results.extend(direct_results)
        
        # 2. 候选词匹配（声调容错）
        candidate_results = self._candidate_match(query)
        if self.debug:
            print(f"[拼音匹配] 候选词匹配结果: {len(candidate_results)}条")
        all_results.extend(candidate_results)
        
        # 3. 拼音转IPA匹配
        ipa_results = self._ipa_match(query)
        if self.debug:
            print(f"[拼音匹配] IPA匹配结果: {len(ipa_results)}条")
        all_results.extend(ipa_results)
        
        # 去重并排序
        unique_results = self._deduplicate_and_sort(all_results)
        
        if self.debug:
            print(f"[拼音匹配] 最终结果: {len(unique_results)}条")
        
        return unique_results[:top_k]
    
    def _direct_pron_match(self, query: str) -> List[Dict]:
        """直接发音匹配"""
        query_normalized = query.lower().replace(" ", "")
        results = []
        
        if query_normalized in self.pron_index:
            for item in self.pron_index[query_normalized]:
                cp = item.copy()
                cp["相似度"] = MATCH_WEIGHTS["exact_match"]
                cp["匹配类型"] = "拼音精准匹配"
                results.append(cp)
        
        return results
    
    def _candidate_match(self, query: str) -> List[Dict]:
        """候选词匹配（声调容错+混淆规则）"""
        query_normalized = query.lower().replace(" ", "")
        results = []
        
        # 生成候选词
        candidates = generate_candidates(query)
        
        # 利用CONFUSION_MAP生成混淆候选
        confusion_candidates = self._generate_confusion_candidates(query_normalized)
        candidates.extend(confusion_candidates)
        
        for candidate in set(candidates):
            if candidate in self.pron_index and candidate != query_normalized:
                similarity = self._calculate_similarity(query_normalized, candidate)
                for item in self.pron_index[candidate]:
                    cp = item.copy()
                    cp["相似度"] = similarity
                    cp["匹配类型"] = "拼音模糊匹配"
                    cp["候选词"] = candidate
                    results.append(cp)
        
        return results
    
    def _generate_confusion_candidates(self, query: str) -> List[str]:
        """利用CONFUSION_MAP生成混淆候选词"""
        candidates = []
        
        # 逐字符应用混淆规则
        for i, char in enumerate(query):
            if char in CONFUSION_MAP:
                for replacement in CONFUSION_MAP[char]:
                    if replacement:  # 跳过空串替换（安全约束）
                        new_candidate = query[:i] + replacement + query[i+1:]
                        candidates.append(new_candidate)
        
        # 检查多字符替换
        for pattern, replacements in CONFUSION_MAP.items():
            if len(pattern) > 1 and pattern in query:
                for replacement in replacements:
                    if replacement:
                        new_candidate = query.replace(pattern, replacement)
                        candidates.append(new_candidate)
        
        return candidates
    
    def _calculate_similarity(self, original: str, candidate: str) -> float:
        """基于混淆类型计算相似度"""
        score = MATCH_WEIGHTS["exact_match"]
        
        # 检查每个字符的混淆类型
        for o_char, c_char in zip(original, candidate):
            if o_char != c_char:
                # 检查是否是声母混淆
                if o_char in CONFUSION_MAP and c_char in CONFUSION_MAP[o_char]:
                    score *= MATCH_WEIGHTS["consonant_confusion"]
                # 检查是否是韵母混淆
                elif any(o_char in key for key in CONFUSION_MAP if len(key) == 1):
                    score *= MATCH_WEIGHTS["vowel_confusion"]
                else:
                    score *= 0.7  # 未知混淆类型
        
        return round(score, 3)
    
    def _ipa_match(self, query: str) -> List[Dict]:
        """拼音转IPA后匹配"""
        ipa_str = pinyin_to_ipa(query)
        results = []
        
        if ipa_str:
            ipa_results = self.ipa_matcher.match(ipa_str, top_k=5)
            for item in ipa_results:
                cp = item.copy()
                cp["匹配类型"] = "拼音转IPA匹配"
                cp["原始拼音"] = query
                cp["转换后IPA"] = ipa_str
                results.append(cp)
        
        return results
    
    def _deduplicate_and_sort(self, results: List[Dict]) -> List[Dict]:
        """去重并按相似度排序"""
        seen = set()
        unique_results = []
        
        for item in results:
            dialect_word = item.get(FIELD_MAPPING["dialect_word"], item.get("方言词", ""))
            if dialect_word and dialect_word not in seen:
                seen.add(dialect_word)
                unique_results.append(item)
        
        # 按相似度排序
        unique_results.sort(key=lambda x: x.get("相似度", 0), reverse=True)
        
        return unique_results