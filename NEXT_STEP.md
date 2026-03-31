# 下一步

## 当前进度
- 已完成：Sprint 1 (项目基础设施与首页), Sprint 2 (用户认证：手机号 + 验证码登录)
- 当前 Sprint：Sprint 2 已完成，准备进入 Sprint 3

## 已完成的内容

### Sprint 1
- 前端首页 P01：Hero 区域（标题/副标题/CTA）、4 张特性卡片、版权页脚
- 全局布局：导航栏（Logo + 登录按钮）、AuthProvider、ToastProvider
- 后端 FastAPI：main.py、config.py、database.py、models.py、auth.py
- 健康检查：GET /api/health 返回 200
- 前后端联通：Next.js rewrites 代理 /api 到后端 8000 端口
- 移动端适配：375px 下特性卡片 2x2 网格布局

### Sprint 2
- 登录页 P02：手机号输入、验证码发送/输入、登录按钮、60s 倒计时
- 后端认证端点：POST /api/auth/send-code、POST /api/auth/login、POST /api/auth/logout、GET /api/auth/me
- JWT token 管理：创建/验证 JWT、Bearer token 认证
- 前端 Auth 状态管理：AuthContext（login/logout/refreshUser）、localStorage token 持久化
- AuthGuard 组件：未登录访问受保护页面自动跳转 /login
- 导航栏用户状态切换：未登录显示"登录"按钮，已登录显示用户头像（手机号后4位色块）+ 下拉菜单（退出登录）
- 首页 CTA 按钮：未登录显示"免费试用"→/login，已登录显示"上传素材"→/upload
- 安全防护：验证码错误锁定（3次失败锁5分钟）、手机号60秒冷却、IP每小时10次限制
- 登录成功后自动跳转到 /upload 页面
- /upload 占位页面（带 AuthGuard 保护，Sprint 3 将实现完整功能）

## 下一个具体任务
Evaluator 应测试 Sprint 2 的验收标准
