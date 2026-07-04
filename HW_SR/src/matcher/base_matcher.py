from typing import List, Dict


class BaseMatcher:
    """
    所有匹配器统一抽象基类
    所有后续新增匹配模块（拼音/方言/语义）必须继承本类，实现统一接口
    """
    def match(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        统一匹配接口
        :param query: 用户输入查询串
        :param top_k: 返回结果数量
        :return: 结构化结果列表
        """
        raise NotImplementedError("所有匹配器必须实现 match 接口方法")