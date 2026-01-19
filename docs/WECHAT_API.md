# 微信登录 API 完整文档

## 目录
1. [概述](#概述)
2. [配置说明](#配置说明)
3. [小程序端接口](#小程序端接口)
4. [网页端接口](#网页端接口)
5. [前端集成示例](#前端集成示例)
6. [常见问题](#常见问题)

## 概述

兴化语记支持两种微信登录方式：
- **微信小程序登录**：使用 `wx.login()` 获取的 `code` (jscode)
- **网页版微信OAuth**：使用网页授权获取的 `code`

### 合规要求
- 用户必须至少绑定**微信**或**邮箱**其中之一
- 支持仅用微信注册（无需邮箱）
- 解绑时确保至少保留一种登录方式

## 配置说明

### 环境变量配置
```bash
# 小程序配置
APP_ID=wxXXXXXXXXXXXXXXXX
APP_SECRECT=your_miniprogram_secret

# 网页版配置（可选）
WEB_APP_ID=wxYYYYYYYYYYYYYYYY
WEB_APP_SECRET=your_web_secret
```

## 小程序端接口

### 1. 微信登录
```
POST /users/wechat
```

**功能**: 使用微信小程序登录已有账户

**请求体**:
```json
{
  "jscode": "string"  // wx.login() 获取的 code
}
```

**响应** (200):
```json
{
  "token": "eyJ...",  // JWT token
  "id": 123           // 用户ID
}
```

**错误响应**:
- `404`: 当前微信未绑定账号
- `500`: 微信API调用失败

**前端示例**:
```javascript
uni.login({
  success: (res) => {
    rawRequest.post('/users/wechat', {
      jscode: res.code
    }).then((data) => {
      uni.setStorageSync('token', data.token);
      uni.setStorageSync('id', data.id);
      // 登录成功，跳转到主页
    }).catch((err) => {
      if (err.statusCode === 404) {
        // 未注册，跳转到注册页面
      }
    });
  }
});
```

---

### 2. 微信注册
```
POST /users/wechat/register
```

**功能**: 使用微信快速注册新账户（一键注册）

**请求体**:
```json
{
  "jscode": "string",      // 必填：wx.login() 获取的 code
  "username": "string",    // 必填：用户名
  "password": "string",    // 必填：密码（6-32位）
  "nickname": "string",    // 可选：昵称（默认为username）
  "avatar": "string",      // 可选：头像（base64或URL）
  "telephone": "string"    // 可选：手机号
}
```

**响应** (200):
```json
{
  "id": 123,              // 用户ID
  "token": "eyJ..."       // JWT token（可直接登录）
}
```

**错误响应**:
- `400`: 表单验证失败
  ```json
  {
    "msg": "表单验证失败",
    "errors": ["username: 用户名格式错误", "password: 密码长度不够"]
  }
  ```
- `409`: 用户名重复或微信已绑定
  ```json
  {
    "msg": "用户名重复"
    // 或 "该微信已绑定账户"
  }
  ```

**前端示例**:
```javascript
export function registerWechatUser(username, password, nickname) {
  uni.login({
    async success(res) {
      await rawRequest.post('/users/wechat/register', {
        username,
        password,
        jscode: res.code,
        nickname,
      }).then(async (data) => {
        // 🆕 现在可以直接登录！
        uni.setStorageSync('token', data.token);
        uni.setStorageSync('id', data.id);
        await loadUserInfo();
        
        uni.showToast({ title: '注册成功' });
        toMePage(); // 直接进入个人主页
      }).catch((err) => {
        // 错误处理
        uni.showToast({
          title: err.data.msg || '注册失败',
          icon: 'error'
        });
      });
    }
  });
}
```

---

### 3. 绑定微信
```
PUT /users/{id}/wechat
```

**功能**: 将微信绑定到现有账户

**请求头**:
```
token: string  // JWT token
```

**请求体**:
```json
{
  "jscode": "string",      // wx.login() 获取的 code
  "overwrite": false       // 可选：是否覆盖已有绑定
}
```

**响应** (200):
```json
{}
```

**错误响应**:
- `401`: 未授权
- `403`: 无权限（不是本人操作）
- `409`: 该微信已绑定其他账号，或该账户已绑定微信

---

### 4. 解绑微信
```
DELETE /users/{id}/wechat
```

**功能**: 解除微信绑定（需要已绑定邮箱）

**请求头**:
```
token: string
```

**响应** (200):
```json
{}
```

**错误响应**:
- `403`: 未绑定邮箱，无法解绑微信
- `404`: 未绑定微信

---

### 5. 微信重置密码
```
POST /users/{id}/password/reset
```

**功能**: 通过微信验证身份后重置密码

**请求头**:
```
token: string
```

**请求体**:
```json
{
  "jscode": "string",        // wx.login() 获取的 code
  "newpassword": "string"    // 新密码
}
```

**响应** (200):
```json
{
  "user": { /* 用户信息 */ },
  "token": "eyJ..."  // 新token
}
```

**错误响应**:
- `403`: 微信与当前用户不匹配

---

## 网页端接口

### 1. 网页版微信登录
```
POST /users/wechat/web
```

**功能**: 使用微信网页授权登录

**请求体**:
```json
{
  "code": "string"  // 微信OAuth回调的code
}
```

**响应** (200):
```json
{
  "token": "eyJ...",
  "id": 123
}
```

**前端示例**:
```javascript
// 1. 引导用户授权
const appid = 'wxYYYYYYYYYYYYYYYY';
const redirect_uri = encodeURIComponent('https://pxm.edialect.top/wechat/callback');
const scope = 'snsapi_userinfo'; // 获取用户信息
const url = `https://open.weixin.qq.com/connect/oauth2/authorize?appid=${appid}&redirect_uri=${redirect_uri}&response_type=code&scope=${scope}&state=STATE#wechat_redirect`;
window.location.href = url;

// 2. 在回调页面处理
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');

fetch('https://api.pxm.edialect.top/users/wechat/web', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ code })
}).then(res => res.json())
.then(data => {
  localStorage.setItem('token', data.token);
  localStorage.setItem('id', data.id);
  // 登录成功
});
```

---

### 2. 网页版微信注册
```
POST /users/wechat/web/register
```

**功能**: 使用微信网页授权注册（可自动获取昵称和头像）

**请求体**:
```json
{
  "code": "string",        // 必填：OAuth回调的code
  "username": "string",    // 必填：用户名
  "password": "string",    // 必填：密码
  "nickname": "string",    // 可选：昵称（默认从微信获取）
  "avatar": "string",      // 可选：头像（默认从微信获取）
  "telephone": "string"    // 可选：手机号
}
```

**响应** (200):
```json
{
  "id": 123,
  "token": "eyJ..."
}
```

**特点**:
- 自动从微信获取用户昵称和头像（scope=snsapi_userinfo时）
- 如果请求体中提供了nickname/avatar，则优先使用请求体的值

---

### 3. 绑定网页版微信
```
PUT /users/{id}/wechat/web
```

**功能**: 将网页版微信绑定到现有账户

**请求头**:
```
token: string
```

**请求体**:
```json
{
  "code": "string",        // OAuth回调的code
  "overwrite": false       // 可选：是否覆盖
}
```

**响应** (200):
```json
{}
```

---

## 邮箱管理接口

### 1. 更新邮箱
```
PUT /users/{id}/email
```

**请求头**:
```
token: string
```

**请求体**:
```json
{
  "email": "string",
  "code": "string"  // 邮箱验证码
}
```

**响应** (200):
```json
{
  "user": { /* 用户完整信息 */ }
}
```

---

### 2. 解绑邮箱（新增）
```
DELETE /users/{id}/email
```

**功能**: 解绑邮箱（需要已绑定微信）

**请求头**:
```
token: string
```

**响应** (200):
```json
{
  "user": { /* 用户完整信息 */ }
}
```

**错误响应**:
- `403`: 未绑定微信，无法解绑邮箱

---

## 前端集成示例

### 一键注册最佳实践

**推荐流程**:
1. 用户点击"微信快速注册"
2. 自动生成用户名和密码
3. 获取微信信息（昵称、头像）
4. 后台静默注册
5. 自动登录，直接进入应用

**完整示例**:
```javascript
// utils/wechat.js
export async function quickWechatRegister() {
  // 1. 获取微信code
  const loginRes = await uni.login();
  if (!loginRes.code) {
    throw new Error('获取微信授权失败');
  }

  // 2. 尝试获取用户信息
  let userInfo = {};
  try {
    const profileRes = await uni.getUserProfile({
      desc: '用于完善会员资料'
    });
    userInfo = profileRes.userInfo;
  } catch (e) {
    console.log('用户取消授权，使用默认信息');
  }

  // 3. 自动生成凭证
  const timestamp = Date.now();
  const username = `wx_${timestamp}`;
  const password = generateSecurePassword(16); // 生成16位随机密码

  // 4. 发送注册请求
  const res = await rawRequest.post('/users/wechat/register', {
    jscode: loginRes.code,
    username: username,
    password: password,
    nickname: userInfo.nickName || username,
    avatar: userInfo.avatarUrl || ''
  });

  // 5. 保存凭证（加密存储）
  uni.setStorageSync('username', username);
  uni.setStorageSync('password', encryptPassword(password));
  uni.setStorageSync('token', res.token);
  uni.setStorageSync('id', res.id);

  // 6. 加载用户信息
  await loadUserInfo();

  return res;
}

// 生成安全的随机密码
function generateSecurePassword(length = 16) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%';
  let password = '';
  for (let i = 0; i < length; i++) {
    password += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return password;
}
```

---

### 自动登录示例

```javascript
// 在 App.vue 的 onLaunch 中
export default {
  onLaunch: function() {
    this.tryAutoLogin();
  },
  methods: {
    async tryAutoLogin() {
      const token = uni.getStorageSync('token');
      if (token) {
        // 尝试刷新token
        const success = await getLoginStatus();
        if (success) {
          console.log('自动登录成功');
          return;
        }
      }

      // Token无效或不存在，尝试微信自动登录
      // #ifndef H5
      try {
        await mpLogin();
        console.log('微信自动登录成功');
      } catch (e) {
        console.log('自动登录失败，需要手动登录');
      }
      // #endif
    }
  }
}
```

---

## 常见问题

### Q1: 小程序和网页版的openid一样吗？
**A**: 不一样。小程序和网页版（包括公众号）的openid是独立的。同一个用户在不同平台有不同的openid。如需统一身份，请使用UnionID（需开通微信开放平台）。

### Q2: 注册后需要再次登录吗？
**A**: 不需要。后端现在返回token和id，前端可以直接保存并登录。

### Q3: 如何获取用户手机号？
**A**: 
- **小程序**: 使用 `<button open-type="getPhoneNumber">` 组件
- **网页**: 需要用户手动输入

### Q4: 用户忘记密码怎么办？
**A**: 
1. 如果绑定了微信，可以使用微信直接登录
2. 如果绑定了邮箱，可以通过邮箱重置密码  
3. 可以使用 `/users/{id}/password/reset` 接口通过微信验证后重置

### Q5: 可以同时解绑微信和邮箱吗？
**A**: 不可以。系统要求至少保留一种登录方式，确保用户账户可访问。

### Q6: "参数值异常"错误怎么解决？
**A**: 该问题已在最新版本修复。如果仍然遇到：
1. 确保使用最新版本的后端代码
2. 检查请求参数是否完整（username, password, jscode）
3. 查看详细错误信息（现在会返回具体的验证错误）

### Q7: 网页授权scope应该用哪个？
**A**:
- `snsapi_base`: 静默授权，只能获取openid
- `snsapi_userinfo`: 需要用户确认，可获取昵称、头像等信息（推荐用于注册）

---

## 技术支持

遇到问题请提交Issue:
- 后端: https://github.com/e-dialect/hinghwa-dict-backend/issues
- 前端Web: https://github.com/e-dialect/hinghwa-dict-web/issues  
- 前端uni-app: https://github.com/e-dialect/hinghwa-dict-uni-app/issues

## 更新日志

**2024-01-06**
- ✅ 修复关键bug：注册时"参数值异常"错误
- ✅ 新增网页版微信OAuth支持
- ✅ 注册接口返回token和id
- ✅ 支持电话号码字段
- ✅ 优化错误信息提示
- ✅ 新增邮箱解绑功能
- ✅ 完善合规性验证
