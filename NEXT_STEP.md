# 下一步

## 当前进度
- 已完成：Sprint 1 (项目基础设施与首页), Sprint 2 (用户认证：手机号 + 验证码登录), Sprint 3 (素材上传与文件管理), Sprint 4 (AI 处理引擎)
- 当前 Sprint：Sprint 4 已完成，准备进入 Sprint 5

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
- 上传页 P03 完整实现：UploadZone、FileList、PreferencePanel 组件
- 后端任务端点：POST /api/tasks、POST /api/tasks/{id}/files、PUT /api/tasks/{id}/files/reorder、DELETE /api/tasks/{id}/files/{file_id}、PUT /api/tasks/{id}/preferences、GET /api/tasks/{id}、GET /api/quota

### Sprint 4
- 后端处理管线：
  - Stage 0: FFmpeg 素材合并（单文件 copy / 多文件 concat demuxer）
  - Stage 1: 语音识别（OpenAI Whisper API，无 key 则使用 mock 数据，输出 word-level 时间戳）
  - Stage 2: 口误检测规则引擎（填充词检测、重复词检测、长停顿检测）
  - Stage 3: 字幕生成（word segments 分组、SRT 文件输出）
  - 后台线程执行，in-memory 进度追踪
- 后端新端点：
  - POST /api/tasks/{id}/process（触发处理）
  - GET /api/tasks/{id}/status（返回 stage、progress、estimated_seconds、stages 数组）
- 任务状态流转：uploading -> processing -> preview（或 failed）
- 处理结果存入 task_results 表（transcribe、stutter、subtitle）
- 失败重试支持（failed 状态可重新触发处理）
- 前端处理中页 P04：
  - /processing/{taskId} 页面，3 阶段进度显示（合并素材 -> 语音识别 -> 检测口误&生成字幕）
  - ProgressSteps 组件：已完成绿色勾号、当前阶段旋转动画、未开始灰色圆点
  - 每 2 秒轮询 GET /api/tasks/{id}/status 更新进度
  - 处理完成自动跳转 /preview/{taskId}
  - 超时检测（>15 分钟）+ 重试按钮
  - 取消处理确认弹窗
- 预览页占位页面（Sprint 5 完整实现）

## 下一个具体任务
Evaluator 应测试 Sprint 4 的验收标准
