#利用模型分析重写用户输入
#方案一：直接调用API云端模型接口，获取重写后的查询文本
# 注意：需先按方案A或B，替换src/query_rewriter.py
import requests
import os
from dotenv import load_dotenv

# ====================== 配置：替换为你的API密钥 ======================
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # 使用LLMAPI进行查询解析
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")  # 轻量模型，响应快
# ==========================================================================

def parse_query(user_query: str) -> dict:
    """调用LLM API，解析用户查询：提取核心词+判断类型"""
    url = f"{DEEPSEEK_BASE_URL}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    # 严格约束输出格式：仅返回JSON，避免多余内容
    prompt = f"""
你是方言查询解析助手，仅做两件事：
1. 提取用户查询的【核心词】（方言词/普通话词/释义）；
2. 判断【类型】：1=方言查方言（输入是方言词），2=普通话/释义查方言；
输出严格为JSON，格式：{{"核心词": ["词1", "词2"], "类型": 1或2}}

示例1：
用户输入：漉
输出：{{"核心词": ["漉"], "类型": 1}}

示例2：
用户输入：爸爸用方言怎么说
输出：{{"核心词": ["爸爸"], "类型": 2}}

示例3：
用户输入：莆仙话里踩水的词是什么
输出：{{"核心词": ["踩水"], "类型": 2}}

示例4：
用户输入：输会𢫫裤里的𢫫裤
输出：{{"核心词": ["𢫫裤"], "类型": 1}}

现在处理用户输入：{user_query}
"""
    # 调用API（轻量模型，响应快）
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,  # 低温保证输出稳定
        "max_tokens": 100
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=3)
        response.raise_for_status()  # 抛出自定义错误
        # 解析JSON结果
        result = response.json()["choices"][0]["message"]["content"].strip()
        print(f"查询解析：{result}")  # 调试日志
        return eval(result)  # 转为字典
    except Exception as e:
        # 出错兜底：默认按普通话查方言处理
        print(f"API解析出错：{e}，兜底处理")
        return {"核心词": [user_query], "类型": 2}

# 测试代码：运行此文件验证解析
if __name__ == "__main__":
    test_queries = ["漉", "爸爸", "踩水的方言"]
    for q in test_queries:
        print(f"\n原始查询：{q}")
        parse_query(q)