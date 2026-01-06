# Pronunciation and Article Approval Fix Documentation

## Issue Summary

Fixed approval history display for Pronunciation and added complete approval workflow for Article model.

## Changes Made

### 1. Fixed Pronunciation Approval History (Commit 57b1f4a)

**Problem**: Approval history was not showing for Pronunciation items even though notifications existed in the database.

**Root Cause**: The query was using incorrect notification fields.
- **Incorrect**: `target_content_type` and `target_object_id`
- **Correct**: `action_content_type` and `action_object_id`

**Fix Applied** (`word/admin.py` line 178-188):
```python
def get_approval_notifications(self, obj):
    """Get approval-related notifications for this pronunciation."""
    from notifications.models import Notification
    from django.contrib.contenttypes.models import ContentType

    ct = ContentType.objects.get_for_model(obj)
    # Pronunciation uses action_object field (see word/pronunciation/views.py)
    notifications = Notification.objects.filter(
        action_content_type=ct, action_object_id=obj.id, verb__icontains="审核"
    ).order_by("-timestamp")

    return notifications
```

**Verification**: This matches how notifications are created in `word/pronunciation/views.py`:
```python
sendNotification(
    verifier,
    [contributor],
    content=content + reason,
    action_object=pronunciation,  # <-- Uses action_object
    title=f"【通知】语音（{pronunciation.word.word}）审核结果",
)
```

### 2. Added Complete Article Approval Workflow

**Features Implemented**:

#### A. Admin Detail Page (`article/admin.py`)
- **Approval Status Display**: Shows "✓ 审核通过" or "⏳ 待审核" based on visibility field
- **Approval History Section**: Displays all approval-related notifications from database
- **Approval Reason Textarea**: For entering approval/rejection reasons
- **Approval Buttons**:
  - **✓ 审核通过**: Approves article (visibility=True), sends notification, redirects to next
  - **✗ 审核不通过**: Rejects article (visibility=False), sends notification, redirects to next
- **Auto-redirect**: After approval, automatically finds and opens next unreviewed article

#### B. List View Filtering
- Added `"visibility"` to `list_filter`
- Admins can now filter by approved (visibility=True) vs unreviewed (visibility=False) articles

#### C. Batch Actions with Notifications
Updated existing batch actions to send notifications:
```python
def pass_visibility(self, request, queryset):
    for article in queryset:
        article.visibility = True
        article.save()
        # Send notification
        sendNotification(
            None,
            [article.author],
            content=f"恭喜您的文章(id={article.id}) 已通过审核",
            action_object=article,
            title="【通知】文章审核结果",
        )
```

#### D. Custom Template (`article/templates/admin/article/article/change_form.html`)
Created Django admin template extending base change_form with:
- Approval status indicator
- Approval history display (color-coded: green for approved, red for rejected)
- Approval reason textarea
- Custom approval buttons

#### E. API Enhancement (`article/views.py`)
Added approval history to `GET /article/{id}` endpoint for admins:
```python
if user and user.is_superuser:
    from notifications.models import Notification
    from django.contrib.contenttypes.models import ContentType
    
    ct = ContentType.objects.get_for_model(article)
    notifications = Notification.objects.filter(
        action_content_type=ct, 
        action_object_id=article.id, 
        verb__icontains="审核"
    ).order_by("-timestamp")
    
    approval_history = [
        {
            "id": n.id,
            "timestamp": n.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "verb": n.verb,
            "description": n.description,
            "actor": n.actor.username if n.actor else None,
            "recipient": n.recipient.username if n.recipient else None,
        }
        for n in notifications
    ]
    response_data["approval_history"] = approval_history
```

## Notification Field Mapping

Different models use different notification fields:

| Model | Notification Field | Query Fields |
|-------|-------------------|--------------|
| **Pronunciation** | `action_object` | `action_content_type`, `action_object_id` |
| **Application** | `target` | `target_content_type`, `target_object_id` |
| **Article** | `action_object` | `action_content_type`, `action_object_id` |

## Database Schema

### Article Model Fields Used
```python
class Article(models.Model):
    author = models.ForeignKey(User, ...)  # Notification recipient
    visibility = models.BooleanField(default=False, verbose_name="是否审核")
    # No verifier field - uses only visibility for approval state
```

**Approval States for Article**:
- `visibility=False` → ⏳ 待审核 (Not reviewed)
- `visibility=True` → ✓ 审核通过 (Approved)

## Workflow Comparison

### Pronunciation (3 states)
- `verifier=None` → 待审核
- `verifier exists + visibility=True` → 审核通过
- `verifier exists + visibility=False` → 审核不通过

### Application (2 states)
- `verifier=None` → 待审核
- `verifier exists` → 已审核

### Article (2 states)
- `visibility=False` → 待审核
- `visibility=True` → 审核通过

## Testing Verification

### Manual Test Steps

1. **Test Pronunciation Approval History**:
   - Go to Django Admin → Word → Pronunciations
   - Filter by "审核人" to find reviewed items
   - Click on a pronunciation that has been reviewed
   - Verify approval history section shows past notifications

2. **Test Article Approval Workflow**:
   - Go to Django Admin → Article → Articles
   - Filter by "visibility=False" to find unreviewed articles
   - Click on an article
   - Enter approval reason in textarea
   - Click "✓ 审核通过" or "✗ 审核不通过"
   - Verify notification sent and redirect to next unreviewed article

3. **Test Article API (Admin)**:
   - Make authenticated GET request to `/article/{id}` as superuser
   - Verify response includes `approval_history` field
   - Verify non-admin users don't see approval_history

## Security

- All approval operations require admin/staff privileges
- API approval history only visible to superusers
- All user input escaped via Django's template system
- Notifications sent using existing secure sendNotification() function

## Backward Compatibility

- No database migrations required
- Uses existing `visibility` field on Article
- All existing articles remain accessible
- Existing notifications properly displayed in approval history

## Files Modified

1. `hinghwa-dict-backend/word/admin.py` - Fixed Pronunciation notification query
2. `hinghwa-dict-backend/article/admin.py` - Added complete approval workflow
3. `hinghwa-dict-backend/article/views.py` - Added API approval history for admins
4. `hinghwa-dict-backend/article/templates/admin/article/article/change_form.html` - New template

## Next Steps

All requested features have been implemented:
- ✅ Pronunciation approval history now displays correctly
- ✅ Article has complete approval workflow (status, history, buttons, filtering)
- ✅ Article uses existing `visibility` field (no new fields needed)
- ✅ All approval data from database now visible to admins
