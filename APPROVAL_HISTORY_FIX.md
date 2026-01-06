# Approval History Fix Documentation

## Problem

The approval history was not displaying existing notifications from the database in the Django admin interface. This was because the notification query was using incorrect field names.

## Root Cause Analysis

After analyzing the existing approval code in the codebase, I discovered that different models use different fields to link notifications:

### Pronunciation Model
In `word/pronunciation/views.py`, when sending approval notifications:
```python
sendNotification(
    verifier,
    [contributor],
    content=content + reason,
    action_object=pronunciation,  # Uses action_object parameter
    title=f"【通知】语音（{pronunciation.word.word}）审核结果",
)
```

This means Pronunciation notifications are stored with:
- `action_content_type` = ContentType of Pronunciation model
- `action_object_id` = Pronunciation instance ID

### Application Model
In `word/application/views.py`, when sending approval notifications:
```python
sendNotification(
    None,
    [application.contributor],
    content,
    target=application,  # Uses target parameter
    title=title,
    action_object=application.word,
)
```

This means Application notifications are stored with:
- `target_content_type` = ContentType of Application model
- `target_object_id` = Application instance ID

## Solution

### 1. Admin Interface Fix

#### PronunciationAdmin (`word/admin.py`)
```python
def get_approval_notifications(self, obj):
    """Get all approval-related notifications for this pronunciation."""
    from notifications.models import Notification
    from django.contrib.contenttypes.models import ContentType

    ct = ContentType.objects.get_for_model(obj)
    # Query using action_object fields (matching pronunciation/views.py)
    notifications = Notification.objects.filter(
        action_content_type=ct, action_object_id=obj.id, verb__icontains="审核"
    ).order_by("-timestamp")

    return notifications
```

#### ApplicationAdmin (`word/admin.py`)
```python
def get_approval_notifications(self, obj):
    """Get approval-related notifications for this application."""
    from notifications.models import Notification
    from django.contrib.contenttypes.models import ContentType

    ct = ContentType.objects.get_for_model(obj)
    # For Application, notifications use target (matching application/views.py)
    notifications = Notification.objects.filter(
        target_content_type=ct, target_object_id=obj.id, verb__icontains="审核"
    ).order_by("-timestamp")

    return notifications
```

### 2. Consistent Notification Sending

Updated all new approval code to use the same field as existing code:

#### Pronunciation Approval Buttons
```python
sendNotification(
    None,
    [obj.contributor],
    content=content,
    action_object=obj,  # Consistent with existing code
    title="【通知】语音审核结果",
)
```

#### Pronunciation Batch Actions
```python
def pass_visibility(self, request, queryset):
    for pro in queryset:
        if not pro.visibility:
            content = f"恭喜您的语音(id={pro.id}) 已通过审核"
            sendNotification(
                None,
                [pro.contributor],
                content=content,
                action_object=pro,  # Consistent with existing code
                title="【通知】语音审核结果",
            )
```

### 3. API Enhancement (Admin Only)

Added approval history to detail endpoints for admin users:

#### Pronunciation Detail API (`word/pronunciation/views.py`)
```python
# PN0101 获取发音信息
def get(self, request, id):
    pronunciation = get_pronunciation_by_id(id)
    pronunciation.views += 1
    pronunciation.save()
    
    result = {"pronunciation": pronunciation_all(pronunciation)}
    
    # Add approval history for admin users
    if "token" in request.headers:
        user = token_check(request.headers["token"], settings.JWT_KEY, -1)
        if user:
            from notifications.models import Notification
            from django.contrib.contenttypes.models import ContentType
            
            ct = ContentType.objects.get_for_model(pronunciation)
            notifications = Notification.objects.filter(
                action_content_type=ct, 
                action_object_id=pronunciation.id, 
                verb__icontains="审核"
            ).order_by("-timestamp")
            
            approval_history = []
            for notif in notifications:
                approval_history.append({
                    "id": notif.id,
                    "timestamp": notif.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "verb": notif.verb,
                    "description": notif.description,
                    "actor": notif.actor.username if notif.actor else "系统",
                    "recipient": notif.recipient.username if notif.recipient else None,
                })
            
            result["approval_history"] = approval_history
    
    return JsonResponse(result, status=200)
```

#### Application Detail API (`word/application/views.py`)
Similar implementation using `target_content_type` and `target_object_id`.

## Response Format

When admin users request pronunciation or application details, the response includes:

```json
{
  "pronunciation": {
    "id": 123,
    "source": "https://example.com/audio.mp3",
    ...
  },
  "approval_history": [
    {
      "id": 456,
      "timestamp": "2024-01-06 15:00:00",
      "verb": "【通知】语音审核结果",
      "description": "恭喜您的语音(id=123) 已通过审核\n\n审核意见：发音标准清晰",
      "actor": "admin",
      "recipient": "contributor_username"
    },
    {
      "id": 455,
      "timestamp": "2024-01-05 14:30:00",
      "verb": "【通知】语音审核结果",
      "description": "很遗憾，您的语音(id=123) 未通过审核\n\n审核意见：背景噪音过大",
      "actor": "reviewer",
      "recipient": "contributor_username"
    }
  ]
}
```

## Testing

To verify the fix works correctly:

1. **Admin Interface**: Navigate to a pronunciation or application detail page in Django admin
   - The "审核历史记录" section should now show existing notifications
   - Green border = approved notifications
   - Red border = rejected notifications

2. **API Testing**: Call the detail endpoints as an admin user
   ```bash
   # Pronunciation detail
   curl -H "token: ADMIN_TOKEN" http://localhost:8000/word/pronunciation/123
   
   # Application detail
   curl -H "token: ADMIN_TOKEN" http://localhost:8000/word/application/456
   ```
   - Response should include `approval_history` array for admin users
   - Regular users should not see this field

## Benefits

1. **Backward Compatibility**: Existing approval notifications are now visible
2. **Data Consistency**: All new approvals use the same field structure as existing code
3. **Single Source of Truth**: Approval reasons stored only in notifications table
4. **Admin Access**: Approval history available in both admin UI and APIs
5. **No Database Changes**: Works with existing schema and data

## Related Files

- `hinghwa-dict-backend/word/admin.py` - Admin interface approval history
- `hinghwa-dict-backend/word/pronunciation/views.py` - Pronunciation API approval history
- `hinghwa-dict-backend/word/application/views.py` - Application API approval history
- `hinghwa-dict-backend/word/templates/admin/word/pronunciation/change_form.html` - UI template
- `hinghwa-dict-backend/word/templates/admin/word/application/change_form.html` - UI template
