# 下一步

## 当前进度
- 已完成：Sprint 1 (项目基础设施与首页), Sprint 2 (用户认证：手机号 + 验证码登录), Sprint 3 (素材上传与文件管理)
- 当前 Sprint：Sprint 3 已完成，准备进入 Sprint 4

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
- 前端 Auth 状态管理：AuthContext、AuthGuard
- 导航栏用户状态切换：未登录显示"登录"按钮，已登录显示用户头像 + 下拉菜单

### Sprint 3
- 上传页 P03 完整实现：
  - UploadZone 组件：拖拽上传区（虚线边框）+ 点击上传，支持多文件
  - FileList 组件：文件列表显示文件名、大小、上传进度条、绿色勾号，dnd-kit 拖拽排序，删除按钮
  - PreferencePanel 组件："让 AI 自动决定"标签（绿色勾号），可展开"高级设置"（字幕样式 3 套 + 字幕位置选择）
  - 文件格式校验：客户端 + 服务端双层验证，非视频文件显示 toast 提示
  - 上传进度条：XMLHttpRequest 实现逐文件进度追踪
  - "开始处理"按钮：有文件时可点击，无文件时灰色禁用
  - 底部显示"您还有 N 条免费额度"
  - 移动端响应式：上传区和偏好设置纵向堆叠
- 后端任务端点：
  - POST /api/tasks（创建任务）
  - POST /api/tasks/{id}/files（上传文件，multipart）
  - PUT /api/tasks/{id}/files/reorder（文件排序）
  - DELETE /api/tasks/{id}/files/{file_id}（删除文件）
  - PUT /api/tasks/{id}/preferences（更新偏好设置）
  - GET /api/tasks/{id}（获取任务详情含文件列表）
  - GET /api/quota（获取用户免费额度）
  - 文件存储：本地磁盘 UPLOAD_DIR/<task_id>/

## 下一个具体任务
Evaluator 应测试 Sprint 3 的验收标准
