import re
import Levenshtein
from typing import List, Dict
from .ipa_constants import (
    CONFUSION_MAP, 
    TONE_MAP, 
    SANDHI_RULES, 
    ASR_ERROR_MAP,
    SANDHI_CONSONANTS,
    ACCENT_MAP,
    MATCH_WEIGHTS,
    SAFETY_CONSTRAINTS
)
from src.data_loader import get_full_df, FIELD_MAPPING
from src.utils.common_utils import clean_ipa_str


class IPAMatcher:
    """
    修复版莆仙方言IPA精准&模糊匹配器
    完整三层匹配架构：
    1. 精准匹配
    2. 规则模糊匹配（新增ʔ硬约束，禁止随意抹除入声尾）
    3. 分段加权兜底匹配（残缺IPA省音/漏写中间音节专属方案）
    
    修复问题：
    1. 数据加载和索引构建问题
    2. 匹配逻辑错误
    3. 调试信息不足
    """

    def __init__(self, enable_rule_fuzzy=True, enable_edit_fuzzy=True, debug=False):
        self.enable_rule_fuzzy = enable_rule_fuzzy
        self.enable_edit_fuzzy = enable_edit_fuzzy
        self.debug = debug

        # 加载全量方言词典
        self.dialect_df = get_full_df()

        # 双层发音索引（简易发音 + 标准IPA）
        self.simple_ipa_index = {}
        self.standard_ipa_index = {}
        self.tone_free_simple_ipa_index = {}
        self.tone_free_standard_ipa_index = {}
        self.all_ipa_list = []
        self.all_tone_free_ipa_list = []

        # 调试信息
        if self.debug:
            print(f"数据加载完成，共{len(self.dialect_df)}条词条")
            print(f"字段映射: {FIELD_MAPPING}")

        self._build_index()

    def _strip_tone_digits(self, ipa: str) -> str:
        return re.sub(r"\d+", "", ipa)

    def _build_index(self):
        """
        构建全局索引
        所有发音统一经过工具函数清洗后再入库，保证匹配统一
        """
        std_count = 0
        simple_count = 0
        
        for _, row in self.dialect_df.iterrows():
            row_dict = row.to_dict()
            
            # 使用正确的字段映射，处理可能的空值
            std_ipa_raw = str(row_dict.get(FIELD_MAPPING["standard_pron"], "")).strip()
            simple_ipa_raw = str(row_dict.get(FIELD_MAPPING["simple_pron"], "")).strip()
            
            # 清理IPA字符串
            std_ipa = clean_ipa_str(std_ipa_raw)
            simple_ipa = clean_ipa_str(simple_ipa_raw)

            # 标准IPA索引构建（排除空值和"nan"）
            if std_ipa and std_ipa != "nan" and std_ipa != "":
                if std_ipa not in self.standard_ipa_index:
                    self.standard_ipa_index[std_ipa] = []
                self.standard_ipa_index[std_ipa].append(row_dict)
                self.all_ipa_list.append(std_ipa)
                std_count += 1

                std_ipa_tone_free = self._strip_tone_digits(std_ipa)
                if std_ipa_tone_free not in self.tone_free_standard_ipa_index:
                    self.tone_free_standard_ipa_index[std_ipa_tone_free] = []
                self.tone_free_standard_ipa_index[std_ipa_tone_free].append(row_dict)
                self.all_tone_free_ipa_list.append(std_ipa_tone_free)

            # 简易发音索引构建（排除空值和"nan"）
            if simple_ipa and simple_ipa != "nan" and simple_ipa != "":
                if simple_ipa not in self.simple_ipa_index:
                    self.simple_ipa_index[simple_ipa] = []
                self.simple_ipa_index[simple_ipa].append(row_dict)
                self.all_ipa_list.append(simple_ipa)
                simple_count += 1

                simple_ipa_tone_free = self._strip_tone_digits(simple_ipa)
                if simple_ipa_tone_free not in self.tone_free_simple_ipa_index:
                    self.tone_free_simple_ipa_index[simple_ipa_tone_free] = []
                self.tone_free_simple_ipa_index[simple_ipa_tone_free].append(row_dict)
                self.all_tone_free_ipa_list.append(simple_ipa_tone_free)
        
        if self.debug:
            print(f"索引构建完成：标准IPA {std_count}条，简易发音 {simple_count}条")
            print(f"总IPA条目数：{len(self.all_ipa_list)}")

    # ============================================================
    # 第一层：精准完全匹配
    # ============================================================
    def _precise_match(self, clean_input: str) -> List[Dict]:
        if self.debug:
            print(f"[精准匹配] 输入: {clean_input}")
        
        results = []
        # 优先简易发音精准命中
        if clean_input in self.simple_ipa_index:
            if self.debug:
                print(f"[精准匹配] 命中简易发音索引")
            for item in self.simple_ipa_index[clean_input]:
                cp = item.copy()
                cp["相似度"] = 1.0
                cp["匹配类型"] = "精准匹配-简易发音"
                results.append(cp)
        # 其次标准IPA精准命中
        if clean_input in self.standard_ipa_index:
            if self.debug:
                print(f"[精准匹配] 命中标准IPA索引")
            for item in self.standard_ipa_index[clean_input]:
                cp = item.copy()
                cp["相似度"] = 1.0
                cp["匹配类型"] = "精准匹配-标准IPA"
                results.append(cp)

        tone_free_input = self._strip_tone_digits(clean_input)
        if tone_free_input != clean_input:
            if tone_free_input in self.tone_free_simple_ipa_index:
                if self.debug:
                    print(f"[精准匹配] 命中去声调简易发音索引")
                for item in self.tone_free_simple_ipa_index[tone_free_input]:
                    cp = item.copy()
                    cp["相似度"] = 1.0
                    cp["匹配类型"] = "精准匹配-简易发音(去声调)"
                    results.append(cp)
            if tone_free_input in self.tone_free_standard_ipa_index:
                if self.debug:
                    print(f"[精准匹配] 命中去声调标准IPA索引")
                for item in self.tone_free_standard_ipa_index[tone_free_input]:
                    cp = item.copy()
                    cp["相似度"] = 1.0
                    cp["匹配类型"] = "精准匹配-标准IPA(去声调)"
                    results.append(cp)

        # 词条去重
        seen_word = set()
        unique_res = []
        for it in results:
            word = it[FIELD_MAPPING["dialect_word"]]
            if word not in seen_word:
                seen_word.add(word)
                unique_res.append(it)
        
        if self.debug:
            print(f"[精准匹配] 结果: {len(unique_res)}条")
        return unique_res

    # ============================================================
    # 第二层：规则模糊匹配（修复版）
    # ============================================================
    def _generate_fuzzy_candidates(self, clean_input: str) -> List[str]:
        """
        优雅的模糊候选生成 - 融合创新与安全
        
        设计特点：
        1. 分层处理：字符级→多字符→声调→类化
        2. 安全约束：避免过度泛化，限制候选数量
        3. 智能应用：仅在合适场景应用高级规则
        """
        candidates = {clean_input}
        has_glottal = "ʔ" in clean_input
        
        # 安全约束：限制候选生成数量
        max_candidates = SAFETY_CONSTRAINTS["max_candidate_generation"]

        # 1. 基础字符级混淆替换
        candidates = self._apply_char_level_confusion(candidates, has_glottal)
        
        # 2. 多字符韵母替换（您的创新）
        candidates = self._apply_multi_char_replacement(candidates)
        
        # 3. 声调兼容处理
        candidates = self._apply_tone_compatibility(candidates, has_glottal)
        
        # 4. 语音识别误差处理（我的补充）
        candidates = self._apply_asr_error_handling(candidates)
        
        # 5. 安全过滤：限制候选数量
        candidates = list(candidates)[:max_candidates]
        
        return candidates
    
    def _apply_char_level_confusion(self, candidates: set, has_glottal: bool) -> set:
        """应用字符级混淆替换（安全约束版）"""
        result = set(candidates)
        
        for cand in list(candidates):
            for idx, char in enumerate(cand):
                # 优先使用CONFUSION_MAP
                if char in CONFUSION_MAP:
                    for rep in CONFUSION_MAP[char]:
                        new_cand = cand[:idx] + rep + cand[idx+1:]
                        # 安全约束：ʔ必须保留
                        if has_glottal and "ʔ" not in new_cand:
                            continue
                        result.add(new_cand)
        
        return result
    
    def _apply_multi_char_replacement(self, candidates: set) -> set:
        """应用多字符替换（您的创新）"""
        result = set(candidates)
        
        for cand in list(candidates):
            # 查找多字符韵母进行替换
            for pattern, replacements in CONFUSION_MAP.items():
                if len(pattern) > 1 and pattern in cand:
                    for rep in replacements:
                        new_cand = cand.replace(pattern, rep)
                        result.add(new_cand)
        
        return result
    
    def _apply_tone_compatibility(self, candidates: set, has_glottal: bool) -> set:
        """应用声调兼容处理"""
        result = set(candidates)
        syl_re = re.compile(r"([a-zɒɔøŋɬʔβ]+)([0-9]+)?")
        
        for cand in list(candidates):
            parts = syl_re.findall(cand)
            if not parts:
                continue
                
            combs = [[]]
            for base, tone in parts:
                # 使用扩展的TONE_MAP
                tone_list = TONE_MAP.get(tone, [tone]) if tone else [""]
                new_comb = []
                for pre in combs:
                    for t in tone_list:
                        new_comb.append(pre + [(base, t)])
                combs = new_comb
                
            for cb in combs:
                new_s = "".join(b + t for b, t in cb)
                # 安全约束：ʔ必须保留
                if has_glottal and "ʔ" not in new_s:
                    continue
                result.add(new_s)
        
        return result
    
    def _apply_asr_error_handling(self, candidates: set) -> set:
        """应用语音识别误差处理（我的补充）"""
        result = set(candidates)
        
        for cand in list(candidates):
            for idx, char in enumerate(cand):
                if char in ASR_ERROR_MAP:
                    for rep in ASR_ERROR_MAP[char]:
                        new_cand = cand[:idx] + rep + cand[idx+1:]
                        result.add(new_cand)
        
        return result

    def _rule_fuzzy_match(self, clean_input: str) -> List[Dict]:
        if not self.enable_rule_fuzzy:
            return []

        if self.debug:
            print(f"[规则模糊匹配] 输入: {clean_input}")
        
        candidates = self._generate_fuzzy_candidates(clean_input)
        tone_free_input = self._strip_tone_digits(clean_input)
        use_tone_free = tone_free_input == clean_input
        results = []
        for cand in candidates:
            if cand in self.simple_ipa_index:
                for it in self.simple_ipa_index[cand]:
                    cp = it.copy()
                    cp["相似度"] = 0.95
                    cp["匹配类型"] = "规则容错匹配"
                    cp["修正后IPA"] = cand
                    results.append(cp)
            if cand in self.standard_ipa_index:
                for it in self.standard_ipa_index[cand]:
                    cp = it.copy()
                    cp["相似度"] = 0.95
                    cp["匹配类型"] = "规则容错匹配"
                    cp["修正后IPA"] = cand
                    results.append(cp)

            if use_tone_free:
                cand_tone_free = self._strip_tone_digits(cand)
                if cand_tone_free in self.tone_free_simple_ipa_index:
                    for it in self.tone_free_simple_ipa_index[cand_tone_free]:
                        cp = it.copy()
                        cp["相似度"] = 0.95
                        cp["匹配类型"] = "规则容错匹配(去声调)"
                        cp["修正后IPA"] = cand_tone_free
                        results.append(cp)
                if cand_tone_free in self.tone_free_standard_ipa_index:
                    for it in self.tone_free_standard_ipa_index[cand_tone_free]:
                        cp = it.copy()
                        cp["相似度"] = 0.95
                        cp["匹配类型"] = "规则容错匹配(去声调)"
                        cp["修正后IPA"] = cand_tone_free
                        results.append(cp)

        # 词条去重
        seen = set()
        out = []
        for it in results:
            w = it[FIELD_MAPPING["dialect_word"]]
            if w not in seen:
                seen.add(w)
                out.append(it)
        
        if self.debug:
            print(f"[规则模糊匹配] 结果: {len(out)}条")
        return out[:3]

    # ===========================================================
    # 第三层核心：IPA三段加权拆分算法
    # ===========================================================
    def split_ipa(self, ipa: str):
        """
        莆仙IPA三段精准拆分函数
        修复问题：确保拆分逻辑正确
        """
        suffix = ""
        body = ipa
        # 截取入声尾段 ʔ+尾调
        glot_idx = body.find("ʔ")
        if glot_idx != -1:
            suffix = body[glot_idx:]
            body = body[:glot_idx]

        # 逆向查找最后一位声调数字，划分主前缀与中间弱音节
        last_digit_idx = -1
        for i in reversed(range(len(body))):
            if body[i].isdigit():
                last_digit_idx = i
                break

        if last_digit_idx != -1:
            prefix = body[:last_digit_idx + 1]
            middle = body[last_digit_idx + 1:]
        else:
            prefix = body
            middle = ""
        return prefix.strip(), middle.strip(), suffix.strip()

    def segment_sim(self, a: str, b: str) -> float:
        """单片段相似度计算，沿用原生Levenshtein编辑距离"""
        if a == b:
            return 1.0
        if not a or not b:
            return 0.0
        dist = Levenshtein.distance(a, b)
        return 1.0 - dist / max(len(a), len(b))

    def weighted_score_calc(self, query_ipa: str, db_ipa: str) -> float:
        """
        
        设计特点：
        1. 智能权重分配：根据混淆类型动态调整
        2. 安全约束：避免过度匹配
        3. 多维度评估：字符、声调、类化等
        """
        # 安全约束：ʔ必须匹配
        if "ʔ" in query_ipa and "ʔ" not in db_ipa:
            return 0.0

        # 分段处理
        q_pre, q_mid, q_suf = self.split_ipa(query_ipa)
        d_pre, d_mid, d_suf = self.split_ipa(db_ipa)

        # 智能权重分配
        pre_sim = self._smart_segment_sim(q_pre, d_pre, "prefix")
        mid_sim = self._smart_segment_sim(q_mid, d_mid, "middle") 
        suf_sim = self._smart_segment_sim(q_suf, d_suf, "suffix")

        # 动态权重调整
        weights = self._dynamic_weight_adjustment(q_pre, d_pre, q_suf, d_suf)
        total_score = pre_sim * weights[0] + mid_sim * weights[1] + suf_sim * weights[2]

        # 特殊规则：残缺输入高分召回
        if q_pre == d_pre and q_suf == d_suf:
            total_score = max(total_score, 0.90)

        # 应用连读调变加权
        total_score = self._apply_sandhi_weight(query_ipa, db_ipa, total_score)

        return round(total_score, 3)
    
    def _smart_segment_sim(self, query: str, target: str, segment_type: str) -> float:
        """智能片段相似度计算"""
        if query == target:
            return MATCH_WEIGHTS["exact_match"]
        if not query or not target:
            return 0.0

        # 基础编辑距离
        base_sim = 1.0 - Levenshtein.distance(query, target) / max(len(query), len(target))
        
        # 混淆关系检测
        confusion_factor = self._detect_confusion_relation(query, target)
        
        # 智能权重融合
        if confusion_factor > 0.8:
            # 高混淆关系，降低编辑距离权重
            score = base_sim * 0.4 + confusion_factor * 0.6
        else:
            # 低混淆关系，保持编辑距离主导
            score = base_sim * 0.7 + confusion_factor * 0.3
            
        return score
    
    def _detect_confusion_relation(self, query: str, target: str) -> float:
        """检测混淆关系（多维度评估）"""
        if query == target:
            return 1.0

        confusion_score = 0.0
        max_len = max(len(query), len(target))
        
        for i in range(min(len(query), len(target))):
            q_char = query[i]
            t_char = target[i]
            
            # 检查CONFUSION_MAP
            if q_char in CONFUSION_MAP and t_char in CONFUSION_MAP[q_char]:
                confusion_score += MATCH_WEIGHTS["consonant_confusion"]
            elif t_char in CONFUSION_MAP and q_char in CONFUSION_MAP[t_char]:
                confusion_score += MATCH_WEIGHTS["consonant_confusion"]
            
            # 检查ASR_ERROR_MAP
            elif q_char in ASR_ERROR_MAP and t_char in ASR_ERROR_MAP[q_char]:
                confusion_score += MATCH_WEIGHTS["asr_error"]
            elif t_char in ASR_ERROR_MAP and q_char in ASR_ERROR_MAP[t_char]:
                confusion_score += MATCH_WEIGHTS["asr_error"]
            
            # 检查多字符匹配
            elif self._check_multi_char_match(query, target, i):
                confusion_score += MATCH_WEIGHTS["vowel_confusion"]
            
            elif q_char == t_char:
                confusion_score += 1.0
        
        return confusion_score / max_len if max_len > 0 else 0.0
    
    def _check_multi_char_match(self, query: str, target: str, start_idx: int) -> bool:
        """检查多字符匹配"""
        # 检查是否存在多字符韵母匹配
        for pattern in CONFUSION_MAP:
            if len(pattern) > 1:
                if query.startswith(pattern, start_idx) and target.startswith(pattern, start_idx):
                    return True
                # 检查混淆关系
                for rep in CONFUSION_MAP[pattern]:
                    if (query.startswith(pattern, start_idx) and target.startswith(rep, start_idx)) or \
                       (query.startswith(rep, start_idx) and target.startswith(pattern, start_idx)):
                        return True
        return False
    
    def _dynamic_weight_adjustment(self, q_pre: str, d_pre: str, q_suf: str, d_suf: str) -> tuple:
        """动态权重调整"""
        # 基础权重
        base_weights = (0.6, 0.1, 0.3)
        
        # 如果前缀匹配度高，适当增加前缀权重
        if q_pre and d_pre and self._smart_segment_sim(q_pre, d_pre, "prefix") > 0.8:
            return (0.7, 0.05, 0.25)
        
        # 如果后缀匹配度高，适当增加后缀权重
        if q_suf and d_suf and self._smart_segment_sim(q_suf, d_suf, "suffix") > 0.8:
            return (0.5, 0.1, 0.4)
        
        return base_weights
    
    def _apply_sandhi_weight(self, query_ipa: str, db_ipa: str, score: float) -> float:
        """应用连读调变加权"""
        for original_tone, sandhi_map in SANDHI_RULES.items():
            if original_tone in query_ipa:
                for target_tone, change_to in sandhi_map.items():
                    if target_tone in db_ipa or change_to in db_ipa:
                        score *= MATCH_WEIGHTS["sandhi_rule"]
                        break
        return score

    def _edit_distance_match(self, clean_input: str) -> List[Dict]:
        if not self.enable_edit_fuzzy:
            return []

        if self.debug:
            print(f"[编辑距离匹配] 输入: {clean_input}")
        
        in_len = len(clean_input)
        tone_free_input = self._strip_tone_digits(clean_input)
        use_tone_free = tone_free_input == clean_input
        # 适配残缺插入字符场景，放宽距离上限
        max_dis = 3 if in_len <= 8 else 4
        match_list = []

        search_pool = self.all_tone_free_ipa_list if use_tone_free else self.all_ipa_list
        compare_input = tone_free_input if use_tone_free else clean_input

        for ipa in set(search_pool):
            # 原生编辑距离仅用于大范围无关结果过滤
            dis = Levenshtein.distance(compare_input, ipa)
            if dis > max_dis:
                continue

            # 统一使用分段加权分数作为唯一最终评分
            score = self.weighted_score_calc(compare_input, ipa)
            if score < 0.45:
                continue

            match_list.append((ipa, score))

        # 按相似度降序排序
        match_list.sort(key=lambda x: -x[1])
        results = []
        for ipa, sim in match_list[:3]:
            if use_tone_free and ipa in self.tone_free_simple_ipa_index:
                for it in self.tone_free_simple_ipa_index[ipa]:
                    cp = it.copy()
                    cp["相似度"] = sim
                    cp["匹配类型"] = "分段加权兜底匹配(去声调)"
                    results.append(cp)
            if use_tone_free and ipa in self.tone_free_standard_ipa_index:
                for it in self.tone_free_standard_ipa_index[ipa]:
                    cp = it.copy()
                    cp["相似度"] = sim
                    cp["匹配类型"] = "分段加权兜底匹配(去声调)"
                    results.append(cp)
            if ipa in self.simple_ipa_index:
                for it in self.simple_ipa_index[ipa]:
                    cp = it.copy()
                    cp["相似度"] = sim
                    cp["匹配类型"] = "分段加权兜底匹配"
                    results.append(cp)
            if ipa in self.standard_ipa_index:
                for it in self.standard_ipa_index[ipa]:
                    cp = it.copy()
                    cp["相似度"] = sim
                    cp["匹配类型"] = "分段加权兜底匹配"
                    results.append(cp)

        # 词条去重
        seen = set()
        unique = []
        for it in results:
            w = it[FIELD_MAPPING["dialect_word"]]
            if w not in seen:
                seen.add(w)
                unique.append(it)
        
        if self.debug:
            print(f"[编辑距离匹配] 结果: {len(unique)}条")
        return unique[:3]

    # ============================================================
    # 对外统一调用入口（融合模式）
    # 收集所有层的结果，去重排序后返回指定数量
    # ============================================================
    def match(self, query: str, top_k: int = 5):
        clean_q = clean_ipa_str(query)
        if not clean_q:
            return []

        if self.debug:
            print(f"\n=== IPA匹配开始 ===")
            print(f"原始输入: {query}")
            print(f"清理后: {clean_q}")

        # 收集所有匹配结果
        all_results = []

        # 第一层：精准匹配（权重最高）
        precise_res = self._precise_match(clean_q)
        if self.debug:
            print(f"[匹配] 精准匹配: {len(precise_res)}条")
        for r in precise_res:
            r['匹配类型'] = '精准匹配'
            r['匹配权重'] = 1.0
            all_results.append(r)

        # 第二层：规则模糊匹配
        fuzzy_res = self._rule_fuzzy_match(clean_q)
        if self.debug:
            print(f"[匹配] 规则模糊匹配: {len(fuzzy_res)}条")
        for r in fuzzy_res:
            if r['方言词'] not in [x['方言词'] for x in all_results]:
                r['匹配类型'] = '规则模糊'
                r['匹配权重'] = 0.9
                all_results.append(r)

        # 第三层：编辑距离匹配
        edit_res = self._edit_distance_match(clean_q)
        if self.debug:
            print(f"[匹配] 编辑距离匹配: {len(edit_res)}条")
        for r in edit_res:
            if r['方言词'] not in [x['方言词'] for x in all_results]:
                r['匹配类型'] = '编辑距离'
                r['匹配权重'] = 0.7
                all_results.append(r)

        # 按相似度和权重排序
        all_results.sort(key=lambda x: (x.get('匹配权重', 0), x.get('相似度', 0)), reverse=True)

        if self.debug:
            print(f"[结果] 合并去重后: {len(all_results)}条")

        return all_results[:top_k]