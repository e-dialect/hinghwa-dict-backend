"""拼音处理核心模块

功能：
1. 拼音切分（支持带声调/不带声调，有空格/无空格）
2. 莆仙话拼音 → IPA 映射
3. 普通话拼音 → IPA 映射
4. 候选生成与组合
5. pinyin_search 入口
"""
import re
from typing import List, Dict, Tuple, Optional
from itertools import product
# 将映射与规则从独立模块导入，以实现解耦
from .pinyin_mappings import (
    PUTIAN_INITIALS, INITIAL_SANDHI, PUTIAN_FINALS,
    ACCENT_VARIANTS, ACCENT_IPA_MAP,
    MANDARIN_TO_PUTIAN_INITIALS, MANDARIN_TO_PUTIAN_FINALS,
    MANDARIN_PRONUNCIATION_MAP, TONE_MAP
)

BASE_SYLLABLE_WEIGHT = 1.0
ACCENT_IPA_WEIGHT = 0.85
ACCENT_VARIANT_WEIGHT = 0.7


# ============================================================
# 拼音切分与解析工具
# ============================================================

def split_putian_syllable(syl: str) -> Tuple[str, str]:
    """拆分莆仙拼音音节为声母和韵母"""
    if len(syl) >= 2 and syl[:2] in ['bb', 'dd', 'gg', 'zz', 'ng']:
        return syl[:2], syl[2:]
    if syl and syl[0] in 'bpmfdtnlgkhjqxzcszhchshryw':
        return syl[0], syl[1:]
    return '', syl


def split_mandarin_syllable(syl: str) -> Tuple[str, str]:
    """拆分普通话音节为声母和韵母"""
    if len(syl) >= 2 and syl[:2] in ['zh', 'ch', 'sh']:
        return syl[:2], syl[2:]
    if syl.startswith('yi'):
        return '', 'i'
    if syl.startswith('wu'):
        return '', 'u'
    if syl.startswith('yu'):
        return '', 'ü'
    if syl and syl[0] in 'bpmfdtnlgkhjqxzcszhchshryw':
        return syl[0], syl[1:]
    return '', syl


def parse_pinyin(pinyin_str: str) -> List[Dict]:
    """
    解析拼音字符串，返回音节列表
    每个音节格式：{'initial': str, 'final': str, 'tone': str}
    支持：带空格/无空格，带声调数字/不带声调
    """
    pinyin_str = pinyin_str.lower().strip()
    if not pinyin_str:
        return []
    parts = pinyin_str.split()
    if not parts:
        parts = [pinyin_str]

    initials = ['zh','ch','sh','bb','dd','gg','zz','ng',
                'b','p','m','f','d','t','n','l',
                'g','k','h','j','q','x','z','c','s','r','w','y']
    finals = list(PUTIAN_FINALS.keys()) + list(MANDARIN_TO_PUTIAN_FINALS.keys())
    finals = sorted(set(finals), key=len, reverse=True)

    syllables = []
    for part in parts:
        i = 0
        while i < len(part):
            matched = False
            # 匹配声母（优先长声母）
            for init in sorted(initials, key=len, reverse=True):
                if part[i:].startswith(init):
                    remaining = part[i+len(init):]
                    for final in finals:
                        flen = len(final)
                        if len(remaining) >= flen:
                            candidate = remaining[:flen]
                            tone = ''
                            if len(remaining) > flen and remaining[flen].isdigit():
                                tone = remaining[flen]
                                candidate = remaining[:flen]
                            if candidate == final:
                                syllables.append({
                                    'initial': init,
                                    'final': final,
                                    'tone': tone,
                                    'source': 'unknown'
                                })
                                i += len(init) + len(candidate) + (1 if tone else 0)
                                matched = True
                                break
                    if matched:
                        break
            if not matched:
                # 尝试直接匹配韵母（零声母）
                for final in finals:
                    flen = len(final)
                    if len(part)-i >= flen:
                        candidate = part[i:i+flen]
                        tone = ''
                        if i+flen < len(part) and part[i+flen].isdigit():
                            tone = part[i+flen]
                        if candidate == final:
                            syllables.append({
                                'initial': '',
                                'final': final,
                                'tone': tone,
                                'source': 'unknown'
                            })
                            i += len(candidate) + (1 if tone else 0)
                            matched = True
                            break
                if not matched:
                    # 未知字符，跳过
                    i += 1
    return syllables


def _dedupe_weighted_candidates(candidates: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    unique = {}
    for ipa, weight in candidates:
        if ipa not in unique or weight > unique[ipa]:
            unique[ipa] = weight
    return list(unique.items())


def _is_accent_variant(base_candidates: List[str], candidate: str) -> bool:
    return candidate not in base_candidates



def putian_syllable_to_ipa(syl: str, tone: Optional[str] = None) -> List[str]:
    """莆仙拼音音节转 IPA（不带声调数字），包含口音变体"""
    initial, final = split_putian_syllable(syl)
    ipa_init = PUTIAN_INITIALS.get(initial, '')
    ipa_finals = PUTIAN_FINALS.get(final, [final])
    candidates = []
    for ipa_final in ipa_finals:
        if ipa_init:
            candidates.append(ipa_init + ipa_final)
        else:
            candidates.append(ipa_final)

    # 添加口音变体：先用 ACCENT_IPA_MAP 的精确替换规则
    accent_candidates = []
    for cand in candidates:
        # 基于 ACCENT_IPA_MAP 的替换（原有规则）
        for accent, rules in ACCENT_IPA_MAP.items():
            new_cand = cand
            for orig, repl in rules:
                new_cand = new_cand.replace(orig, repl)
            if new_cand != cand:
                accent_candidates.append(new_cand)

        # 基于 ACCENT_VARIANTS 的变体扩展（替换单个片段为多个候选）
        for accent, var_map in ACCENT_VARIANTS.items():
            for orig, repl_list in var_map.items():
                for repl in repl_list:
                    new_cand = cand.replace(orig, repl)
                    if new_cand != cand:
                        accent_candidates.append(new_cand)

    # 合并候选并去重
    candidates.extend(accent_candidates)
    return list(set(candidates))


def putian_syllable_to_ipa_weighted(syl: str, tone: Optional[str] = None) -> List[Tuple[str, float]]:
    """返回莆仙音节 IPA 候选及权重，口音变体降权。"""
    initial, final = split_putian_syllable(syl)
    ipa_init = PUTIAN_INITIALS.get(initial, '')
    ipa_finals = PUTIAN_FINALS.get(final, [final])

    base_candidates = []
    for ipa_final in ipa_finals:
        if ipa_init:
            base_candidates.append(ipa_init + ipa_final)
        else:
            base_candidates.append(ipa_final)

    weighted = [(cand, BASE_SYLLABLE_WEIGHT) for cand in base_candidates]

    accent_candidates = []
    for cand in base_candidates:
        for accent, rules in ACCENT_IPA_MAP.items():
            new_cand = cand
            for orig, repl in rules:
                new_cand = new_cand.replace(orig, repl)
            if new_cand != cand and _is_accent_variant(base_candidates, new_cand):
                accent_candidates.append((new_cand, ACCENT_IPA_WEIGHT))

        for accent, var_map in ACCENT_VARIANTS.items():
            for orig, repl_list in var_map.items():
                for repl in repl_list:
                    new_cand = cand.replace(orig, repl)
                    if new_cand != cand and _is_accent_variant(base_candidates, new_cand):
                        accent_candidates.append((new_cand, ACCENT_VARIANT_WEIGHT))

    return _dedupe_weighted_candidates(weighted + accent_candidates)

def putian_pinyin_to_ipa_candidates(pinyin_str: str) -> List[Tuple[str, float]]:
    """莆仙拼音字符串 → IPA候选列表（带声调数字，权重1.0）"""
    syllables = parse_pinyin(pinyin_str)
    if not syllables:
        return []
    candidates_per_syl = []
    for syl in syllables:
        ipa_segs = putian_syllable_to_ipa_weighted(syl['initial'] + syl['final'], syl['tone'])
        tone = syl['tone']
        if tone:
            tone_cands = TONE_MAP.get(tone, [tone])
        else:
            tone_cands = ['']
        segs = []
        for seg, seg_weight in ipa_segs:
            for tc in tone_cands:
                ipa_with_tone = seg + tc
                segs.append((ipa_with_tone, seg_weight))
        candidates_per_syl.append(segs)
    # 笛卡尔积
    results = []
    for combo in product(*candidates_per_syl):
        ipa_full = ''.join(c[0] for c in combo)
        weight = sum(c[1] for c in combo) / len(combo)
        results.append((ipa_full, weight))
    results = list(set(results))
    results.sort(key=lambda x: -x[1])
    return results[:30]

# ============================================================
# 五、普通话拼音 → IPA 候选（优化版，权重 0.8，考虑口音）
# ============================================================

def mandarin_syllable_to_ipa(syl: str) -> List[str]:
    """普通话发音描述转莆仙话IPA，包含口音变体"""
    initial, final = split_mandarin_syllable(syl)

    # 获取莆仙话声母候选
    putian_initials = MANDARIN_TO_PUTIAN_INITIALS.get(initial, [''])

    # 获取莆仙话韵母候选
    putian_finals = MANDARIN_TO_PUTIAN_FINALS.get(final, [final])

    # 组合声母和韵母
    candidates = []
    for ipa_init in putian_initials:
        for ipa_final in putian_finals:
            if ipa_init:
                candidates.append(ipa_init + ipa_final)
            else:
                candidates.append(ipa_final)

    # 添加口音变体：使用 ACCENT_IPA_MAP 和 ACCENT_VARIANTS 两类规则
    accent_candidates = []
    for cand in candidates:
        for accent, rules in ACCENT_IPA_MAP.items():
            new_cand = cand
            for orig, repl in rules:
                new_cand = new_cand.replace(orig, repl)
            if new_cand != cand:
                accent_candidates.append(new_cand)

        for accent, var_map in ACCENT_VARIANTS.items():
            for orig, repl_list in var_map.items():
                for repl in repl_list:
                    new_cand = cand.replace(orig, repl)
                    if new_cand != cand:
                        accent_candidates.append(new_cand)

    candidates.extend(accent_candidates)

    # 去重，保留合理数量的候选
    candidates = list(set(candidates))[:3]
    return candidates


def mandarin_syllable_to_ipa_weighted(syl: str) -> List[Tuple[str, float]]:
    """返回普通话音节对应的 IPA 候选及权重，口音变体降权。"""
    initial, final = split_mandarin_syllable(syl)
    putian_initials = MANDARIN_TO_PUTIAN_INITIALS.get(initial, [''])
    putian_finals = MANDARIN_TO_PUTIAN_FINALS.get(final, [final])

    base_candidates = []
    for ipa_init in putian_initials:
        for ipa_final in putian_finals:
            if ipa_init:
                base_candidates.append(ipa_init + ipa_final)
            else:
                base_candidates.append(ipa_final)

    weighted = [(cand, 0.8) for cand in base_candidates]

    accent_candidates = []
    for cand in base_candidates:
        for accent, rules in ACCENT_IPA_MAP.items():
            new_cand = cand
            for orig, repl in rules:
                new_cand = new_cand.replace(orig, repl)
            if new_cand != cand and _is_accent_variant(base_candidates, new_cand):
                accent_candidates.append((new_cand, ACCENT_IPA_WEIGHT))

        for accent, var_map in ACCENT_VARIANTS.items():
            for orig, repl_list in var_map.items():
                for repl in repl_list:
                    new_cand = cand.replace(orig, repl)
                    if new_cand != cand and _is_accent_variant(base_candidates, new_cand):
                        accent_candidates.append((new_cand, ACCENT_VARIANT_WEIGHT))

    return _dedupe_weighted_candidates(weighted + accent_candidates)

def mandarin_pinyin_to_ipa_candidates(pinyin_str: str) -> List[Tuple[str, float]]:
    """普通话发音描述 → 莆仙话IPA候选（权重0.8）"""
    pinyin_str = pinyin_str.lower().strip()

    # 优先检查发音映射
    norm = pinyin_str.replace(" ", "")
    if norm in MANDARIN_PRONUNCIATION_MAP:
        mappings = MANDARIN_PRONUNCIATION_MAP[norm]
        results = []
        for mapping in mappings:
            candidates = putian_pinyin_to_ipa_candidates(mapping)
            results.extend([(ipa, 0.85) for ipa, _ in candidates])
        return results[:30] if results else []

    syllables = parse_pinyin(pinyin_str)
    if not syllables:
        return []

    candidates_per_syl = []
    for syl in syllables:
        ipa_segs = mandarin_syllable_to_ipa_weighted(syl['initial'] + syl['final'])
        # 普通话查询不强制加声调（用户可能不知道方言声调）
        segs = [(seg, weight) for seg, weight in ipa_segs]
        if not segs:
            # 兜底：使用原始拼音片段
            segs = [(syl['initial'] + syl['final'], 0.3)]
        candidates_per_syl.append(segs)

    results = []
    for combo in product(*candidates_per_syl):
        ipa_full = ''.join(c[0] for c in combo)
        weight = sum(c[1] for c in combo) / len(combo)
        results.append((ipa_full, weight))

    results = list(set(results))
    results.sort(key=lambda x: -x[1])
    return results[:30]

# ============================================================
# 六、混合拼音输入（莆仙+普通话按音节混合）
# ============================================================

def mixed_pinyin_to_ipa_candidates(pinyin_str: str) -> List[Tuple[str, float]]:
    """按音节混合生成 IPA 候选：每个音节同时考虑莆仙和普通话映射，支持混合输入。
    返回列表形式为 (ipa_str, weight)。
    """
    syllables = parse_pinyin(pinyin_str)
    if not syllables:
        return []

    candidates_per_syl = []
    for syl in syllables:
        key = syl['initial'] + syl['final']
        tone = syl.get('tone', '')

        segs = []
        # 莆仙候选（权重 1.0）
        try:
            putian_segs = putian_syllable_to_ipa_weighted(key, tone)
        except Exception:
            putian_segs = []
        if putian_segs:
            tone_cands = TONE_MAP.get(tone, ['']) if tone else ['']
            for ps, ps_weight in set(putian_segs):
                for tc in tone_cands:
                    segs.append((ps + tc, ps_weight))

        # 普通话候选（权重 0.8）
        try:
            mandarin_segs = mandarin_syllable_to_ipa_weighted(key)
        except Exception:
            mandarin_segs = []
        for ms, ms_weight in set(mandarin_segs):
            segs.append((ms, ms_weight))

        # 兜底：使用原始拼音片段（低权重）
        if not segs:
            segs = [(key, 0.3)]

        candidates_per_syl.append(segs)

    # 笛卡尔积组合
    results = []
    for combo in product(*candidates_per_syl):
        ipa_full = ''.join([c[0] for c in combo])
        weight = sum(c[1] for c in combo) / len(combo)
        results.append((ipa_full, weight))

    # 去重并排序
    results = list({(r[0], r[1]) for r in results})
    results.sort(key=lambda x: -x[1])
    return results[:50]

# ============================================================
# 七、统一搜索入口
# ============================================================

def pinyin_search(query: str, ipa_matcher, top_k: int = 5) -> List[Dict]:
    """
    拼音查询主入口
    :param query: 拼音字符串，如 "a1 ma3" 或 "a ma"
    :param ipa_matcher: IPAMatcher 实例
    :param top_k: 返回结果数量
    """
    query = query.strip()
    if not query:
        return []
    # 优先使用混合候选（支持莆仙+普通话混合输入）
    mixed_candidates = mixed_pinyin_to_ipa_candidates(query)
    if mixed_candidates:
        all_candidates = mixed_candidates
    else:
        putian_candidates = putian_pinyin_to_ipa_candidates(query)
        mandarin_candidates = mandarin_pinyin_to_ipa_candidates(query)
        all_candidates = putian_candidates + mandarin_candidates

    # 去重
    seen = set()
    unique = []
    for ipa, w in all_candidates:
        if ipa not in seen:
            seen.add(ipa)
            unique.append((ipa, w))

    # 调用 IPA 匹配器
    all_results = []
    for ipa_str, weight in unique[:30]:
        matches = ipa_matcher.match(ipa_str, top_k=3)
        for m in matches:
            m['pinyin_weight'] = weight
            all_results.append(m)

    # 去重并排序
    from src.data_loader import FIELD_MAPPING
    unique_words = {}
    for r in all_results:
        word = r[FIELD_MAPPING["dialect_word"]]
        if word not in unique_words or r.get("相似度", 0) > unique_words[word].get("相似度", 0):
            unique_words[word] = r
    results = list(unique_words.values())
    results.sort(key=lambda x: x.get("相似度", 0) * 0.7 + x.get("pinyin_weight", 0) * 0.3, reverse=True)
    return results[:top_k]

# ============================================================
# 八、兼容旧接口（供 pinyin_matcher.py 使用）
# ============================================================

def generate_candidates(query: str) -> List[str]:
    """生成候选拼音串（用于简单发音索引）"""
    q = (query or '').lower().strip()
    if not q:
        return []
    q_nospace = q.replace(' ', '')
    q_nodigits = re.sub(r"\d", "", q_nospace)
    candidates = [q_nospace]
    if q_nodigits != q_nospace:
        candidates.append(q_nodigits)
    # 基于 parse_pinyin 重建
    try:
        syls = parse_pinyin(q)
        if syls:
            rebuilt = ''.join([s['initial'] + s['final'] for s in syls])
            if rebuilt and rebuilt not in candidates:
                candidates.append(rebuilt)
    except Exception:
        pass
    seen = set()
    out = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out

def pinyin_to_ipa(query: str) -> str:
    """将拼音串转换为单一 IPA（选择权重最高的候选）"""
    if not query:
        return ''
    mixed = mixed_pinyin_to_ipa_candidates(query)
    if mixed:
        return max(mixed, key=lambda x: x[1])[0]
    putian = putian_pinyin_to_ipa_candidates(query)
    mandarin = mandarin_pinyin_to_ipa_candidates(query)
    allc = putian + mandarin
    if not allc:
        return ''
    best = max(allc, key=lambda x: x[1])[0]
    return best

# ============================================================
# 测试代码（仅在本模块独立运行时执行）
# ============================================================
if __name__ == "__main__":
    print("=== 测试修正后的普通话发音描述映射 ===")

    # 测试1：声母映射
    print("\n1. 声母映射测试：")
    test_initials = ['f', 'd', 'zh', 'ch', 'sh', 'r', 'j', 'q', 'x']
    for initial in test_initials:
        putian = MANDARIN_TO_PUTIAN_INITIALS.get(initial, [])
        print(f"   普通话'{initial}' → 莆仙话{putian}")

    # 测试2：韵母映射
    print("\n2. 韵母映射测试：")
    test_finals = ['ou', 'iu', 'ie', 'an', 'en', 'in']
    for final in test_finals:
        putian = MANDARIN_TO_PUTIAN_FINALS.get(final, [])
        print(f"   普通话'{final}' → 莆仙话{putian}")

    # 测试3：常用词发音映射
    print("\n3. 常用词发音映射测试：")
    test_words = ['liu', 'yue', 'tian', 'dou', 'fu', 'liuyuetian', 'doufu', 'ajie']
    for word in test_words:
        mapping = MANDARIN_PRONUNCIATION_MAP.get(word, [])
        print(f"   普通话'{word}' → 莆仙话{mapping}")

    # 测试4：普通话拼音转IPA
    print("\n4. 普通话拼音转IPA测试：")
    test_queries = ['dou fu', 'liu yue tian', 'a jie', 'shui', 'ren']
    for query in test_queries:
        candidates = mandarin_pinyin_to_ipa_candidates(query)
        print(f"   '{query}' → {[c[0] for c in candidates[:3]]}")

    # 测试5：莆仙话拼音转IPA（确保原有功能不变）
    print("\n5. 莆仙话拼音转IPA测试（原有功能）：")
    test_putian = ['a1 ma3', 'ah6 sau1', 'lor2 ba5']
    for query in test_putian:
        candidates = putian_pinyin_to_ipa_candidates(query)
        print(f"   '{query}' → {[c[0] for c in candidates[:3]]}")

    # 测试6：混合拼音测试
    print("\n6. 混合拼音测试（莆仙话+普通话）：")
    test_mixed = ['a1 dou', 'liu lang', 'tiau fu']
    for query in test_mixed:
        candidates = mixed_pinyin_to_ipa_candidates(query)
        print(f"   '{query}' → {[c[0] for c in candidates[:3]]}")