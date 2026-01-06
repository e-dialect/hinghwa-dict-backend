# Django Admin 图片预览功能演示

## 功能说明

已为以下模型的图片 URL 字段添加了图片预览功能：

### 1. 文章封面 (Article.cover)
在文章编辑页面，`cover` 字段会显示：
- URL 输入框（用于输入或编辑图片 URL）
- 图片预览（最大宽度 300px，最大高度 300px）
- 美观的边框和圆角样式
- 错误处理（如果图片加载失败会显示提示）

```
┌─────────────────────────────────────────────────┐
│ 图片地址: *                                     │
├─────────────────────────────────────────────────┤
│ https://example.com/article-cover.jpg           │
├─────────────────────────────────────────────────┤
│ 图片预览:                                       │
│ ┌───────────────────────────────────────────┐   │
│ │                                           │   │
│ │         [文章封面图片预览]                 │   │
│ │                                           │   │
│ │      (最大 300x300px)                     │   │
│ │                                           │   │
│ └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 2. 音乐封面 (Music.cover)
在音乐编辑页面，`cover` 字段会显示类似的图片预览。

```
┌─────────────────────────────────────────────────┐
│ 音乐封面地址: *                                 │
├─────────────────────────────────────────────────┤
│ https://example.com/music-cover.jpg             │
├─────────────────────────────────────────────────┤
│ 图片预览:                                       │
│ ┌───────────────────────────────────────────┐   │
│ │                                           │   │
│ │         [音乐封面图片预览]                 │   │
│ │                                           │   │
│ │      (最大 300x300px)                     │   │
│ │                                           │   │
│ └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 3. 用户头像 (UserInfo.avatar)
在用户信息编辑页面，`avatar` 字段会显示：
- URL 输入框
- 头像预览（最大宽度 200px，最大高度 200px）
- 更小的尺寸适合头像显示

```
┌─────────────────────────────────────────────────┐
│ 头像: *                                         │
├─────────────────────────────────────────────────┤
│ https://example.com/user-avatar.jpg             │
├─────────────────────────────────────────────────┤
│ 图片预览:                                       │
│ ┌─────────────────────────────┐                 │
│ │                             │                 │
│ │    [用户头像图片预览]        │                 │
│ │                             │                 │
│ │    (最大 200x200px)         │                 │
│ │                             │                 │
│ └─────────────────────────────┘                 │
└─────────────────────────────────────────────────┘
```

## 技术特点

### 1. 安全性
- 所有 URL 都经过 HTML 转义，防止 XSS 攻击
- 使用 Django 的 `format_html()` 和 `escape()` 函数

### 2. 错误处理
- 使用 `onerror` 事件处理图片加载失败
- 加载失败时隐藏图片，显示友好提示信息
- 提示信息："图片加载失败或URL无效"

### 3. 响应式设计
- 可配置最大宽度和高度
- 图片自动缩放以适应限制
- 保持图片原始宽高比

### 4. 美观样式
- 1px 灰色边框
- 4px 圆角
- 5px 内边距
- 10px 上边距（与 URL 输入框保持距离）
- 块级元素显示

## 实现代码

### ImagePreviewWidget 类

```python
class ImagePreviewWidget(forms.URLInput):
    """
    A custom widget that displays an image preview for image URL fields.
    Shows both the URL input field and a preview of the image.
    """

    def __init__(self, attrs=None, max_width=300, max_height=300):
        default_attrs = {"class": "vURLField"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
        self.max_width = max_width
        self.max_height = max_height

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)

        # Add image preview if there's a value
        if value:
            escaped_value = escape(value)
            image_preview = format_html(
                """
            <div style="margin-top: 10px;">
                <img src="{}" alt="{}" style="max-width: {}px; max-height: {}px; border: 1px solid #ddd; border-radius: 4px; padding: 5px; display: block;" 
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                <p style="display: none; color: #666; font-style: italic;">{}</p>
            </div>
            """,
                escaped_value,
                _("图片预览"),
                self.max_width,
                self.max_height,
                _("图片加载失败或URL无效"),
            )
            html = html + image_preview

        return mark_safe(html)
```

### 使用示例

#### Article Admin
```python
from utils.admin.widgets import MarkdownEditorWidget, ImagePreviewWidget

class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = "__all__"
        widgets = {
            "content": MarkdownEditorWidget(),
            "cover": ImagePreviewWidget(),
        }
```

#### Music Admin
```python
from utils.admin.widgets import AudioPlayerWidget, ImagePreviewWidget

class MusicAdminForm(forms.ModelForm):
    class Meta:
        model = Music
        fields = "__all__"
        widgets = {
            "source": AudioPlayerWidget(),
            "cover": ImagePreviewWidget(),
        }
```

#### UserInfo Admin
```python
from utils.admin.widgets import ImagePreviewWidget

class UserInfoAdminForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = "__all__"
        widgets = {
            "avatar": ImagePreviewWidget(max_width=200, max_height=200),
        }
```

## 审核操作

所有带有 `visibility` 字段的模型（Article、Music、Word、Pronunciation）都已经配置了审核操作：

### 现有的审核动作

1. **"所选 XX 通过审核"** (`pass_visibility`)
   - 批量将选中项目标记为可见
   - 发送通知给贡献者（Pronunciation）
   - 显示成功消息

2. **"所选 XX 不通过审核"** (`withdraw_visibility`)
   - 批量将选中项目标记为不可见
   - 发送通知给贡献者（Pronunciation）
   - 显示成功消息

### 使用方法

1. 在列表页面选择要审核的项目（勾选复选框）
2. 在"操作"下拉菜单中选择：
   - "所选 XX 通过审核"
   - "所选 XX 不通过审核"
3. 点击"执行"按钮
4. 系统会显示操作结果和影响的记录数

### 示例：Pronunciation Admin

```python
class PronunciationAdmin(admin.ModelAdmin):
    actions = ["pass_visibility", "withdraw_visibility"]
    
    def pass_visibility(self, request, queryset):
        for pro in queryset:
            if not pro.visibility:
                # 发送审核通过通知
                content = f"恭喜您的语音(id={pro.id}) 已通过审核"
                sendNotification(...)
            pro.visibility = True
            pro.verifier_id = 2
            pro.save()
        # 显示成功消息
        self.message_user(request, f"{updated} 个语音被成功标记为可见。")
    
    pass_visibility.short_description = "所选 发音 通过审核"
```

## 与前端审核工具的一致性

后台的审核操作与前端审核页面保持一致：
- ✅ 同样的 `visibility` 字段控制
- ✅ 同样的审核通过/不通过逻辑
- ✅ 同样的通知机制
- ✅ 批量操作支持

这确保了管理员无论在后台还是前端工具中审核，体验都是一致的。

## 浏览器兼容性

### 图片预览
- ✅ Chrome/Edge (所有版本)
- ✅ Firefox (所有版本)
- ✅ Safari (所有版本)
- ✅ IE 11+

### 图片格式支持
- ✅ JPEG/JPG
- ✅ PNG
- ✅ GIF (静态和动态)
- ✅ WebP (现代浏览器)
- ✅ SVG
- ✅ BMP

## 最佳实践

1. **图片大小**：建议上传适当大小的图片，避免过大导致加载缓慢
2. **URL 格式**：使用完整的 HTTP/HTTPS URL
3. **CORS**：确保图片服务器允许跨域访问
4. **错误处理**：预览失败不影响保存，只是显示提示
5. **尺寸配置**：根据用途调整 `max_width` 和 `max_height`
   - 头像：200x200
   - 封面：300x300 或更大
   - 缩略图：150x150

## 总结

图片预览功能提供了：
- 📷 直观的图片预览
- 🔒 安全的 URL 处理
- 🎨 美观的界面样式
- 🛡️ 完善的错误处理
- ✅ 审核操作已完善配置

管理员可以在编辑页面直接看到图片效果，无需打开新标签页查看，大大提升了工作效率！
