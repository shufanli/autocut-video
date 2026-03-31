# 下一步

## 当前进度
- 已完成：Sprint 0 — 项目脚手架与基础设施
- 已完成：Sprint 1 — 用户认证：手机号 + 验证码登录
- 当前 Sprint：Sprint 1 已完成，准备进入 Sprint 2
- 当前状态：Sprint 1 全部验收标准已实现

## Sprint 1 完成清单
- [x] P02 登录页 UI 完成：手机号输入框、获取验证码按钮、验证码输入框、登录按钮，样式符合 DESIGN.md
- [x] 点击"获取验证码"：后端 mock 短信（控制台打印验证码，固定 123456）
- [x] 验证码发送后按钮变为"已发送（60s）"倒计时
- [x] 输入正确验证码后登录成功，后端返回 JWT token，前端存储并跳转
- [x] 验证码错误：输入框下方显示红色错误提示
- [x] 连续 3 次错误：锁定 5 分钟（可配置）
- [x] 同一 IP 每小时验证码发送上限 10 次（可配置）
- [x] 后端 /api/auth/send-code、/api/auth/login、/api/auth/logout、/api/auth/me 四个端点正常工作
- [x] 前端全局 Auth 状态管理：已登录时导航栏显示用户头像（手机号后 4 位圆形色块），未登录显示"登录"按钮
- [x] 未登录访问需认证页面时重定向到 /login（AuthGuard 组件）

## Sprint 1 技术实现
- JWT 存储在 localStorage（MVP 简化），token 有效期 72 小时
- 验证码存储：Python dict + TTL（MVP 简化）
- 新用户首次登录自动创建 users 记录，free_quota_remaining = 3
- 前端 AuthProvider context 管理全局认证状态
- Navbar 根据登录状态切换：登录按钮 / 用户头像（带下拉菜单）

## 下一个具体任务
启动 Sprint 2 — 首页与上传页

## 阻塞项
无
