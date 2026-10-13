# 亲属关系图词条盘点与导入

`hinghwa-dict-backend/word/data/relative_graph_entries.json` 是待审计清单，不是自动采集结果。它依据莆仙乡音社《莆仙话亲属称谓关系图 v1.0（莆田腔版本）》[原图](https://github.com/user-attachments/assets/3aacc81d-7607-45d6-815c-7721fdf7c905)（[backend issue #390](https://github.com/e-dialect/hinghwa-dict-backend/issues/390)），并从前端 `hinghwa-dict-web/src/components/Tools/relative.js` 盘点 ID 为 `null` 的图节点。经前后端清单对照，当前列入 20 个唯一方言词形；`阿丈`另标记为快照已有。关系图能支持词形及关系角色盘点，不能单独证明词条的本地读音或释义。

2026-10-12 对给定 SQLite 快照做了精确词形核查。图清单中的 `阿丈` 已对应数据库 ID 6115，因此标记为 `existing`，并要求人工核对现存释义、IPA 和拼音；不应再作为新词创建。快照另有 `孙婿`（4930）、`孙新妇`（4931）、`外头孙`（2440）和 `婶娘囝`（4820），它们不是这份 `null` 节点清单中的词形，不据此添加图词条。

其余条目暂为 `pending`：现有来源不足以可靠核定兴化本地的 IPA、拼音和完整释义。不要根据关系标签猜读音或扩写释义。转为 `confirmed` 前，维护者须逐项补全 `word`、`definition`、`standard_ipa`、`standard_pinyin`、`evidence`，并由熟悉该方言的审校者对照可追溯词典条目、页码或经校订的原始记录复核。只有关系图截图而没有独立读音/释义依据，不满足导入门槛。

默认命令只做 dry-run，不写数据库：

```bash
cd hinghwa-dict-backend
python manage.py import_relative_graph_entries --json
python manage.py import_relative_graph_entries --catalog /path/to/reviewed.json --apply --contributor-id 2 --json
```

`--apply` 要求指定已存在的贡献者，不会创建账户。导入前会预检整份清单；任何目录格式错误、重复词形或与库内词条不一致的冲突都会阻止本批所有候选词写入，并以非零状态退出（`--json` 会先输出完整报告）。目录中标为 `existing` 的条目也会按 ID 和词形查询当前运行时数据库；快照中的 ID 若已不存在或指向其他词形，就作为冲突要求重审。相同词、释义和规范化读音已存在时记为 `existing`，不会更新词条。成功新建的词条仍设置 `visibility=False`，必须经过正常审核流程。

此脚本仅用于第一阶段经来源复核后的词条补录；`pending` 代表等待人工审校，不代表自动生成待审数据。整体词典数据结构及关系图模块的后续调整跟踪于[总 Issue #188](https://github.com/e-dialect/hinghwa-dict-web/issues/188)。

报告类别：

- `created`：dry-run 中是候选；apply 中是已写入记录。
- `existing`：ID 与词形在运行时数据库中匹配的人工标注词条，或与库内审校字段一致的词条。
- `pending`：缺少审校材料，不会写库。
- `conflict`：目录无效、词形重复、已有词 ID 过期/错配或库内字段不一致。
- `blocked`：apply 时整批存在冲突而未写入的候选词。
