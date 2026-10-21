# 词语语义检索

`GET /words?search=...` 的新检索实现在主 Django 项目的 `word` app 内运行，
不需要启动第二套 HTTP 服务。它支持方言词精确查询、拼音、IPA、混合输入和
BGE 语义检索；接口返回结构保持不变。

检索策略整理自
[`e-dialect/hinghwa_semantic_retrieval`](https://github.com/e-dialect/hinghwa_semantic_retrieval)，
但模型、索引和演示工程不随 Django 源码发布。

## 索引生命周期

词条创建、删除，或下列字段发生变化时，Django 会在事务提交后登记新的索引版本：

- `word`
- `definition`
- `annotation`
- `mandarin`
- `standard_ipa`
- `standard_pinyin`
- `visibility`

独立 worker 读取所有 `visibility=True` 的词条，导出带真实 `Word.id` 的 JSON
快照并生成 FAISS 索引。构建完成后通过 manifest 原子切换；失败不会覆盖上一代
文件。索引等待、构建或失败期间，Web 服务会记录原因并回退原有加权检索。

```bash
python manage.py migrate
python manage.py semantic_index_worker
```

一次性重建或故障恢复：

```bash
python manage.py semantic_index_worker --once --force
```

Docker Compose 已包含 `semantic-index-worker`，Web 与 worker 必须共享数据库和
`semantic_search_data` volume。索引状态也可在 Django Admin 中查看。

## 模型与配置

默认模型为 `BAAI/bge-small-zh-v1.5`，固定 revision：
`7999e1d3359715c523056ef9478215996d62a620`。Docker 构建阶段下载模型，运行阶段
启用 Hugging Face 离线模式。该模型在模型卡中标注为 MIT License：
<https://huggingface.co/BAAI/bge-small-zh-v1.5>。

主要环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `SEMANTIC_SEARCH_DATA_DIR` | `semantic_search_data` | 快照、索引和 manifest 目录 |
| `SEMANTIC_SEARCH_MODEL_NAME` | `BAAI/bge-small-zh-v1.5` | 模型名称 |
| `SEMANTIC_SEARCH_MODEL_REVISION` | 上述固定 commit | 模型 revision |
| `SEMANTIC_SEARCH_ENCODING_BATCH_SIZE` | `32` | 每次编码的文本数，允许 `1..32`；资源紧张的 Compose 部署可在 `.env` 中设为 `8`，同时应用于 Web 和 worker |
| `SEMANTIC_SEARCH_WORKER_POLL_SECONDS` | `5` | worker 空闲轮询间隔 |
| `SEMANTIC_SEARCH_WORKER_MAX_BACKOFF_SECONDS` | `300` | 失败重试退避上限 |
| `SEMANTIC_SEARCH_WORKER_LEASE_SECONDS` | `1800` | 单次构建的 worker lease |
| `SEMANTIC_SEARCH_MODEL_CACHE` | `.model_cache` | 构建阶段的模型缓存目录 |

## 可选 DeepSeek 解析

DeepSeek 默认关闭。本地分类和 BGE 足以处理普通查询；只有同时配置以下变量时，
自然语言和混合查询才会被发送给外部服务：

```dotenv
SEMANTIC_SEARCH_LLM_ENABLED=true
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
SEMANTIC_SEARCH_LLM_TIMEOUT_SECONDS=3
```

外部服务必须返回严格 JSON。超时、错误状态或无效 JSON 都会自动改用本地查询，
代码不会执行模型返回的文本。启用此功能前，应确认查询文本外发符合隐私政策。


## SQLite directory and source reconciliation

`SQLITE_DATABASE_PATH` optionally selects an absolute, canonical SQLite path. When unset, the legacy `BASE_DIR/db.sqlite3` default is unchanged. The example Compose uses `/data/db.sqlite3` and binds its complete existing `../../data` parent for both Web and worker; WAL, SHM and journal files must remain beside the same database for both processes. Web still binds existing media, logs and **material/audio** at their old container destinations. Do not copy to a second live database or bind only the main SQLite file. For a legacy image which predates this setting, swapping only the image in this Compose is unsafe: retain its frozen old configuration or use a separately reviewed canonical-directory runtime bridge and exact-pair replay. This example change does not migrate or enable a production instance; validate ownership, canonical connection paths and the exact data/configuration pair before rollout. The worker shares only this application's registered data parent and has no public route; any narrower worker mount policy requires a separately rehearsed directory layout.

Post-commit signals are best effort: database contention must not turn an already committed Word edit into a misleading failed request. The worker reconciles all canonical visible Word fields against the published `entries_sha256` and both artifact checksums at startup and every `SEMANTIC_SEARCH_RECONCILE_SECONDS` (default 30, allowed 0..300; zero checks each poll). Bulk operations, raw/legacy SQL writes and missed signals are detected without relying on the revision counter alone. Non-index fields such as view counts do not trigger a rebuild. Source hashing streams rows in stable ID order with the exact canonical encoding used by the index snapshot; it never loads the whole corpus just to poll.

Before marking a build ready, the worker obtains SQLite's writer reservation and checks the current canonical source digest again. A changed source leaves the state pending and does not publish that stale generation. A failed/expired owner cannot publish over another worker. The final source scan and each checksum scan have a `SEMANTIC_SEARCH_SOURCE_SCAN_SECONDS` budget (default 2, positive and at most 30 seconds); the source scan bounds the final SQLite write-lock window, subject to one row/chunk and filesystem scheduling. Budget exhaustion fails closed to a pending/failed state rather than trusting an unverified ready generation. Size/budget failures need measurement and review; raising retry counts does not establish compatibility. Periodic reconciliation requires the worker to be running and the DB/storage to become available; it is not a promise of instant freshness or a substitute for worker monitoring.

An explicit `semantic_index_worker --once --force` propagates database invalidation errors and exits unsuccessfully if it cannot complete a rebuild. It must not be treated as successful merely because a best-effort invalidation returned or a pending/leased worker did nothing. Real recovery evidence must still check revision, new generation, source/file digests and released lease.

Regressions cover real SQLite writer exclusion, a concurrent legacy write during encoding, missed signals, periodic throttling, all encoded fields, corrupt artifacts, expired leases, and SIGKILL/WAL directory recovery. The e2e image job runs these inside its existing built image with network disabled, synthetic settings and bounded tmpfs/resources; tests use a deterministic encoder and real CPU FAISS, not production data or external/model downloads. This is separate from full-model capacity acceptance. No approval-field migration or cross-version approval bridge is supplied here: legacy re-review of `Application.approved` remains a distinct unresolved business-compatibility issue.
