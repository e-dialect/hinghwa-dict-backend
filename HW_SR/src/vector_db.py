#建立向量库，利用（双轨检索：精准 + 语义）
import faiss
import numpy as np
import os
import sys
import pickle
from typing import List, Dict
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_loader import load_excel_data, exact_match_search, get_full_df, FIELD_MAPPING
from src.encoder import encode_entry, encode_query, VECTOR_DIM

# ====================== 配置 ======================
INDEX_PATH = "models/dialect_faiss.index"  # FAISS索引保存路径
ID_MAP_PATH = "models/entry_id_map.pkl"    # 词条ID映射路径
# ===================================================

def build_faiss_index() -> tuple[faiss.IndexFlatIP, List[str]]:
    """构建FAISS语义索引（适配普通话/释义查询）"""
    df, entry_ids = load_excel_data()
    vectors = []
    print("生成词条向量...")
    for _, row in tqdm(df.iterrows(), total=len(df), desc="生成向量"):
        vectors.append(encode_entry(row.to_dict()))
    
    # 构建FAISS内积索引
    vectors_np = np.array(vectors, dtype=np.float32)
    index = faiss.IndexFlatIP(VECTOR_DIM)
    index.add(vectors_np)
    
    # 保存索引
    os.makedirs("models", exist_ok=True)
    faiss.write_index(index, INDEX_PATH)
    with open(ID_MAP_PATH, "wb") as f:
        pickle.dump(entry_ids, f)
    print(f"FAISS索引构建完成！共{index.ntotal}条向量")
    return index, entry_ids

def load_faiss_index() -> tuple[faiss.IndexFlatIP, List[str]]:
    """加载索引（不存在则自动构建）"""
    if not os.path.exists(INDEX_PATH) or not os.path.exists(ID_MAP_PATH):
        return build_faiss_index()
    index = faiss.read_index(INDEX_PATH)
    with open(ID_MAP_PATH, "rb") as f:
        entry_ids = pickle.load(f)
    print(f"加载本地FAISS索引：{index.ntotal}条向量")
    return index, entry_ids

def semantic_search(query_text: str, top_k: int = 5) -> List[Dict]:
    """语义检索：针对普通话/释义查询"""
    index, _ = load_faiss_index()
    df = get_full_df()
    
    # 生成查询向量+执行检索
    query_vec = encode_query(query_text)
    scores, indices = index.search(np.array([query_vec], dtype=np.float32), top_k)
    
    # 组装结果（含相似度得分）
    results = []
    for i in range(top_k):
        idx = indices[0][i]
        if idx < 0:
            continue
        entry = df.iloc[idx].to_dict()
        entry["相似度"] = round(float(scores[0][i]), 3)  # 保留x位小数
        results.append(entry)
    return results

def core_search(parsed_query: dict) -> List[Dict]:
    """核心检索：按查询类型自动选链路（精准/语义）"""
    keywords = parsed_query["核心词"]
    query_type = parsed_query["类型"]  # 1=方言查方言，2=普通话/释义查方言
    results = []
    
    # 类型1：方言查方言 → 精准匹配优先
    if query_type == 1:
        for kw in keywords:
            results.extend(exact_match_search(kw))
        # 精准无结果，语义兜底
        if not results:
            results = semantic_search(" ".join(keywords), top_k=3)
    
    # 类型2：普通话/释义查方言 → 语义检索
    elif query_type == 2:
        results = semantic_search(" ".join(keywords), top_k=5)
    
    # 去重（按方言词去重）
    seen_words = set()
    unique_results = []
    for res in results:
        word = res[FIELD_MAPPING["dialect_word"]]
        if word not in seen_words:
            seen_words.add(word)
            unique_results.append(res)
    return unique_results

# 测试代码：运行此文件构建索引+测试检索
if __name__ == "__main__":
    #不再强制构建，自动加载本地已有的索引
    index, entry_ids = load_faiss_index()
    # 测试普通话查方言
    test_res = semantic_search("爸爸", top_k=5)
    for res in test_res:
        print(f"方言词：{res['方言词']} | 释义：{res['释义注释']} | 相似度：{res['相似度']}")