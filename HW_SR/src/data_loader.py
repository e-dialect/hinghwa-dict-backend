"""加载 Django ORM 数据 + 精准倒排索引。"""

import os
from typing import Dict, List, Tuple

import pandas as pd


# ====================== 核心配置：Django ORM 数据源 ======================
DJANGO_SETTINGS_MODULE = "django_service.config.settings"

FIELD_MAPPING = {
    "dialect_word": "方言词",
    "simple_pron": "简易发音",
    "standard_pron": "标准发音",
    "definition": "释义注释",
}
# ====================================================================

# 全局单例：方言词精准倒排索引（方言词→全字段数据）
INVERTED_INDEX: Dict[str, dict] = {}
# 全局单例：全量数据集
FULL_DF: pd.DataFrame = None
_DJANGO_READY = False


def _ensure_django() -> None:
    global _DJANGO_READY
    if _DJANGO_READY:
        return

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)
    import django
    from django.apps import apps

    if not apps.ready:
        django.setup()
    _DJANGO_READY = True


def _combine_definition(definition: str, annotation: str) -> str:
    definition = str(definition).strip()
    annotation = str(annotation).strip()
    if definition and annotation:
        return f"{definition}\n{annotation}"
    return definition or annotation


def _normalize_word_word_item(item: dict) -> dict:
    combined_definition = _combine_definition(item.get("definition", ""), item.get("annotation", ""))
    return {
        "id": int(item.get("id", 0) or 0),
        "word": str(item.get("word", "")).strip(),
        "definition": str(item.get("definition", "")).strip(),
        "annotation": str(item.get("annotation", "")).strip(),
        "mandarin": str(item.get("mandarin", "")).strip(),
        "standard_ipa": str(item.get("standard_ipa", "")).strip(),
        "standard_pinyin": str(item.get("standard_pinyin", "")).strip(),
        "views": int(item.get("views", 0) or 0),
        "visibility": bool(item.get("visibility", False)),
        "contributor_id": int(item.get("contributor_id", 0) or 0),
        "tags": str(item.get("tags", "")).strip(),
        "方言词": str(item.get("word", "")).strip(),
        "简易发音": str(item.get("standard_pinyin", "")).strip(),
        "标准发音": str(item.get("standard_ipa", "")).strip(),
        "释义注释": combined_definition,
    }


def _fetch_word_word_rows() -> List[dict]:
    _ensure_django()
    from django_service.api.models import WordWord

    rows: List[dict] = []
    queryset = WordWord.objects.order_by("id").values(
        "id",
        "word",
        "definition",
        "annotation",
        "mandarin",
        "standard_ipa",
        "standard_pinyin",
        "views",
        "visibility",
        "contributor_id",
        "tags",
    )

    for item in queryset:
        rows.append({
            "id": int(item.get("id", 0)),
            "方言词": str(item.get("word", "")).strip(),
            "简易发音": str(item.get("standard_pinyin", "")).strip(),
            "标准发音": str(item.get("standard_ipa", "")).strip(),
            "释义注释": _combine_definition(item.get("definition", ""), item.get("annotation", "")),
        })

    return rows


def get_word_word_dto_by_id(word_id: int | str) -> dict | None:
    """按 word_word 表主键反查并返回完整 DTO。"""
    _ensure_django()
    from django_service.api.models import WordWord

    try:
        pk = int(word_id)
    except (TypeError, ValueError):
        return None

    item = WordWord.objects.filter(id=pk).values(
        "id",
        "word",
        "definition",
        "annotation",
        "mandarin",
        "standard_ipa",
        "standard_pinyin",
        "views",
        "visibility",
        "contributor_id",
        "tags",
    ).first()
    if not item:
        return None

    return _normalize_word_word_item(item)


def get_word_word_dtos_by_word(word: int | str) -> List[dict]:
    """按方言词反查并返回完整 DTO 列表。"""
    _ensure_django()
    from django_service.api.models import WordWord

    word_text = str(word).strip()
    if not word_text:
        return []

    querysets = WordWord.objects.filter(word__iexact=word_text).values(
        "id",
        "word",
        "definition",
        "annotation",
        "mandarin",
        "standard_ipa",
        "standard_pinyin",
        "views",
        "visibility",
        "contributor_id",
        "tags",
    ).order_by("id")

    return [_normalize_word_word_item(item) for item in querysets]


def load_excel_data() -> Tuple[pd.DataFrame, List[str]]:
    """加载 Django ORM 数据，构建精准倒排索引（方言查方言核心）"""
    global FULL_DF

    print("正在加载 Django ORM 数据（word_word 表）...")
    rows = _fetch_word_word_rows()
    if not rows:
        raise ValueError("word_word 表中没有可用数据")

    df = pd.DataFrame(rows)
    df = df.dropna(how="all").copy()
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip().fillna("")

    df["entry_id"] = [f"entry_{i:04d}" for i in range(len(df))]
    FULL_DF = df

    build_inverted_index(df)
    print(f"数据加载完成！共{len(df)}条词条，精准索引构建成功")
    return df, df["entry_id"].tolist()

def build_inverted_index(df: pd.DataFrame):
    """构建方言词倒排索引，确保方言查方言100%精准"""
    global INVERTED_INDEX
    INVERTED_INDEX.clear()
    for _, row in df.iterrows():
        dialect_word = row[FIELD_MAPPING["dialect_word"]]
        index_key = dialect_word.lower()  # 支持大小写不敏感匹配
        INVERTED_INDEX[index_key] = row.to_dict()

def exact_match_search(query: str) -> List[dict]:
    """方言词精准查询：输入方言词，返回全字段数据"""
    query_key = query.strip().lower()
    if not INVERTED_INDEX:
        load_excel_data()

    exact_result = INVERTED_INDEX.get(query_key)
    if exact_result:
        return [exact_result]

    return [data for word, data in INVERTED_INDEX.items() if query_key in word]

def get_full_df() -> pd.DataFrame:
    """获取全量数据集（供语义检索用）"""
    if FULL_DF is None:
        load_excel_data()
    return FULL_DF

# 测试代码：运行此文件可验证数据加载
if __name__ == "__main__":
    load_excel_data()
    test_res = exact_match_search("郎罢")  # 替换为你的方言词测试
    print(f"精准查询测试结果：{test_res}")