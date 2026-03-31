# 下一步

## 当前进度
- 已完成：Sprint 1 (项目基础设施与首页), Sprint 2 (用户认证：手机号 + 验证码登录), Sprint 3 (素材上传与文件管理), Sprint 4 (AI 处理引擎), Sprint 5 (预览页：口误审核 + 字幕样式)
- 当前 Sprint：Sprint 5 已完成，准备进入 Sprint 6

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
- 后端处理管线：FFmpeg 合并、Whisper 语音识别(mock)、口误检测规则引擎、字幕生成
- 前端处理中页 P04：3 阶段进度显示、超时检测、取消处理
- 后台线程处理、in-memory 进度追踪

### Sprint 5
- 后端预览 API：
  - GET /api/tasks/{id}/preview：返回文字稿(words)、口误标记(stutter_marks)、字幕(subtitles)、统计信息
  - PUT /api/tasks/{id}/preview：保存用户调整（口误标记切换、字幕样式）
  - 动态统计：根据当前 mark actions 实时计算 deleted_count 和 deleted_duration_ms
- 前端预览页 P05：
  - TranscriptPanel：展示文字稿，口误标记红色背景 + 删除线，支持点击切换 delete/keep
  - StutterWordMark：删除态（红色背景+删除线）、保留态（绿色左竖线+正常文字）
  - PauseMark：长停顿标记（显示停顿时长，可切换删除/保留）
  - SubtitleStylePanel：3 套预设样式（简洁白字/黑底白字/彩色高亮）+ 视觉预览
  - SubtitlePreview：模拟视频画面上的字幕效果预览
  - StutterStatsBar：实时统计"共检测到 N 处口误，预计缩短 M 秒"
  - 底部操作栏："重新处理"（次要按钮）+ "确认，开始渲染"（主按钮）
  - 移动端适配：文字稿区域和字幕设置纵向堆叠
- 修复 Sprint 4 P2 问题：estimated_seconds 使用 ?? 替代 || 运算符

## 下一个具体任务
Sprint 5 P1 bug 已修复（循环重定向问题）。Evaluator 应复测 Sprint 5 验收标准中的"确认，开始渲染"按钮跳转行为。通过后进入 Sprint 6。
