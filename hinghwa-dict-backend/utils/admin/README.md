# Django Admin 自定义前端工具

## 概述

本项目为 Django Admin 添加了自定义前端工具，包括自定义 Widget（Markdown 编辑器、音频播放器、图片预览）和完整的审核工作流程，以增强内容编辑和管理体验。

## 功能特性

### 1. 自定义 Widget

#### Markdown 编辑器
为以下模型添加了 Markdown 编辑器（使用 EasyMDE v2.18.0）：
- **Article**: `content` 字段
- **Word**: `annotation` 字段  
- **Application**: `annotation` 字段

功能：实时预览、语法高亮、工具栏、全屏模式、并排预览、字数统计

#### 音频播放器
为以下模型添加了 HTML5 音频播放器：
- **Music**: `source` 字段
- **Pronunciation**: `source` 字段

功能：直接播放音频文件（MP3、WAV、OGG）、保留 URL 输入框

#### 图片预览
为以下模型添加了图片预览：
- **Article**: `cover` 字段（300x300px）
- **Music**: `cover` 字段（300x300px）
- **UserInfo**: `avatar` 字段（200x200px）

功能：自动显示图片、可配置尺寸、加载失败提示

### 2. 审核工作流程

#### Pronunciation（语音）审核
- **审核状态**：基于 `verifier` + `visibility` 字段
  - 待审核：`verifier=None`
  - 审核通过：`verifier存在 + visibility=True`
  - 审核不通过：`verifier存在 + visibility=False`
- **详情页功能**：
  - 显示当前审核状态和审核人
  - 审核理由输入框
  - "审核通过"/"审核不通过"按钮
  - 审核历史记录（显示所有相关通知）
  - 自动跳转到下一个待审核项
- **列表页功能**：
  - 自定义审核人筛选器（未审核/已审核全部/具体审核人）
- **通知**：审核操作会发送站内通知给贡献者，包含审核理由

#### Application（词条申请）审核
- **审核状态**：基于 `verifier` 字段
  - 待审核：`verifier=None`
  - 已审核：`verifier存在`
- **详情页功能**：同 Pronunciation
- **列表页功能**：同 Pronunciation
- **通知**：审核操作会发送站内通知给贡献者

#### Article（文章）审核
- **审核状态**：基于 `visibility` 字段
  - 待审核：`visibility=False`
  - 审核通过：`visibility=True`
- **详情页功能**：
  - 显示当前审核状态
  - 审核理由输入框
  - "审核通过"/"审核不通过"按钮
  - 审核历史记录
  - 自动跳转到下一个待审核文章
- **列表页功能**：
  - 是否审核筛选器
- **通知**：审核操作会发送站内通知给作者
- **批量操作**：支持批量审核通过/不通过（只对状态变化的项发送通知）

## 技术实现

### Widget 模块 (`utils/admin/widgets.py`)

```python
from utils.admin.widgets import MarkdownEditorWidget, AudioPlayerWidget, ImagePreviewWidget

# 使用示例
class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = "__all__"
        widgets = {
            "content": MarkdownEditorWidget(),
            "cover": ImagePreviewWidget(max_width=300, max_height=300),
        }
```

**Widget 实现**：
- `MarkdownEditorWidget`: 继承 `forms.Textarea`，通过 CDN 加载 EasyMDE
- `AudioPlayerWidget`: 继承 `forms.URLInput`，使用 HTML5 `<audio>` 元素
- `ImagePreviewWidget`: 继承 `forms.URLInput`，使用 HTML5 `<img>` 元素

### 审核功能实现

**通知集成**：
- Pronunciation: 使用 `action_object` 字段关联
- Application: 使用 `target` 字段关联
- Article: 使用 `action_object` 字段关联
- 审核历史通过查询 `notifications` 表获取

**自定义筛选器**：
```python
class VerifierListFilter(admin.SimpleListFilter):
    title = "审核人"
    parameter_name = "verifier_status"
    
    def lookups(self, request, model_admin):
        return [
            ("unreviewed", "未审核"),
            ("reviewed_all", "已审核（全部）"),
            # 动态添加所有审核人
        ]
```

**自动跳转逻辑**：
审核后查找下一个待审核项（`verifier__isnull=True` 或 `visibility=False`），如果有则跳转，否则返回列表页。

## 使用方法

### 启动服务
```bash
cd hinghwa-dict-backend
python manage.py runserver
```

访问：`http://127.0.0.1:8000/admin/`

### 审核工作流程

1. 在列表页使用筛选器选择"未审核"项
2. 点击进入详情页
3. 播放音频/查看内容/编辑字段
4. 在审核理由框输入审核意见
5. 点击"审核通过"或"审核不通过"按钮
6. 系统自动保存、发送通知、跳转到下一项
7. 重复步骤 3-6 直到完成所有审核

### API 集成（仅管理员）

管理员访问以下接口时会返回 `approval_history` 字段：
- `GET /word/pronunciation/{id}`
- `GET /word/application/{id}`
- `GET /article/{id}`

## 安全性

- 所有用户输入通过 `format_html()` 和 `escape()` 转义，防止 XSS
- JavaScript 变量正确转义
- EasyMDE 使用固定版本（v2.18.0），不使用 `@latest`
- 审核历史 API 仅对 `is_superuser=True` 的用户开放
- CodeQL 扫描：0 个安全漏洞

## 依赖

- Django 5.0.3
- django-notifications-hq 1.8.3
- django-simpleui 2023.3.1
- EasyMDE 2.18.0（CDN）
- Python 3.10-3.12

## 扩展指南

### 添加新的 Markdown 字段
```python
from utils.admin.widgets import MarkdownEditorWidget

class YourModelAdminForm(forms.ModelForm):
    class Meta:
        model = YourModel
        fields = "__all__"
        widgets = {
            "your_field": MarkdownEditorWidget(),
        }
```

### 添加新的审核模型

1. 确保模型有审核相关字段（`verifier` 和/或 `visibility`）
2. 创建自定义模板 `admin/{app}/{model}/change_form.html`
3. 在 Admin 类中添加审核方法：
```python
def approve_{model}(self, request, object_id):
    obj = self.get_object(request, object_id)
    approval_reason = request.POST.get("approval_reason", "")
    
    if not obj.visibility:  # 状态改变时
        obj.visibility = True
        obj.verifier = request.user
        obj.save()
        
        # 发送通知
        sendNotification(
            None,
            [obj.contributor],
            content=f"您的{model}(id={obj.id}) 已通过审核\n\n审核意见：{approval_reason}",
            action_object=obj,
            title="【通知】审核结果",
        )
    
    # 查找下一个待审核项并跳转
    next_obj = Model.objects.filter(verifier__isnull=True).first()
    if next_obj:
        return HttpResponseRedirect(f"../{next_obj.id}/change/")
    return HttpResponseRedirect("../")
```

## 许可证

与主项目相同
