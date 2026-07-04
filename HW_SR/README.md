# hinghwa_semantic_retrieval

莆仙方言语义检索子模块。

## 环境与技术栈

- Python 3.13
- HTTP 服务：标准库 `http.server`，使用 `ThreadingHTTPServer` 提供 8088 端口访问
- 检索能力：Django ORM 数据加载、FAISS 向量检索、IPA / 拼音 / 方言词匹配、结果格式化
- 依赖安装：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

## 启动方式

先激活虚拟环境：

```powershell
\.\.venv\Scripts\Activate.ps1
```

启动 HTTP 服务：

```powershell
python demo.py --mode serve --port 8088
```

如果你还想保留命令行交互模式：

```powershell
python demo.py --mode cli
```

## Django 接口服务

如果你要把当前检索能力封装给主项目调用，建议使用仓库内新增的 Django 外壳，而不是改动现有 `demo.py` 的服务逻辑。

启动方式：

```powershell
python django_service\manage.py runserver 0.0.0.0:8000
```

接口地址：

- `GET /api/health/`
- `GET /api/query/id/123/`
- `GET /api/query/word/郎罢/`
- `GET /api/query/郎`
- `GET /api/query/?query=郎`
- `POST /api/query/`

POST 请求体示例：

```json
{
	"query": "郎"
}
```

返回结构与当前 `demo.py` 的 `query_detail()` 一致，外层统一补充 `ok` 字段，方便主项目直接判断请求是否成功。

更完整的部署和接入流程见 [docs/django_integration.md](docs/django_integration.md)。

## 接口说明

### 1. 健康检查

```http
GET http://localhost:8088/health
```

返回示例：

```json
{
	"ok": true,
	"message": "service running"
}
```

### 2. Apifox 测试接口

```http
GET http://127.0.0.1:8000/api/query/id/123/
GET http://127.0.0.1:8000/api/query/word/郎罢/
GET http://127.0.0.1:8000/api/query/郎
GET http://127.0.0.1:8000/api/query/?query=郎
POST http://127.0.0.1:8000/api/query/
```

POST 请求体示例：

```json
{
	"query": "郎"
}
```

### 3. 浏览器直连查询

可以直接在浏览器地址栏输入：

```text
http://127.0.0.1:8000/api/query/郎
http://127.0.0.1:8000/api/query/郎罢
```

服务会直接返回结构化 JSON 结果，不需要额外前端页面。

## 返回结构

接口返回包含以下字段：

- `ok`：是否请求成功
- `query`：原始查询词
- `intent`：意图识别结果
- `confidence`：意图置信度
- `count`：匹配条数
- `results`：结构化检索结果
- `formatted`：便于调试的文本格式结果

## 备注

- 代码入口在 `demo.py`
- 当前服务默认监听 `0.0.0.0:8088`
- 第一次查询会按需加载数据和模型，首个请求可能稍慢
