# Django Admin 自定义工具 - 使用指南

## 快速开始

### 1. 查看 Markdown 编辑器

#### 编辑文章（Article）
1. 访问 Django Admin: `http://127.0.0.1:8000/admin/`
2. 点击 "文章" (Article)
3. 点击 "新增文章" 或编辑现有文章
4. 在 "正文" (content) 字段，你会看到 Markdown 编辑器

**预期效果**：
```
┌─────────────────────────────────────────────────┐
│ 正文: ▼                                         │
├─────────────────────────────────────────────────┤
│ [B] [I] [H] │ " ≡ 1. │ 🔗 📷 │ 👁 ↔ ⛶ │ ? │
├─────────────────────────────────────────────────┤
│ # 标题                                          │
│                                                 │
│ **粗体文本** *斜体文本*                         │
│                                                 │
│ - 列表项 1                                      │
│ - 列表项 2                                      │
│                                                 │
│ [链接文字](http://example.com)                 │
│                                                 │
├─────────────────────────────────────────────────┤
│ Lines: 7 | Words: 10 | Cursor: 7:1            │
└─────────────────────────────────────────────────┘
```

**工具栏功能**：
- `[B]` = 粗体
- `[I]` = 斜体
- `[H]` = 标题
- `"` = 引用
- `≡` = 无序列表
- `1.` = 有序列表
- `🔗` = 插入链接
- `📷` = 插入图片
- `👁` = 预览模式
- `↔` = 并排预览
- `⛶` = 全屏编辑
- `?` = Markdown 指南

#### 编辑词语附注（Word.annotation）
1. 访问 "词语" (Word)
2. 编辑任意词语
3. 在 "附注" (annotation) 字段看到相同的 Markdown 编辑器

#### 编辑词语修改申请（Application.annotation）
1. 访问 "词语修改申请" (Application)
2. 编辑任意申请
3. 在 "附注" (annotation) 字段看到相同的 Markdown 编辑器

### 2. 查看音频播放器

#### 编辑音乐（Music）
1. 访问 "音乐" (Music)
2. 点击 "新增音乐" 或编辑现有音乐
3. 在 "音乐地址" (source) 字段输入音频 URL

**预期效果**：
```
┌─────────────────────────────────────────────────┐
│ 音乐地址: *                                     │
├─────────────────────────────────────────────────┤
│ https://example.com/music.mp3                   │
├─────────────────────────────────────────────────┤
│ 音频预览:                                       │
│ ┌─────────────────────────────────────────────┐ │
│ │ ▶ ━━━━━━━━━━━━━━━━━━━━━ 0:00 / 3:45  🔊    │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**功能**：
- `▶/⏸` = 播放/暂停
- 进度条 = 拖动到指定位置
- 时间显示 = 当前时间 / 总时长
- `🔊` = 音量控制

#### 编辑语音（Pronunciation）
1. 访问 "语音" (Pronunciation)
2. 编辑任意语音
3. 在 "来源" (source) 字段输入音频 URL
4. 看到相同的音频播放器

## Markdown 编辑器详细功能

### 基础编辑

#### 标题
```markdown
# 一级标题
## 二级标题
### 三级标题
```

#### 文本样式
```markdown
**粗体文本**
*斜体文本*
~~删除线~~
```

#### 列表
```markdown
无序列表：
- 项目 1
- 项目 2
  - 子项目 2.1
  - 子项目 2.2

有序列表：
1. 第一项
2. 第二项
3. 第三项
```

#### 链接和图片
```markdown
[链接文字](http://example.com)
![图片描述](http://example.com/image.jpg)
```

#### 引用
```markdown
> 这是一段引用文本
> 可以多行
```

#### 代码
```markdown
行内代码: `code`

代码块:
```python
def hello():
    print("Hello World")
```
```

### 高级功能

#### 预览模式
点击 `👁` (预览) 按钮：
- 左侧：Markdown 源码
- 右侧：渲染后的效果

#### 并排模式
点击 `↔` (并排) 按钮：
- 同时显示编辑和预览
- 实时看到渲染效果
- 滚动同步

#### 全屏模式
点击 `⛶` (全屏) 按钮：
- 专注编辑模式
- 最大化编辑空间
- 按 ESC 退出

#### 状态栏信息
底部显示：
- `Lines: 10` - 总行数
- `Words: 50` - 字数统计
- `Cursor: 5:10` - 光标位置（行:列）

## 音频播放器详细功能

### 支持的格式
- MP3 (`.mp3`) - 最常用
- WAV (`.wav`) - 无损音频
- OGG (`.ogg`) - 开源格式

### 播放控制

#### 基本控制
- **播放/暂停**: 点击 ▶/⏸ 按钮
- **进度控制**: 拖动进度条
- **音量调节**: 点击 🔊 图标，拖动音量滑块

#### 键盘快捷键（浏览器原生）
- `空格键` - 播放/暂停
- `←/→` - 后退/快进
- `↑/↓` - 增加/减少音量

### URL 输入
输入音频文件的完整 URL，例如：
```
https://example.com/audio/sample.mp3
https://cdn.example.com/music/song.wav
http://localhost:8000/media/pronunciation/test.mp3
```

**注意事项**：
- URL 必须可公开访问
- 确保 CORS 配置允许跨域访问
- 支持相对 URL（如果音频文件在同一域名下）

## 使用技巧

### Markdown 编辑器技巧

1. **快速插入**：使用工具栏按钮快速插入 Markdown 语法
2. **键盘快捷键**：
   - `Ctrl+B` - 粗体
   - `Ctrl+I` - 斜体
   - `Ctrl+K` - 插入链接
3. **拖放图片**：直接拖放图片到编辑器（如果配置了图片上传）
4. **自动保存**：Django Admin 会在提交时保存内容

### 音频播放器技巧

1. **测试音频**：保存前先播放测试音频是否正常
2. **使用相对路径**：如果音频存储在项目 media 目录，使用相对路径
3. **格式转换**：推荐使用 MP3 格式以获得最佳兼容性
4. **文件大小**：注意音频文件大小，避免加载过慢

## 常见问题

### Markdown 编辑器

**Q: 为什么看不到 Markdown 编辑器？**
A: 确保：
1. JavaScript 已启用
2. 网络可以访问 CDN (jsdelivr.net)
3. 浏览器支持现代 JavaScript

**Q: 如何插入表格？**
A: Markdown 表格语法：
```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 内容1 | 内容2 | 内容3 |
| 内容4 | 内容5 | 内容6 |
```

**Q: 预览样式和实际显示不同？**
A: 预览使用 EasyMDE 的默认样式。实际显示取决于前端应用的 CSS 样式。

### 音频播放器

**Q: 为什么音频无法播放？**
A: 检查：
1. URL 是否正确
2. 音频文件是否存在
3. 服务器是否允许跨域访问（CORS）
4. 音频格式是否被浏览器支持

**Q: 可以上传本地音频文件吗？**
A: 需要先上传音频文件到服务器或 CDN，然后在 source 字段输入 URL。

**Q: 为什么只有 URL 输入框没有播放器？**
A: 播放器只在保存后且 URL 有效时显示。先保存记录，再编辑即可看到播放器。

## 扩展自定义

### 为其他模型添加 Markdown 编辑器

在你的 `admin.py` 中：

```python
from django import forms
from utils.admin.widgets import MarkdownEditorWidget
from .models import YourModel

class YourModelAdminForm(forms.ModelForm):
    class Meta:
        model = YourModel
        fields = "__all__"
        widgets = {
            "your_text_field": MarkdownEditorWidget(),
        }

class YourModelAdmin(admin.ModelAdmin):
    form = YourModelAdminForm
    # ... 其他配置

admin.site.register(YourModel, YourModelAdmin)
```

### 为其他模型添加音频播放器

```python
from django import forms
from utils.admin.widgets import AudioPlayerWidget
from .models import YourModel

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

admin.site.register(YourModel, YourModelAdmin)
```

## 性能优化建议

### Markdown 编辑器
- 对于超大文本（>100KB），考虑分页或分块编辑
- 关闭不需要的工具栏按钮以简化界面
- 如果频繁编辑，可以考虑本地缓存 EasyMDE

### 音频播放器
- 使用 `preload="metadata"` 只预加载元数据，不预加载整个文件
- 对于大文件，考虑使用流式播放服务
- 使用 CDN 加速音频文件访问

## 安全注意事项

### 已实施的安全措施
✅ 所有用户输入都经过 HTML 转义
✅ 使用 Django 的 `format_html` 防止 XSS 攻击
✅ JavaScript 中的变量经过转义
✅ CDN 资源使用固定版本（避免供应链攻击）

### 使用建议
- 只允许受信任的用户访问 Admin 界面
- 定期更新 EasyMDE 版本（在 `widgets.py` 中更新 CDN URL）
- 为音频文件设置合理的访问权限
- 使用 HTTPS 传输音频和其他媒体文件

## 浏览器兼容性

### Markdown 编辑器
- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+

### 音频播放器
- ✅ Chrome 4+
- ✅ Firefox 3.5+
- ✅ Safari 4+
- ✅ Edge (所有版本)
- ⚠️ IE 11 (部分功能)

## 获取帮助

- 查看 `utils/admin/README.md` 了解技术细节
- 查看 `DEPENDENCIES.md` 了解依赖和兼容性
- 查看 `IMPLEMENTATION_SUMMARY.md` 了解实现细节
- 运行 `python test_admin_widgets.py` 测试配置

## 更新日志

### 版本 1.0.0 (2024-01-06)
- ✅ 实现 Markdown 编辑器（基于 EasyMDE 2.18.0）
- ✅ 实现音频播放器（HTML5）
- ✅ 应用于 Article、Word、Application、Music、Pronunciation 模型
- ✅ 修复安全漏洞（XSS、脚本注入）
- ✅ 添加国际化支持
- ✅ 完善文档和测试
