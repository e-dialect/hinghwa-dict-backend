# Frontend Issues for WeChat Login Improvements

## Issue 1: [uni-app] 微信注册后自动登录

**标题**: 微信注册成功后自动登录，提升用户体验

**描述**:

### 背景
目前微信注册流程中，用户注册成功后需要返回到登录页面重新输入用户名和密码登录，体验不够流畅。

后端已经更新，注册接口现在会返回 `token` 和 `id`，可以实现注册后自动登录。

### 当前行为
```javascript
// src/services/user.js registerWechatUser()
.then(async () => {
  uni.showToast({ title: '注册成功' });
  uni.navigateBack({ delta: 1 }); // 返回上一页，用户需要重新登录
})
```

### 期望行为
```javascript
.then(async (res) => {
  // 保存token和id
  uni.setStorageSync('token', res.token);
  uni.setStorageSync('id', res.id);
  
  // 加载用户信息
  await loadUserInfo();
  
  uni.showToast({ title: '注册成功' });
  
  // 直接进入个人主页
  toMePage();
})
```

### 修改文件
- `src/services/user.js` 中的 `registerWechatUser` 函数
- 导入 `loadUserInfo` 和 `toMePage`

### 好处
1. 提升用户体验，一键注册即可使用
2. 减少用户操作步骤
3. 符合"微信一键登录"的设计初衷

### 优先级
建议：高 🔴

### 参考实现
参见后端文档: `docs/WECHAT_API.md` 中的"前端集成示例"部分

---

## Issue 2: [uni-app] 实现真正的"一键注册"功能

**标题**: 实现微信一键注册 - 自动生成用户名和密码

**描述**:

### 背景
当前微信注册仍需要用户输入用户名、密码、昵称等信息，不够"一键"。建议实现真正的一键注册功能。

### 建议方案

**方案一：简化注册（推荐）**
在微信注册页面添加"快速注册"按钮：
- 自动生成用户名（如：`wx_1234567890`）
- 自动生成强密码（后台加密保存）
- 尝试获取微信昵称和头像
- 直接完成注册并登录

**方案二：保留当前流程，增加快捷选项**
保留现有表单，但添加"使用微信信息快速填充"功能：
- 点击按钮自动填充用户名、昵称
- 用户只需确认即可

### 实现示例

```javascript
// 新增文件: src/services/quickRegister.js
export async function quickWechatRegister() {
  // 1. 获取微信授权
  const loginRes = await uni.login();
  
  // 2. 尝试获取用户信息
  let userInfo = {};
  try {
    const profile = await uni.getUserProfile({
      desc: '用于完善会员资料'
    });
    userInfo = profile.userInfo;
  } catch (e) {
    console.log('用户取消授权');
  }

  // 3. 生成凭证
  const username = `wx_${Date.now()}`;
  const password = generatePassword(16);

  // 4. 注册
  const res = await rawRequest.post('/users/wechat/register', {
    jscode: loginRes.code,
    username,
    password,
    nickname: userInfo.nickName || username,
    avatar: userInfo.avatarUrl || ''
  });

  // 5. 保存并登录
  uni.setStorageSync('username', username);
  uni.setStorageSync('password', password); // 加密存储
  uni.setStorageSync('token', res.token);
  uni.setStorageSync('id', res.id);

  return res;
}
```

### 修改页面
- `src/pages/login/register/wechat.vue` - 添加"快速注册"按钮
- 或创建新页面 `src/pages/login/register/wechat-quick.vue`

### 用户体验
1. 首次使用：点击"微信一键注册" → 授权 → 完成（3秒内）
2. 后续使用：微信自动登录或用户名密码登录
3. 密码管理：提供"修改密码"入口供用户自定义

### 优先级
建议：中 🟡

---

## Issue 3: [web] 实现H5网页版微信OAuth登录

**标题**: 支持H5页面微信授权登录

**描述**:

### 背景
后端已实现网页版微信OAuth接口：
- `POST /users/wechat/web` - 登录
- `POST /users/wechat/web/register` - 注册
- `PUT /users/{id}/wechat/web` - 绑定

前端需要实现相应的H5页面支持。

### 需要实现的功能

1. **微信授权跳转**
```javascript
function redirectToWechatAuth() {
  const appid = process.env.WEB_APP_ID;
  const redirect_uri = encodeURIComponent(
    window.location.origin + '/wechat/callback'
  );
  const state = Math.random().toString(36).substring(7);
  sessionStorage.setItem('wechat_state', state);
  
  const url = `https://open.weixin.qq.com/connect/oauth2/authorize?` +
    `appid=${appid}&redirect_uri=${redirect_uri}&` +
    `response_type=code&scope=snsapi_userinfo&state=${state}#wechat_redirect`;
  
  window.location.href = url;
}
```

2. **回调处理页面**
创建 `/wechat/callback` 路由：
- 获取URL中的code参数
- 验证state参数
- 调用后端登录/注册接口
- 保存token并跳转

3. **在微信内浏览器检测**
```javascript
function isWeChatBrowser() {
  return /MicroMessenger/i.test(navigator.userAgent);
}

// 在登录页面
if (isWeChatBrowser()) {
  // 显示"微信登录"按钮
}
```

### 文件修改
- 新增: `src/pages/wechat/callback.vue` - 微信回调页面
- 修改: `src/pages/login/login.vue` - 添加微信登录按钮
- 新增: `src/services/wechatWeb.js` - 网页版微信登录服务

### 注意事项
1. 需要在微信公众平台配置JS接口安全域名
2. 需要配置OAuth2回调域名
3. scope选择：
   - `snsapi_base`: 静默授权，只获取openid
   - `snsapi_userinfo`: 需用户确认，可获取昵称头像（推荐）

### 优先级
建议：中 🟡

---

## Issue 4: [uni-app] 优化错误提示信息

**标题**: 显示后端返回的详细错误信息

**描述**:

### 背景
后端已优化错误响应，返回详细的字段验证错误，但前端仍显示通用错误信息。

### 当前行为
```javascript
// 400错误统一显示
uni.showToast({
  title: err.data.msg || '注册失败',
  icon: 'error'
});
```

### 后端返回格式
```json
{
  "msg": "表单验证失败",
  "errors": [
    "username: 用户名格式不正确",
    "password: 密码长度不足6位"
  ]
}
```

### 期望行为
```javascript
// 优化后
if (err.data.errors && err.data.errors.length > 0) {
  // 显示第一个错误，或者显示所有错误
  uni.showModal({
    title: err.data.msg || '注册失败',
    content: err.data.errors.join('\n'),
    showCancel: false
  });
} else {
  uni.showToast({
    title: err.data.msg || '注册失败',
    icon: 'error'
  });
}
```

### 修改文件
- `src/services/user.js` - registerWechatUser 函数的错误处理
- 可以封装成通用的错误处理函数

### 好处
1. 用户清楚知道哪里出错
2. 减少重复尝试
3. 提升用户体验

### 优先级
建议：低 🟢

---

## Issue 5: [uni-app] 增加手机号获取功能

**标题**: 微信注册时支持获取用户手机号

**描述**:

### 背景
后端已支持保存手机号字段，前端可以在注册时获取用户授权的手机号。

### 实现方式
```vue
<template>
  <button open-type="getPhoneNumber" @getphonenumber="getPhoneNumber">
    快速获取手机号
  </button>
</template>

<script>
export default {
  methods: {
    getPhoneNumber(e) {
      if (e.detail.code) {
        // 获取到code，发送给后端
        // 后端需要用session_key解密
        this.telephone = e.detail.code;
      }
    }
  }
}
</script>
```

### 注意事项
1. 需要小程序通过认证
2. 需要后端支持解密（使用session_key）
3. 用户可以选择不授权手机号

### 后端支持
后端已支持接收 `telephone` 字段，需要额外实现手机号解密功能（如果使用加密的code）。

### 优先级
建议：低 🟢（可选功能）

---

## 总结

### 建议优先级
1. 🔴 **高优先级** - Issue 1: 注册后自动登录（最简单，效果最明显）
2. 🟡 **中优先级** - Issue 2: 一键注册（提升用户体验）
3. 🟡 **中优先级** - Issue 3: H5微信OAuth（扩展使用场景）
4. 🟢 **低优先级** - Issue 4: 错误信息优化（细节优化）
5. 🟢 **低优先级** - Issue 5: 手机号获取（可选功能）

### 开发顺序建议
1. 先实现 Issue 1（注册后自动登录）- 1小时
2. 再实现 Issue 4（错误信息优化）- 1小时  
3. 然后实现 Issue 2（一键注册）- 3-4小时
4. 最后实现 Issue 3（H5支持）- 4-6小时

所有issue的详细技术文档和示例代码请参考后端仓库的 `docs/WECHAT_API.md` 文件。
