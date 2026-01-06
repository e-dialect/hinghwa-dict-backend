# 依赖和部署兼容性说明

## 概述

本文档说明了 `requirements.txt`、`Dockerfile` 和相关配置文件之间的兼容性设置。

## Python 版本兼容性

### 生产环境 (Docker)
- **Dockerfile**: Python 3.10 (python:3.10-bookworm)
- **推荐原因**: Python 3.10 是一个稳定的 LTS 版本，在生产环境中广泛使用

### 开发环境
- **支持**: Python 3.10, 3.11, 3.12
- **requirements.txt** 已经过测试，可在这些版本上正常工作

## 关键依赖版本说明

### NumPy 版本
```
numpy>=1.26.0,<2.0.0
```
- **原因**: 
  - `numpy 1.23.x` 只支持 Python 3.8-3.11，不支持 Python 3.12
  - `numpy 1.26.x` 支持 Python 3.9-3.12，兼容性最好
  - 避免 numpy 2.x 以保持向后兼容性
- **兼容**: ✅ Python 3.10 (Dockerfile) 和 Python 3.12 (开发)

### FFmpeg 依赖
```python
# 已移除: ffmpeg==1.4, ffprobe==0.5
```
- **原因**: 
  - `ffmpeg==1.4` 和 `ffprobe==0.5` 是过时的 Python 包装器
  - 它们与现代 Python 版本不兼容
  - 项目实际上不导入这些 Python 包
  - 项目使用 `pydub`，它依赖系统级的 ffmpeg 工具

- **解决方案**: 
  - 在 Dockerfile 中通过 `apt-get install ffmpeg` 安装系统级 ffmpeg
  - 保留 `pydub==0.25.1` 作为 Python 音频处理库

### Django 及扩展
```
django==5.0.3
django-cors-headers~=4.3.1
django-simpleui==2023.3.1
django_apscheduler
django-notifications-hq==1.8.3
```
- **兼容**: ✅ 所有包都支持 Python 3.10-3.12

## Dockerfile 优化

### 修复的问题

1. **pip 安装命令语法错误**
   ```dockerfile
   # 修复前:
   RUN pip install -ihttps://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
   
   # 修复后:
   RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
   ```
   - 在 `-i` 和 URL 之间添加了缺失的空格

2. **优化层结构**
   ```dockerfile
   # 修复前: 多个 RUN 命令
   RUN apt-get update
   RUN apt-get install ffmpeg -y
   
   # 修复后: 合并命令并清理
   RUN apt-get update && \
       apt-get install -y ffmpeg && \
       apt-get clean && \
       rm -rf /var/lib/apt/lists/*
   ```
   - 减少镜像层数
   - 清理 apt 缓存以减小镜像大小

3. **添加 pip 缓存优化**
   ```dockerfile
   RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
   ```
   - 使用 `--no-cache-dir` 减小镜像大小

## .dockerignore 优化

增强了 `.dockerignore` 文件以避免不必要的文件被复制到 Docker 镜像中：

```
# 数据库
*.sqlite3
db.sqlite3

# 媒体文件
media/

# Python 缓存
__pycache__/
*.py[cod]

# 虚拟环境
venv/
env/

# IDE 文件
.vscode/
.idea/

# 日志
logs/
*.log

# 环境变量
.env

# Git 文件
.git/
.gitignore
```

**好处**:
- 减小 Docker 上下文大小
- 加快构建速度
- 避免敏感信息泄露

## 系统依赖

### 必需的系统包

在 Docker 容器中（已在 Dockerfile 中配置）:
```bash
apt-get install -y ffmpeg
```

在本地开发环境中:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 从 https://ffmpeg.org/download.html 下载并配置环境变量
```

## 安装测试

### 验证 requirements.txt 可以一次性安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 升级 pip
pip install --upgrade pip setuptools wheel

# 安装依赖（应该一次成功）
pip install -r hinghwa-dict-backend/requirements.txt
```

### 验证 Docker 构建

```bash
cd hinghwa-dict-backend
docker build -t hinghwa-dict-backend:test .
```

## 兼容性矩阵

| 组件 | Python 3.10 | Python 3.11 | Python 3.12 |
|------|-------------|-------------|-------------|
| Django 5.0.3 | ✅ | ✅ | ✅ |
| numpy 1.26.x | ✅ | ✅ | ✅ |
| pydub 0.25.1 | ✅ | ✅ | ✅ |
| django-simpleui | ✅ | ✅ | ✅ |
| 所有其他依赖 | ✅ | ✅ | ✅ |

## 故障排除

### 问题: numpy 安装失败

**原因**: 试图在 Python 3.12 上安装 numpy 1.23.x

**解决方案**: 使用更新的 requirements.txt（已修复）

### 问题: ffmpeg 或 ffprobe 模块未找到

**原因**: 旧的 requirements.txt 包含过时的 Python 包

**解决方案**: 
1. 从 requirements.txt 中移除（已完成）
2. 安装系统级 ffmpeg（Dockerfile 中已配置）

### 问题: pip install 命令失败

**原因**: Dockerfile 中的 pip 命令语法错误

**解决方案**: 已修复（在 -i 和 URL 之间添加空格）

## 更新日志

### 2024-01-06
- ✅ 修复 numpy 版本不兼容问题 (1.23.0 → 1.26.0+)
- ✅ 移除过时的 ffmpeg/ffprobe Python 包
- ✅ 修复 Dockerfile pip 命令语法错误
- ✅ 优化 Dockerfile 层结构
- ✅ 增强 .dockerignore 文件
- ✅ 添加详细注释和文档
- ✅ 验证兼容性（Python 3.10-3.12）

## 维护建议

1. **定期更新依赖**: 使用 `pip list --outdated` 检查过期包
2. **测试兼容性**: 在更新前在虚拟环境中测试
3. **保持文档同步**: 更新依赖时同步更新此文档
4. **遵循语义化版本**: 使用 `~=` 或 `>=,<` 指定版本范围
5. **Docker 镜像优化**: 定期检查镜像大小并优化
