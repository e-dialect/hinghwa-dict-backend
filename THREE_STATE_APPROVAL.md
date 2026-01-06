# 三状态审核系统说明

## 概述

系统现在支持三种审核状态，而不仅仅是两种（已审核/未审核）。这样可以明确区分"还没审核"和"审核不通过"两种情况。

## 三种审核状态

### 1. pending（待审核）⏳
- **含义**: 提交后还没有被审核
- **显示**: 橙色 "⏳ 待审核"
- **特点**: 
  - 这是默认状态
  - `verifier` 字段为空
  - `visibility` = False（Pronunciation）

### 2. approved（审核通过）✓
- **含义**: 已审核并通过
- **显示**: 绿色 "✓ 审核通过 (审核人: xxx)"
- **特点**:
  - `verifier` 字段记录审核人
  - `visibility` = True（Pronunciation）
  - 内容对外可见

### 3. rejected（审核不通过）✗
- **含义**: 已审核但不通过
- **显示**: 红色 "✗ 审核不通过 (审核人: xxx)"
- **特点**:
  - `verifier` 字段记录审核人
  - `visibility` = False（Pronunciation）
  - 内容不对外可见
  - **区别于pending**: 明确表示已经审核过但不合格

## 数据库字段

### Pronunciation 模型
```python
approval_status = CharField(
    max_length=20,
    choices=[
        ('pending', '待审核'),
        ('approved', '审核通过'),
        ('rejected', '审核不通过'),
    ],
    default='pending',
    verbose_name='审核状态'
)
```

### Application 模型
```python
approval_status = CharField(
    max_length=20,
    choices=[
        ('pending', '待审核'),
        ('approved', '审核通过'),
        ('rejected', '审核不通过'),
    ],
    default='pending',
    verbose_name='审核状态'
)
```

## 列表页面筛选

### 按审核状态筛选

在列表页面右侧的筛选器中，现在可以按 **审核状态** 进行筛选：

#### Pronunciation 列表
筛选选项：
- `审核状态` → 选择：
  - `待审核` - 显示所有等待审核的语音
  - `审核通过` - 显示所有通过审核的语音
  - `审核不通过` - 显示所有被拒绝的语音

同时还可以按以下条件筛选：
- `是否可见` - 兼容旧的筛选方式
- `贡献者`
- `县区`

#### Application 列表
筛选选项：
- `审核状态` → 选择：
  - `待审核` - 显示所有等待审核的申请
  - `审核通过` - 显示所有通过审核的申请
  - `审核不通过` - 显示所有被拒绝的申请

同时还可以按以下条件筛选：
- `贡献者`
- `审核人`
- `关联词条`

### 组合筛选示例

**查找待审核的语音**:
- `审核状态` = `待审核`

**查找被某个审核人拒绝的申请**:
- `审核状态` = `审核不通过`
- `审核人` = 选择特定审核人

**查找已通过但不可见的语音**（异常情况）:
- `审核状态` = `审核通过`
- `是否可见` = `否`

## 详情页面

### 审核状态显示

在编辑页面顶部会显示当前的审核状态：

```
┌─────────────────────────────────────────┐
│ 审核状态: ⏳ 待审核                     │  ← 橙色，表示还没审核
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 审核状态: ✓ 审核通过 (审核人: admin)   │  ← 绿色，表示通过
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 审核状态: ✗ 审核不通过 (审核人: admin) │  ← 红色，表示不通过
└─────────────────────────────────────────┘
```

### 审核按钮

根据当前状态，显示不同的按钮：

#### 状态 = pending（待审核）
显示两个按钮：
- `✓ 审核通过` - 蓝色按钮
- `✗ 审核不通过` - 红色按钮

#### 状态 = approved（审核通过）
显示一个按钮：
- `✗ 审核不通过` - 红色按钮（可以改为不通过）

#### 状态 = rejected（审核不通过）
显示一个按钮：
- `✓ 审核通过` - 蓝色按钮（可以改为通过）

**注意**: 任何状态都可以切换到另一个状态，提供了灵活的审核流程。

## 审核工作流程

### 场景1：正常审核流程

1. **用户提交** → 状态 = `pending`（待审核）
2. **审核人查看** → 播放音频/查看内容
3. **审核决定**：
   - 点击 `✓ 审核通过` → 状态 = `approved`
   - 点击 `✗ 审核不通过` → 状态 = `rejected`
4. **自动跳转** → 下一个 `pending` 状态的项目

### 场景2：修改审核结果

1. **当前状态** = `approved`（审核通过）
2. **发现问题** → 需要改为不通过
3. **点击** `✗ 审核不通过` → 状态 = `rejected`
4. **通知发送** → 贡献者收到审核不通过通知

### 场景3：重新审核

1. **当前状态** = `rejected`（审核不通过）
2. **用户修改后** → 需要重新审核
3. **点击** `✓ 审核通过` → 状态 = `approved`
4. **通知发送** → 贡献者收到审核通过通知

## 通知系统

### Pronunciation（语音）

#### 审核通过
```
标题：【通知】语音审核结果
内容：恭喜您的语音(id=123) 已通过审核
```

#### 审核不通过
```
标题：【通知】语音审核结果
内容：很遗憾，您的语音(id=123) 未通过审核
```

### Application（词条申请）

目前 Application 没有配置通知功能，但保留了扩展接口。

## 自动跳转逻辑

点击审核按钮后，系统会：

1. 保存当前项目的审核状态
2. 查找下一个 `approval_status='pending'` 的项目
3. 按 ID 升序排序
4. 如果找到，跳转到该项目的编辑页面
5. 如果没有更多待审核项目，返回列表页面

**关键点**: 只查找 `pending` 状态的项目，不会跳转到 `rejected` 的项目。

## 与旧系统的兼容性

### Pronunciation
- 保留 `visibility` 字段用于兼容性
- `approved` 状态时 `visibility=True`
- `pending` 或 `rejected` 状态时 `visibility=False`

### 旧的批量操作
列表页面的批量操作（"所选 XX 通过审核"等）仍然可用，但建议使用新的三状态系统。

## 数据迁移

### 迁移文件
`word/migrations/0011_add_approval_status.py`

### 默认值
新字段的默认值为 `'pending'`（待审核）

### 现有数据
运行迁移后，所有现有记录的 `approval_status` 将被设置为 `'pending'`。
如果需要，可以根据 `visibility` 或 `verifier` 字段更新历史数据。

### 更新历史数据的建议脚本

```python
# 在 Django shell 中运行
from word.models import Pronunciation, Application

# 更新 Pronunciation
for p in Pronunciation.objects.all():
    if p.visibility and p.verifier:
        p.approval_status = 'approved'
        p.save()
    elif not p.visibility and p.verifier:
        # 假设有审核人但不可见 = 不通过
        p.approval_status = 'rejected'
        p.save()
    # else: 保持 pending

# 更新 Application  
for a in Application.objects.all():
    if a.verifier:
        # 假设有审核人 = 通过（可根据实际情况调整）
        a.approval_status = 'approved'
        a.save()
    # else: 保持 pending
```

## 列表显示

### list_display 字段

#### Pronunciation
```python
list_display = [
    "id",
    "word",
    "pinyin",
    "ipa",
    "contributor",
    "county",
    "views",
    "approval_status",  # 新增：审核状态
    "visibility",       # 保留：兼容性
    "granted",
    "verifier",
]
```

#### Application
```python
list_display = [
    "id",
    "word",
    "reason",
    "contributor",
    "approval_status",  # 新增：审核状态
    "granted",
    "verifier",
]
```

### 显示效果

在列表中，`approval_status` 列会显示：
- `待审核` - 橙色标记
- `审核通过` - 绿色标记
- `审核不通过` - 红色标记

## 最佳实践

### 1. 审核流程
- 使用 `待审核` 筛选器找到需要审核的项目
- 逐个审核，使用 `✓ 审核通过` 或 `✗ 审核不通过`
- 利用自动跳转功能提高效率

### 2. 质量控制
- `审核不通过` 不是删除，而是标记为不合格
- 允许贡献者看到反馈并改进
- 可以重新审核之前被拒绝的项目

### 3. 数据分析
- 统计各状态的数量
- 分析审核通过率
- 识别需要改进的领域

## 技术细节

### 字段定义
```python
APPROVAL_STATUS_CHOICES = [
    ('pending', '待审核'),
    ('approved', '审核通过'),
    ('rejected', '审核不通过'),
]
```

### 状态转换矩阵

| 当前状态 | 可转换到 | 操作 |
|---------|---------|------|
| pending | approved | 点击 "✓ 审核通过" |
| pending | rejected | 点击 "✗ 审核不通过" |
| approved | rejected | 点击 "✗ 审核不通过" |
| rejected | approved | 点击 "✓ 审核通过" |

所有转换都会：
1. 更新 `approval_status` 字段
2. 设置 `verifier` 为当前用户
3. 更新 `visibility`（Pronunciation）
4. 发送通知（Pronunciation）
5. 跳转到下一个待审核项

## 总结

三状态审核系统提供了：
- ✅ **明确的状态区分**: pending vs rejected
- ✅ **灵活的筛选**: 按审核状态筛选
- ✅ **完整的工作流**: 审核、拒绝、重审
- ✅ **详细的记录**: 审核人和审核结果
- ✅ **自动化流程**: 自动跳转到下一个
- ✅ **向后兼容**: 保留旧字段和功能

这个系统更符合实际的审核需求，能够区分"还没审核"和"审核不通过"两种完全不同的情况！
