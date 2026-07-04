from abc import ABC, abstractmethod
from typing import List, Union
import numpy as np

class BaseEncoder(ABC):
    """
    编码抽象基类：定义文本/IPA/拼音编码接口，适配BGE模型
    预留IPA/拼音编码扩展，当前仅实现文本编码（支撑精准匹配）
    """
    @abstractmethod
    def encode_text(self, texts: Union[str, List[str]]) -> np.ndarray:
        """文本编码（核心）：用于方言词条/查询的向量化"""
        pass

    @abstractmethod
    def encode_ipa(self, ipa_list: Union[str, List[str]]) -> np.ndarray:
        """预留：IPA编码接口（后续模糊IPA匹配用）"""
        pass

    @abstractmethod
    def encode_pinyin(self, pinyin_list: Union[str, List[str]]) -> np.ndarray:
        """预留：拼音编码接口（后续拼音匹配用）"""
        pass