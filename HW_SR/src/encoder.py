# """
# 语义嵌入的作用，是把文本转化为向量，让计算机能够理解词语之间的语义相似性，
# 从而实现同义词匹配、普通话查方言、自然语言提问、描述性查询，
# """
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Union
from src.base.base_encoder import BaseEncoder
from src.utils.common_utils import clean_ipa_str

# ====================== 配置 ======================
# bge模型路径
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "bge-small-zh-v1.5")
VECTOR_DIM = 512  # bge-small固定512维
# 字段权重：释义权重最高
FIELD_WEIGHTS = {
    "definition": 0.6,    # 释义：核心权重，适配普通话查方言
    "dialect_word": 0.3,  # 方言词：辅助匹配
    "simple_pron": 0.05,  # 简易发音：轻微辅助
    "standard_pron": 0.05 # 标准发音：轻微辅助
}
# 字段映射
FIELD_MAPPING = {
    "dialect_word": "方言词",
    "simple_pron": "简易发音",
    "standard_pron": "标准发音",
    "definition": "释义注释"
}
# ===================================================

class BGEDialectEncoder(BaseEncoder):
    """BGE编码实现：文本为核心，IPA/拼音先统一归一后复用文本编码。"""

    def __init__(self, model_path: str = MODEL_PATH, vector_dim: int = VECTOR_DIM):
        self.model_path = model_path
        self.vector_dim = vector_dim
        self._model = None

    def load_embedding_model(self):
        """加载嵌入模型，仅加载一次。"""
        if self._model is None:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"bge模型不存在：{self.model_path}")
            print("加载bge嵌入模型...")
            self._model = SentenceTransformer(self.model_path)
        return self._model

    def _encode_one(self, text: str) -> np.ndarray:
        normalized = str(text).strip()
        if normalized == "" or normalized.lower() == "nan":
            return np.zeros(self.vector_dim, dtype=np.float32)

        model = self.load_embedding_model()
        vec = model.encode(normalized, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vec, dtype=np.float32)

    def encode_text(self, texts: Union[str, List[str]]) -> np.ndarray:
        """文本编码：str返回1维向量，List[str]返回2维向量。"""
        if isinstance(texts, str):
            return self._encode_one(texts)

        if not texts:
            return np.zeros((0, self.vector_dim), dtype=np.float32)

        vectors = [self._encode_one(text) for text in texts]
        return np.vstack(vectors)

    def encode_ipa(self, ipa_list: Union[str, List[str]]) -> np.ndarray:
        """IPA编码：先做IPA清洗，再复用文本编码。"""
        if isinstance(ipa_list, str):
            return self.encode_text(clean_ipa_str(ipa_list))

        cleaned_list = [clean_ipa_str(ipa) for ipa in ipa_list]
        return self.encode_text(cleaned_list)

    def encode_pinyin(self, pinyin_list: Union[str, List[str]]) -> np.ndarray:
        """拼音编码预留：先做基础归一化，再复用文本编码。"""
        if isinstance(pinyin_list, str):
            normalized = "".join(pinyin_list.lower().strip().split())
            return self.encode_text(normalized)

        normalized_list = ["".join(str(item).lower().strip().split()) for item in pinyin_list]
        return self.encode_text(normalized_list)


# 全局单例编码器（兼容原有函数式调用）
_encoder = BGEDialectEncoder()


def load_embedding_model():
    """兼容旧接口：加载嵌入模型，仅加载一次。"""
    return _encoder.load_embedding_model()


def encode_single_text(text: str) -> np.ndarray:
    """兼容旧接口：单文本生成归一化向量（空文本返回全0）。"""
    return _encoder.encode_text(text)


def encode_ipa(ipa_text: str) -> np.ndarray:
    """新增兼容接口：单IPA文本编码。"""
    return _encoder.encode_ipa(ipa_text)

def encode_entry(entry: Dict[str, str]) -> np.ndarray:
    """词条向量：按权重融合4个字段"""
    total_vec = np.zeros(VECTOR_DIM)
    for field_key, weight in FIELD_WEIGHTS.items():
        field_name = FIELD_MAPPING[field_key]
        field_text = entry.get(field_name, "")
        total_vec += encode_single_text(field_text) * weight
    # 归一化（保证余弦相似度准确）
    norm = np.linalg.norm(total_vec)
    return total_vec / norm if norm > 1e-6 else total_vec

def encode_query(query_text: str) -> np.ndarray:
    """查询向量：用户输入生成向量"""
    return _encoder.encode_text(query_text)

# 测试代码
if __name__ == "__main__":
    test_entry = {"方言词": "伓", "释义注释": "相当于普通话“不”"}
    vec = encode_entry(test_entry)
    print(f"向量维度：{vec.shape}，模长：{np.linalg.norm(vec):.3f}")  # 模长应为1
