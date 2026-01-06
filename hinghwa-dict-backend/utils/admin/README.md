# Django Admin 自定义前端工具

## 概述

本项目为 Django Admin 添加了自定义前端工具，以增强内容编辑和展示体验。

## 功能特性

### 1. Markdown 编辑器

为以下模型的字段添加了 Markdown 编辑器（使用 EasyMDE）：

- **Article 模型**：`content` 字段
- **Word 模型**：`annotation` 字段
- **Application 模型**：`annotation` 字段

**功能特点**：
- 实时预览
- 语法高亮
- 工具栏包含常用 Markdown 格式化选项（粗体、斜体、标题、列表、链接、图片等）
- 全屏编辑模式
- 并排预览模式
- 字数统计和光标位置显示

### 2. 音频播放器

为以下模型的字段添加了音频播放器：

- **Music 模型**：`source` 字段
- **Pronunciation 模型**：`source` 字段

**功能特点**：
- 直接在 Admin 界面中播放音频文件
- 支持多种音频格式（MP3、WAV、OGG）
- 保留 URL 输入框，同时显示音频播放器
- 响应式设计，适配不同屏幕尺寸

### 3. 图片预览

为以下模型的字段添加了图片预览：

- **Article 模型**：`cover` 字段（文章封面）
- **Music 模型**：`cover` 字段（音乐封面）
- **UserInfo 模型**：`avatar` 字段（用户头像）

**功能特点**：
- 直接在 Admin 界面中预览图片
- 可配置预览图片的最大宽度和高度
- 图片加载失败时显示友好提示
- 保留 URL 输入框，同时显示图片预览
- 美观的边框和圆角样式

## 技术实现

### 自定义 Widget 模块

创建了 `utils/admin/widgets.py` 模块，包含三个自定义 Widget：

1. **MarkdownEditorWidget**：继承自 `forms.Textarea`
   - 使用 EasyMDE（SimpleMDE 的后继者）
   - 通过 CDN 加载 CSS 和 JavaScript
   - 自动初始化编辑器

2. **AudioPlayerWidget**：继承自 `forms.URLInput`
   - 使用 HTML5 `<audio>` 元素
   - 自动检测音频 URL 并显示播放器
   - 无需额外的 JavaScript 库

3. **ImagePreviewWidget**：继承自 `forms.URLInput`
   - 使用 HTML5 `<img>` 元素
   - 自动检测图片 URL 并显示预览
   - 支持自定义预览图片尺寸
   - 包含错误处理机制
   - 使用 HTML5 `<audio>` 元素
   - 自动检测音频 URL 并显示播放器
   - 无需额外的 JavaScript 库

### Admin 表单定制

为每个需要自定义 Widget 的模型创建了对应的 ModelForm：

```python
# 示例：Article Admin
class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = "__all__"
        widgets = {
            "content": MarkdownEditorWidget(),
        }

class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    # ... 其他配置
```

## 使用方法

### 查看效果

1. 启动 Django 开发服务器：
   ```bash
   cd hinghwa-dict-backend
   python manage.py runserver
   ```

2. 访问 Admin 界面：`http://127.0.0.1:8000/admin/`

3. 编辑以下任一模型以查看自定义 Widget：
   - **文章**（Article）：在编辑页面会看到 Markdown 编辑器
   - **音乐**（Music）：在编辑页面会看到音频播放器
   - **词语**（Word）：在附注字段会看到 Markdown 编辑器
   - **语音**（Pronunciation）：在编辑页面会看到音频播放器

### Markdown 编辑器使用

- 点击工具栏按钮插入 Markdown 语法
- 点击"预览"按钮查看渲染效果
- 点击"并排"按钮同时查看编辑和预览
- 点击"全屏"按钮进入全屏编辑模式
- 使用 Markdown 语法编写内容，如：
  ```markdown
  # 标题
  **粗体** *斜体*
  - 列表项
  [链接](http://example.com)
  ![图片](http://example.com/image.jpg)
  ```

### 音频播放器使用

- 在 `source` 字段输入音频文件的 URL
- 保存后，页面会自动显示音频播放器
- 点击播放按钮即可播放音频
- 支持的音频格式：MP3、WAV、OGG

### 图片预览使用

- 在图片 URL 字段（如 `cover`、`avatar`）输入图片的 URL
- 保存后，页面会自动显示图片预览
- 如果图片加载失败，会显示友好的错误提示
- 支持的图片格式：JPG、PNG、GIF、WebP 等所有浏览器支持的格式

## 优势

1. **无缝集成**：完全集成在 Django Admin 中，无需离开 Admin 界面
2. **轻量级**：使用 CDN 加载资源，不增加项目体积
3. **易于扩展**：可以轻松为其他模型字段添加相同的功能
4. **用户友好**：提供直观的编辑和预览体验
5. **最小侵入**：仅修改需要自定义的 Admin 类，不影响其他功能

## 维护和扩展

### 为其他字段添加 Markdown 编辑器

```python
from utils.admin.widgets import MarkdownEditorWidget

class YourModelAdminForm(forms.ModelForm):
    class Meta:
        model = YourModel
        fields = "__all__"
        widgets = {
            "your_markdown_field": MarkdownEditorWidget(),
        }

class YourModelAdmin(admin.ModelAdmin):
    form = YourModelAdminForm
    # ... 其他配置
```

### 为其他字段添加音频播放器

```python
from utils.admin.widgets import AudioPlayerWidget

class YourModelAdminForm(forms.ModelForm):
    class Meta:
        model = YourModel
        fields = "__all__"
        widgets = {
            "your_audio_url_field": AudioPlayerWidget(),
        }

class YourModelAdmin(admin.ModelAdmin):
    form = YourModelAdminForm
    # ... 其他配置
```

### 为其他字段添加图片预览

```python
from utils.admin.widgets import ImagePreviewWidget

class YourModelAdminForm(forms.ModelForm):
    class Meta:
        model = YourModel
        fields = "__all__"
        widgets = {
            "your_image_url_field": ImagePreviewWidget(max_width=400, max_height=400),
        }

class YourModelAdmin(admin.ModelAdmin):
    form = YourModelAdminForm
    # ... 其他配置
```

## 依赖

- Django 5.0.3
- django-simpleui 2023.3.1（可选，用于增强 Admin 界面外观）
- EasyMDE（通过 CDN 加载）

## 许可证

与主项目相同
