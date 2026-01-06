# 词条和语音审核功能详细说明

## 概述

为 Pronunciation（语音）和 Application（词条申请）模型的详情页面添加了审核功能，实现了完整的审核工作流程。

## 功能特性

### 1. 审核状态显示

在编辑页面顶部显示当前审核状态：

#### Pronunciation（语音）
```
审核状态：
✓ 已通过审核 (审核人: admin)  或
⏳ 待审核
```

#### Application（词条申请）
```
审核状态：
✓ 已审核 (审核人: admin)  或
⏳ 待审核
```

### 2. 审核按钮

在保存按钮旁边添加审核操作按钮：

#### 待审核状态
- **✓ 审核通过** - 蓝色按钮，点击后：
  - 标记为已审核/可见
  - 设置审核人为当前用户
  - 发送通知给贡献者（Pronunciation）
  - 自动跳转到下一个待审核项目

#### 已审核状态
- **✗ 撤销审核** - 红色按钮，点击后：
  - 取消审核状态/标记为不可见
  - 清除审核人
  - 发送通知给贡献者（Pronunciation）
  - 自动跳转到下一个待审核项目

### 3. 自动跳转

点击审核按钮后，系统会：
1. 保存审核状态
2. 查找下一个待审核的项目
3. 自动跳转到下一个项目的编辑页面
4. 如果没有更多待审核项目，返回列表页面

这样可以实现快速连续审核工作流程。

## 审核工作流程

### 推荐的审核流程

#### 语音审核（Pronunciation）
1. 从列表页面筛选 `visibility=False` 的语音
2. 点击第一个待审核语音进入详情页
3. **播放音频** - 使用页面上的音频播放器
4. **查看内容** - 检查拼音、IPA、地理位置等信息
5. **修改校对** - 如有需要，直接在页面上修改
6. **点击"✓ 审核通过"** - 审核通过并自动跳转到下一个
7. 重复步骤 3-6，直到审核完所有待审核语音

#### 词条申请审核（Application）
1. 从列表页面筛选 `verifier=空` 的申请
2. 点击第一个待审核申请进入详情页
3. **查看内容** - 查看词条内容、定义、附注等
4. **编辑Markdown附注** - 使用Markdown编辑器编辑附注
5. **修改校对** - 如有需要，修改相关字段
6. **点击"✓ 审核通过"** - 审核通过并自动跳转到下一个
7. 重复步骤 3-6，直到审核完所有待审核申请

### 按钮行为

#### "保存"按钮
- 保存当前修改
- 停留在当前页面
- 不改变审核状态

#### "保存并继续编辑"按钮
- 保存当前修改
- 刷新当前页面
- 不改变审核状态

#### "保存并新增"按钮
- 保存当前修改
- 跳转到新建页面
- 不改变审核状态

#### "✓ 审核通过"按钮
- 保存当前修改
- 标记为已审核/可见
- 发送通知（Pronunciation）
- **自动跳转到下一个待审核项目**

#### "✗ 撤销审核"按钮
- 保存当前修改
- 取消审核状态
- 发送通知（Pronunciation）
- **自动跳转到下一个待审核项目**

## 技术实现

### 自定义模板

创建了两个自定义的 Django Admin 模板：

1. `word/templates/admin/word/pronunciation/change_form.html`
2. `word/templates/admin/word/application/change_form.html`

这些模板扩展了 Django 默认的 `admin/change_form.html`，在底部提交按钮区域添加了：
- 审核状态显示
- 审核通过按钮
- 撤销审核按钮

### 后端逻辑

在 Admin 类中实现了 `response_change()` 方法来处理自定义按钮：

```python
class PronunciationAdmin(admin.ModelAdmin):
    change_form_template = "admin/word/pronunciation/change_form.html"
    
    def response_change(self, request, obj):
        """Handle custom approval buttons on the change form."""
        if "_approve" in request.POST:
            # 处理审核通过
            obj.visibility = True
            obj.verifier = request.user
            obj.save()
            # 发送通知
            # 跳转到下一个
        elif "_reject" in request.POST:
            # 处理撤销审核
            obj.visibility = False
            obj.verifier = None
            obj.save()
            # 跳转到下一个
        return super().response_change(request, obj)
```

### 智能跳转

实现了 `_get_next_*_redirect()` 方法来查找下一个待审核项目：

```python
def _get_next_pronunciation_redirect(self, request, obj):
    """Redirect to the next pending pronunciation for review."""
    # 查找下一个 visibility=False 的语音
    next_pronunciation = Pronunciation.objects.filter(
        visibility=False,
        id__gt=obj.id
    ).order_by('id').first()
    
    if next_pronunciation:
        # 跳转到下一个
        url = reverse('admin:word_pronunciation_change', args=[next_pronunciation.pk])
        return HttpResponseRedirect(url)
    else:
        # 没有更多待审核项，返回列表
        url = reverse('admin:word_pronunciation_changelist')
        return HttpResponseRedirect(url)
```

## 与列表页批量操作的对比

### 列表页批量操作（已有）
- **优点**：可以同时审核多个项目
- **缺点**：无法查看详细内容、播放音频、编辑修改

### 详情页单个审核（新增）
- **优点**：
  - 可以查看完整内容
  - 可以播放音频（Pronunciation）
  - 可以编辑和修改
  - 可以使用Markdown编辑器（Application）
  - 自动跳转到下一个，提高效率
- **缺点**：一次只能审核一个

### 推荐使用场景

- **快速批量审核**：使用列表页的批量操作
- **仔细审核并修改**：使用详情页的单个审核
- **混合使用**：先用列表页快速筛选，再用详情页逐个审核

## 通知功能

### Pronunciation 审核通知

#### 审核通过时
```
标题：【通知】语音审核结果
内容：恭喜您的语音(id=123) 已通过审核
```

#### 审核撤销时
```
标题：【通知】语音审核结果
内容：很遗憾，您的语音(id=123) 审核已被撤销
```

### Application 审核通知

Application 目前没有配置通知功能，可以根据需要添加。

## 界面展示

### Pronunciation 编辑页面

```
┌─────────────────────────────────────────────────────────────┐
│ Pronunciation #123                                          │
├─────────────────────────────────────────────────────────────┤
│ 词语: [选择词语]                                           │
│ 来源: https://example.com/audio.mp3                        │
│ [🔊 音频播放器]                                            │
│ 拼音: [输入框]                                             │
│ IPA: [输入框]                                              │
│ 县区: [输入框]                                             │
│ ... 其他字段 ...                                           │
├─────────────────────────────────────────────────────────────┤
│ 审核状态: ⏳ 待审核                                        │
│                                                             │
│ [保存] [保存并继续编辑] [保存并新增]                        │
│ [✓ 审核通过] [删除]                                        │
└─────────────────────────────────────────────────────────────┘
```

### Application 编辑页面

```
┌─────────────────────────────────────────────────────────────┐
│ Application #456                                            │
├─────────────────────────────────────────────────────────────┤
│ 关联词条: [选择词条]                                       │
│ 理由: [输入框]                                             │
│ 词: [输入框]                                               │
│ 注释: [文本框]                                             │
│ 附注: [Markdown编辑器]                                     │
│ ... 其他字段 ...                                           │
├─────────────────────────────────────────────────────────────┤
│ 审核状态: ⏳ 待审核                                        │
│                                                             │
│ [保存] [保存并继续编辑] [保存并新增]                        │
│ [✓ 审核通过] [删除]                                        │
└─────────────────────────────────────────────────────────────┘
```

## 键盘快捷键建议

虽然当前版本没有实现键盘快捷键，但可以考虑在未来版本添加：

- `Alt+A` - 审核通过
- `Alt+R` - 撤销审核
- `Alt+S` - 保存
- `Alt+N` - 跳转到下一个

## 数据库字段说明

### Pronunciation 模型
- `visibility` (Boolean) - 是否可见/通过审核
  - `False` = 待审核
  - `True` = 已通过审核
- `verifier` (ForeignKey) - 审核人
  - `None` = 未审核
  - User对象 = 已审核，显示审核人

### Application 模型
- `verifier` (ForeignKey) - 审核人
  - `None` = 待审核
  - User对象 = 已审核，显示审核人

## 筛选待审核项目

### 在列表页筛选

#### Pronunciation
右侧筛选器：
- `是否可见` → 选择 `否`

或在搜索栏使用高级筛选（如果可用）

#### Application
右侧筛选器：
- `审核人` → 选择 `---------`（空值）

## 总结

新的审核功能提供了：
1. ✅ 在详情页面直接查看审核状态
2. ✅ 在详情页面直接修改审核状态
3. ✅ 播放音频后立即审核（Pronunciation）
4. ✅ 编辑Markdown后立即审核（Application）
5. ✅ 自动跳转到下一个待审核项目
6. ✅ 发送审核通知（Pronunciation）
7. ✅ 符合人类操作习惯的工作流程

这完全满足了"点击具体一个语音，播放语音内容，然后修改、校对，然后点击审核通过，然后保存，然后找到下一个待审核的语音继续审核"的需求！
