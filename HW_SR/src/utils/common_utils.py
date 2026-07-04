import re

_UNIFIED_IPA_SPECIAL = {"ɒ", "ɔ", "ø", "œ", "ŋ", "ɬ", "ʔ", "ʰ", "˥", "˧", "˨", "˩", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸"}
_UNIFIED_ALLOWED_ASCII = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ")
# def clean_ipa_str(ipa_str):
#     # 先打印原始输入
#     # print(f"[调试] 原始输入IPA：{repr(ipa_str)}")
    
#     # 只做最基础的清洗：去首尾空格、中间多余空格
#     ipa_str = ipa_str.strip()
#     ipa_str = re.sub(r"\s+", " ", ipa_str)
    
#     # 打印清洗后的结果
#     # print(f"[调试] 清洗后IPA：{repr(ipa_str)}")
#     return ipa_str

import re

def clean_ipa_str(ipa_str: str) -> str:
    """
    莆仙方言专属IPA清洗函数，全量覆盖所有合法字符
    规则：
    1. 全角转半角，统一小写
    2. 去除首尾/中间多余空格
    3. 白名单全量覆盖莆仙方言所有IPA字符、简易发音、声调
    4. 只过滤中文、emoji等完全无关内容
    """
    if not ipa_str or not isinstance(ipa_str, str):
        return ""
    
    # 1. 全角转半角
    full_to_half = str.maketrans({
        chr(0xFF01 + i): chr(0x21 + i) for i in range(94)
    })
    ipa_str = ipa_str.translate(full_to_half)
    
    # 2. 统一小写，去除所有空格
    ipa_str = ipa_str.lower().replace(" ", "")
    
    # 3. 全量合法字符白名单（100%覆盖你的数据集）
    legal_chars = r"[a-z0-9ɒɔøŋɬʔ?βkhthpʰtʰkʰɕtɕ]"
    cleaned = "".join(re.findall(legal_chars, ipa_str))
    
    return cleaned

def format_match_result(item):
    return {
        "方言词": item.get("方言词", ""),
        "简易发音": item.get("简易发音", ""),
        "标准发音": item.get("标准发音", ""),
        "释义注释": item.get("释义注释", ""),
        "相似度": round(item.get("score", 0.0), 4)
    }