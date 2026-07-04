"""拼音意图解析器

功能：从自然语言中准确提取核心词（拼音片段和方言汉字词）
支持混合输入，如“阿舅的发音是不是 a1 gu5”
输出结构供后续检索使用，并实现拼音+方言词组合匹配策略。
"""
import re
import json
import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional, Tuple
from itertools import product

load_dotenv()

# 拼音片段匹配模式（支持声调数字1-8，支持连字符和空格）
PINYIN_PATTERN = re.compile(
    r'[a-zA-Züv]+(?:[-\s]?[a-zA-Züv]+)*(?:[1-8])?',
    re.IGNORECASE
)

# 方言汉字词匹配模式
CHINESE_WORD_PATTERN = re.compile(r'[\u4e00-\u9fa5]+')


def normalize_pinyin_fragments(fragments: List[str]) -> List[str]:
    """
    归一化拼音片段：
    - 合并多个片段为一个字符串（空格分隔）
    - 连字符转空格
    - 去除多余空格
    - 统一小写
    """
    if not fragments:
        return []
    combined = ' '.join(fragments)
    combined = combined.replace('-', ' ')
    combined = re.sub(r'\s+', ' ', combined).strip()
    combined = combined.lower()
    return [combined]  # 返回单个字符串，便于后续拼音解析


def merge_dialect_words(words: List[str]) -> List[str]:
    """合并方言词：去重即可（LLM应已保证不拆散）"""
    if not words:
        return []
    # 简单去重，保留顺序
    seen = set()
    result = []
    for w in words:
        if w not in seen:
            seen.add(w)
            result.append(w)
    return result


def fallback_extract(query: str) -> Dict:
    """正则兜底：提取中文词和拼音片段（当LLM失败时使用）"""
    # 提取中文词
    chinese_words = CHINESE_WORD_PATTERN.findall(query)
    # 提取拼音片段（过滤掉过短的）
    pinyin_matches = PINYIN_PATTERN.findall(query.lower())
    pinyin_fragments = [p for p in pinyin_matches if len(p) >= 2 and not p.isdigit()]
    # 归一化
    normalized_pinyin = normalize_pinyin_fragments(pinyin_fragments) if pinyin_fragments else []
    return {
        "pinyin_fragments": normalized_pinyin,
        "dialect_words": merge_dialect_words(chinese_words),
        "query_type": "mixed" if chinese_words and normalized_pinyin else ("pinyin_only" if normalized_pinyin else "word_only")
    }


def call_llm_parser(user_query: str) -> Optional[Dict]:
    """调用LLM提取拼音片段和方言词"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

    if not api_key:
        return None

    url = f"{base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # 严格限制输出格式的Prompt
    prompt = f"""
你是一个方言查询解析助手。用户输入自然语言，可能包含：
- 方言汉字词（如“阿舅”、“郎罢”、“阿姨”）
- 拼音片段（可能是莆仙拼音或普通话拼音，可能带数字声调、空格、连字符，如 "a1 gu5", "lao ba", "ah6 sau1", "ba1-de3-eng1"）

请执行以下操作：
1. 提取所有**拼音片段**（连续字母，可包含数字1-8，可包含空格或连字符，但不要包含中文或标点）
2. 提取所有**方言汉字词**（连续中文字符，可能是单个字或多个字，不要拆散）
3. 判断用户主要意图类型：
   - "pinyin_only"：只有拼音片段，没有方言汉字
   - "word_only"：只有方言汉字，没有拼音
   - "mixed"：同时有拼音和方言汉字

输出严格为JSON，格式：
{{"pinyin_fragments": ["拼音1", "拼音2"], "dialect_words": ["词1", "词2"], "query_type": "类型"}}

如果没有拼音片段，pinyin_fragments 为空数组；如果没有方言汉字，dialect_words 为空数组。

**重要规则**：
- 拼音片段必须完整，不要拆分（如 "a1 gu5" 是一个片段，不要分成 "a1" 和 "gu5"）
- 方言汉字词必须完整，不要拆分（如 "阿姨" 是一个词，不要分成 "阿" 和 "姨"）
- 如果拼音片段中包含声调数字，保留数字
- 如果拼音片段中使用连字符（如 "ba1-de3-eng1"），保留连字符或转为空格都可，但建议保留原样

**示例**：
1. 输入：阿舅的发音是不是 a1 gu5
   输出：{{"pinyin_fragments": ["a1 gu5"], "dialect_words": ["阿舅"], "query_type": "mixed"}}

2. 输入：读音像 lao ba 的词
   输出：{{"pinyin_fragments": ["lao ba"], "dialect_words": [], "query_type": "pinyin_only"}}

3. 输入：莆仙话里“爸爸”怎么说
   输出：{{"pinyin_fragments": [], "dialect_words": ["爸爸"], "query_type": "word_only"}}

4. 输入：语义为阿姨发音为阿1i13的方言词是？
   输出：{{"pinyin_fragments": ["a1 i2"], "dialect_words": ["阿姨"], "query_type": "mixed"}}

5. 输入：请问郎罢是什么意思
   输出：{{"pinyin_fragments": [], "dialect_words": ["郎罢"], "query_type": "word_only"}}

6. 输入：擘地生的发音是 ba1 de3 eng1 吗
   输出：{{"pinyin_fragments": ["ba1 de3 eng1"], "dialect_words": ["擘地生"], "query_type": "mixed"}}

7. 输入：我想查一个词，听起来像 ah6 sau1，意思是调皮的人
   输出：{{"pinyin_fragments": ["ah6 sau1"], "dialect_words": [], "query_type": "pinyin_only"}}

现在处理用户输入：{user_query}
"""

    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 300
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=5)
        response.raise_for_status()
        result_text = response.json()["choices"][0]["message"]["content"].strip()
        # 提取JSON部分（防止LLM输出多余内容）
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        print(f"LLM解析出错：{e}")
        return None


def parse_pinyin_intent(user_query: str) -> Dict:
    """
    解析自然语言中的拼音意图，返回核心词

    返回格式：
    {
        "pinyin_fragments": ["a1 ma3"],   # 归一化后的拼音片段（单个字符串）
        "dialect_words": ["阿妈"],        # 方言汉字词列表
        "query_type": "mixed"             # pinyin_only / word_only / mixed
    }
    """
    # 1. 尝试LLM提取
    llm_result = call_llm_parser(user_query)
    if llm_result and "pinyin_fragments" in llm_result and "dialect_words" in llm_result:
        pinyin_fragments = llm_result.get("pinyin_fragments", [])
        dialect_words = llm_result.get("dialect_words", [])
        query_type = llm_result.get("query_type", "mixed")
        # 归一化拼音片段
        normalized = normalize_pinyin_fragments(pinyin_fragments)
    else:
        # 2. 降级：正则提取
        fallback = fallback_extract(user_query)
        normalized = fallback["pinyin_fragments"]
        dialect_words = fallback["dialect_words"]
        query_type = fallback["query_type"]

    return {
        "pinyin_fragments": normalized,
        "dialect_words": merge_dialect_words(dialect_words),
        "query_type": query_type
    }


def mix_pinyin_and_dialect_ranking(
    pinyin_results: List[Dict],
    dialect_words: List[str],
    semantic_similarity_func=None
) -> List[Dict]:
    """
    对拼音检索结果进行重排序，利用方言词约束提升准确率

    :param pinyin_results: pinyin_search 返回的候选列表
    :param dialect_words: 提取到的方言汉字词列表
    :param semantic_similarity_func: 可选，计算两个词语义相似度的函数，默认仅精确匹配
    :return: 重排后的候选列表
    """
    if not pinyin_results or not dialect_words:
        return pinyin_results

    for item in pinyin_results:
        word = item.get("方言词", "")
        # 精确匹配加分
        if any(w == word for w in dialect_words):
            item["bonus"] = 0.5
        # 可选：语义相似度匹配
        elif semantic_similarity_func:
            max_sim = 0
            for w in dialect_words:
                sim = semantic_similarity_func(word, w)
                if sim > max_sim:
                    max_sim = sim
            if max_sim > 0.8:
                item["bonus"] = 0.3
            else:
                item["bonus"] = 0
        else:
            item["bonus"] = 0
        # 计算最终得分（可根据需要调整权重）
        base_score = item.get("相似度", 0)
        pinyin_w = item.get("pinyin_weight", 0.5)
        item["final_score"] = base_score * 0.6 + item["bonus"] * 0.3 + pinyin_w * 0.1

    pinyin_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    return pinyin_results


# 便捷函数：直接获取核心词
def extract_core_words(user_query: str) -> Tuple[List[str], List[str], str]:
    """
    返回 (pinyin_list, dialect_words_list, query_type)
    """
    result = parse_pinyin_intent(user_query)
    return result["pinyin_fragments"], result["dialect_words"], result["query_type"]


if __name__ == "__main__":
    test_queries = [
        "阿舅的发音是不是 a1 gu5",
        "读音像 lao ba 的词",
        "莆仙话里“爸爸”怎么说",
        "语义为阿姨发音为阿1i13的方言词是？",
        "请问郎罢是什么意思",
        "擘地生的发音是 ba1 de3 eng1 吗",
        "我想查一个词，听起来像 ah6 sau1，意思是调皮的人",
        "普通话语义词"
    ]

    for q in test_queries:
        result = parse_pinyin_intent(q)
        print(f"输入: {q}")
        print(f"  拼音片段: {result['pinyin_fragments']}")
        print(f"  方言词: {result['dialect_words']}")
        print(f"  类型: {result['query_type']}")
        print()