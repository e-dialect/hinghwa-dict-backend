# Django 接入与部署说明

本文说明如何把现有检索项目封装成 Django 接口服务，并接入主项目。

## 设计原则

- 不修改现有检索逻辑，继续沿用 `demo.py` 中的 `ExtensibleFusionQueryManager`。
- Django 只负责 HTTP 层、参数解析、状态码和 JSON 输出。
- 查询入口保持单一，避免主项目同时直连多个实现。

## 当前结构

- 核心检索：`demo.py` 中的 `ExtensibleFusionQueryManager.query_detail()`
- 现有独立 HTTP 服务：`demo.py --mode serve`
- 新增 Django 外壳：`django_service/`

## 服务接口

### 健康检查

`GET /api/health/`

返回示例：

```json
{
  "ok": true,
  "message": "service running"
}
```

### 查询接口

`GET /api/query/id/123/`

`GET /api/query/word/郎罢/`

`GET /api/query/?query=郎`

`POST /api/query/`

POST 请求体示例：

```json
{
  "query": "郎"
}
```

### 返回结构

接口返回会保留检索核心输出：

- `query`
- `intent`
- `confidence`
- `count`
- `results`
- `formatted`

并在最外层统一增加：

- `ok`

## 本地部署流程

1. 安装依赖。

```powershell
\.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. 启动 Django 服务。

```powershell
python django_service\manage.py runserver 0.0.0.0:8000
```

3. 用浏览器或 Apifox 验证。

```text
http://127.0.0.1:8000/api/health/
http://127.0.0.1:8000/api/query/id/123/
http://127.0.0.1:8000/api/query/word/郎罢/
http://127.0.0.1:8000/api/query/?query=郎
```

## 主项目接入流程

建议主项目只把它当作一个独立查询服务来调用。

### 方式一：后端直连

主项目后端向 Django 服务发送 HTTP 请求，拿到 JSON 后直接渲染或继续业务处理。

Python 示例：

```python
import requests

resp = requests.get("http://127.0.0.1:8000/api/query/", params={"query": "郎"}, timeout=15)
data = resp.json()
```

按主键或方言词查询时，也可以直接调用：

```python
resp = requests.get("http://127.0.0.1:8000/api/query/id/123/", timeout=15)
data = resp.json()

resp = requests.get("http://127.0.0.1:8000/api/query/word/郎罢/", timeout=15)
data = resp.json()
```

### 方式二：前端直连

如果主项目前端直接请求这个接口，当前 Django 外壳已经返回了基础跨域头，可直接测试。

### 方式三：反向代理统一域名

生产环境里可以把 Django 服务挂到内网端口，再由 Nginx 或网关转发到主项目统一域名下。

## 部署建议

- 开发测试：直接用 `runserver`
- 内网联调：Django 独立进程运行，主项目通过内网地址调用
- 生产环境：建议由反向代理暴露统一入口，Django 只保留服务接口

## 维护建议

- 如果后续要新增鉴权、限流、日志、灰度，可以只加在 Django 外层，不动检索核心。
- 如果后续要复用同一套查询逻辑给 Flask、FastAPI 或 CLI，也建议继续复用现有查询管理器。