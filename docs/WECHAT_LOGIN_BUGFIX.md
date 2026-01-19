# WeChat Login Bug Fix and Improvements

## Critical Bug Fixed

### Issue
WeChat mini-program registration was failing with "参数值异常" (parameter value exception) error.

### Root Cause
In `user/view/wechat.py`, the `WechatRegister` and `WechatWebRegister` classes were attempting to:
1. Create a User object with `user_form.save(commit=False)`
2. Create a UserInfo object **before** saving the User to database
3. Access `user.id` which was `None` because user wasn't saved yet

This caused a `ValueError` exception when trying to create the UserInfo object, which was caught by Django's `ExceptionMiddleware` and returned as "参数值异常".

### Fix Applied
**Before:**
```python
user = user_form.save(commit=False)
user.set_password(...)
user.email = ""
user_info = UserInfo.objects.create(user=user, ...)  # ❌ User not saved yet!
# ... 
user.save()  # Too late!
```

**After:**
```python
user = user_form.save(commit=False)
user.set_password(...)
user.email = ""
user.save()  # ✅ Save user FIRST
user_info = UserInfo.objects.create(user=user, ...)  # ✅ Now it works!
```

### Testing
Created test script (`/tmp/test_wechat_register.py`) that verifies:
- User form validation works
- User can be saved successfully
- UserInfo can be created after user is saved
- Test passes ✅

## New Features Implemented

### 1. Enhanced Error Messages
Instead of generic "请求有误", the API now returns detailed validation errors:
```json
{
  "msg": "表单验证失败",
  "errors": ["field1: error message", "field2: error message"]
}
```

### 2. WeChat-Only Registration
Users can now register with only WeChat, without providing an email:
- Email field is optional for WeChat registration
- Automatically set to empty string if not provided
- User can add email later

### 3. Phone Number Support
Added support for phone number in registration:
```json
{
  "username": "user123",
  "password": "pass123",
  "jscode": "wx_code",
  "telephone": "13800138000"  // Optional
}
```

### 4. Web WeChat OAuth Support
Added three new endpoints for web/H5 WeChat OAuth:
- `POST /users/wechat/web` - Web WeChat login
- `POST /users/wechat/web/register` - Web WeChat registration
- `PUT /users/<id>/wechat/web` - Bind Web WeChat to account

### 5. Email Unbinding
Added endpoint to unbind email (requires WeChat bound):
- `DELETE /users/<id>/email` - Unbind email

### 6. Enhanced Registration Response
Registration now returns token and user ID for immediate login:
```json
{
  "id": 123,
  "token": "jwt_token_here"
}
```

## Frontend Compatibility

### Current Frontend Behavior
Looking at `hinghwa-dict-uni-app/src/services/user.js`:
- Line 49: Calls `/users/wechat/register` with username, password, jscode, nickname
- Line 54-60: On success, shows "注册成功" and navigates back
- **Issue**: Doesn't save the returned token/id, user must login again

### Backend Changes Compatibility
✅ **Fully backward compatible** - All changes maintain existing API contracts:
- Request parameters unchanged
- Success status code unchanged (200)
- Response now includes additional fields (token, id) but frontend can ignore them
- Error responses improved but still return appropriate status codes

### Recommended Frontend Improvements

**Option 1: Auto-login after registration (Recommended)**
```javascript
// In registerWechatUser function (user.js line 49)
await rawRequest.post('/users/wechat/register', {
  username, password, jscode, nickname,
}).then(async (res) => {
  // Save token and id for auto-login
  uni.setStorageSync('token', res.token);
  uni.setStorageSync('id', res.id);
  await loadUserInfo();
  
  uni.showToast({
    title: '注册成功',
  });
  
  // Navigate to home/me page instead of back
  toMePage();
}).catch((err) => {
  // Error handling remains the same
});
```

**Option 2: Keep current behavior (No changes needed)**
Frontend continues to work as-is. Users register then login manually.

## API Endpoints Summary

### Mini-Program Endpoints
| Method | Endpoint | Description | Changes |
|--------|----------|-------------|---------|
| POST | `/users/wechat` | WeChat login | ✅ No change |
| POST | `/users/wechat/register` | WeChat register | ✨ Now returns token+id, better errors, supports phone |
| PUT | `/users/<id>/wechat` | Bind WeChat | ✅ No change |
| DELETE | `/users/<id>/wechat` | Unbind WeChat | ✅ No change |

### Web OAuth Endpoints (NEW)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/wechat/web` | Web WeChat login |
| POST | `/users/wechat/web/register` | Web WeChat register |
| PUT | `/users/<id>/wechat/web` | Bind Web WeChat |

### Email Management
| Method | Endpoint | Description | Changes |
|--------|----------|-------------|---------|
| PUT | `/users/<id>/email` | Update email | ✅ No change |
| DELETE | `/users/<id>/email` | Unbind email | ✨ NEW endpoint |

## Configuration

Add to `.env` file:
```bash
# WeChat Mini-Program
APP_ID=your_miniprogram_appid
APP_SECRECT=your_miniprogram_secret

# WeChat Web OAuth (optional, defaults to mini-program credentials)
WEB_APP_ID=your_web_appid
WEB_APP_SECRET=your_web_secret
```

## Security & Compliance

### Account Binding Rules
Users must maintain at least one login method:
- ✅ Can have WeChat only (no email)
- ✅ Can have email only (no WeChat)
- ❌ Cannot unbind both WeChat and email
- Attempting to unbind the last method returns 403 error

### Validation
- Password: 6-32 characters (enforced by `PasswordValidation`)
- Username: Must be unique
- WeChat openid: Must be unique per account

## Testing Checklist

Backend testing:
- [x] User registration without email works
- [x] UserInfo created correctly
- [x] Token generated and returned
- [x] Phone number saved if provided
- [ ] WeChat API integration (requires valid APP_ID/SECRET)
- [ ] Web OAuth endpoints (requires valid WEB_APP_ID/SECRET)

Frontend testing needed:
- [ ] Mini-program registration flow
- [ ] Error messages display correctly
- [ ] Consider implementing auto-login
- [ ] Web/H5 WeChat OAuth integration

## Migration Notes

### For Developers
1. No database migrations required (existing schema works)
2. No breaking changes to existing APIs
3. New endpoints are additive only
4. Frontend can adopt new features incrementally

### For Deployment
1. Ensure `.env` has valid `APP_ID` and `APP_SECRECT`
2. Optionally add `WEB_APP_ID` and `WEB_APP_SECRET` for web OAuth
3. No special migration steps needed
4. Backward compatible with existing users

## Future Enhancements

### Recommended
1. **UnionID Support**: Use WeChat UnionID to link mini-program and web accounts
2. **Phone Verification**: Add SMS verification for phone numbers
3. **Social Login**: Support other OAuth providers (QQ, Weibo, etc.)

### Frontend Improvements
1. Auto-login after registration
2. Better error message display
3. One-click registration UI (auto-generate username/password)
4. Web WeChat OAuth integration

## References

- WeChat Mini-Program Auth: https://developers.weixin.qq.com/miniprogram/dev/api-backend/open-api/login/auth.code2Session.html
- WeChat Web OAuth: https://developers.weixin.qq.com/doc/offiaccount/OA_Web_Apps/Wechat_webpage_authorization.html
- Django User Model: https://docs.djangoproject.com/en/5.0/ref/contrib/auth/
