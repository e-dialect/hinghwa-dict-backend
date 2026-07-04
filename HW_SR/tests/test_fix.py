import pandas as pd
import re
import os

# ====================== 自动找项目data目录下的Excel文件 ======================
# 获取当前脚本所在目录（tests目录）
current_dir = os.path.dirname(os.path.abspath(__file__))
# 项目根目录（tests的上一级）
project_root = os.path.dirname(current_dir)
# data目录
data_dir = os.path.join(project_root, "data")

# 自动找data目录下的第一个Excel文件
excel_files = [f for f in os.listdir(data_dir) if f.endswith((".xlsx", ".xls"))]
if not excel_files:
    raise FileNotFoundError(f"在 {data_dir} 目录下没找到Excel文件！请把你的方言词典Excel文件放到这个目录里。")
EXCEL_PATH = os.path.join(data_dir, excel_files[0])
print(f"✅ 自动找到Excel文件：{EXCEL_PATH}")
# ==============================================================================

# 1. 加载数据，先看列名和前几行
df = pd.read_excel(EXCEL_PATH)
print(f"\n✅ 数据加载成功！共{len(df)}条词条")
print(f"✅ Excel列名：{df.columns.tolist()}")
print("\n✅ 前3条数据预览：")
print(df.head(3))

# 2. 让你确认字段名是否正确
print("\n⚠️  请确认上面的列名是否包含：方言词、简易发音、标准发音、释义注释（或对应的英文列名）")
input("按回车键继续...")

# 3. 清洗函数（极简版，只去空格转小写）
def clean_ipa(ipa_str):
    if not isinstance(ipa_str, str):
        return ""
    return ipa_str.strip().lower().replace(" ", "")

# 4. 构建双索引（先让你手动指定列名，避免字段名不对）
print("\n请输入Excel中对应的列名（直接回车使用默认值）：")
col_word = input("方言词列名（默认：方言词）：") or "方言词"
col_simple = input("简易发音列名（默认：简易发音）：") or "简易发音"
col_standard = input("标准发音列名（默认：标准发音）：") or "标准发音"
col_def = input("释义注释列名（默认：释义注释）：") or "释义注释"

simple_ipa_index = {}
standard_ipa_index = {}

for _, row in df.iterrows():
    try:
        word = str(row[col_word])
        simple_pron = clean_ipa(str(row[col_simple]))
        standard_pron = clean_ipa(str(row[col_standard]))
        definition = str(row[col_def])
        
        if simple_pron:
            if simple_pron not in simple_ipa_index:
                simple_ipa_index[simple_pron] = []
            simple_ipa_index[simple_pron].append({
                "方言词": word,
                "简易发音": simple_pron,
                "标准发音": standard_pron,
                "释义注释": definition
            })
        
        if standard_pron:
            if standard_pron not in standard_ipa_index:
                standard_ipa_index[standard_pron] = []
            standard_ipa_index[standard_pron].append({
                "方言词": word,
                "简易发音": simple_pron,
                "标准发音": standard_pron,
                "释义注释": definition
            })
    except Exception as e:
        print(f"⚠️  跳过一条数据：{e}")
        continue

print(f"\n✅ 简易发音索引构建完成，共{len(simple_ipa_index)}条")
print(f"✅ 标准IPA索引构建完成，共{len(standard_ipa_index)}条")

# 5. 测试你之前失败的输入！
test_inputs = [
    "diau1cong1",
    "a1i2",
    "tiau21lɔŋ533",
    "diau1dorh6"
]

print("\n==================== 测试结果 ====================")
for inp in test_inputs:
    clean_inp = clean_ipa(inp)
    # 先查简易发音索引
    res = simple_ipa_index.get(clean_inp, [])
    if res:
        print(f"输入：{inp} → ✅ 匹配简易发音成功！")
        for item in res:
            print(f"  方言词：{item['方言词']}，标准IPA：{item['标准发音']}，释义：{item['释义注释'][:30]}...")
    else:
        # 再查标准IPA索引
        res = standard_ipa_index.get(clean_inp, [])
        if res:
            print(f"输入：{inp} → ✅ 匹配标准IPA成功！")
            for item in res:
                print(f"  方言词：{item['方言词']}，简易发音：{item['简易发音']}，释义：{item['释义注释'][:30]}...")
        else:
            print(f"输入：{inp} → ❌ 未匹配到")
print("===================================================")