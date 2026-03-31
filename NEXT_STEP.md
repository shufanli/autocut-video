# 下一步

## 当前进度
- 已完成：Sprint 1 (项目基础设施与首页), Sprint 2 (用户认证：手机号 + 验证码登录), Sprint 3 (素材上传与文件管理), Sprint 4 (AI 处理引擎), Sprint 5 (预览页：口误审核 + 字幕样式), Sprint 6 (视频渲染与完成页)
- 当前 Sprint：Sprint 6 已完成，准备进入 Sprint 7

## 已完成的内容

### Sprint 6
- 后端渲染引擎 (`backend/services/render.py`):
  - FFmpeg 两步渲染：先裁剪口误片段(filter_complex trim+concat)，再烧录字幕(如libass可用)
  - 渲染进度追踪：in-memory dict，通过 GET /api/tasks/{id}/render-status 查询
  - 自动重试：渲染失败自动重试 1 次 (RENDER_MAX_RETRY=1)
  - WebVTT 字幕生成：为 HTML5 播放器提供带时间戳调整的 .vtt 字幕文件
  - 无 libass 时优雅降级：跳过字幕烧录，仅做裁剪+WebVTT外挂字幕
  - 渲染完成后：task.status="completed", 设置 expires_at=24h, 记录输出文件信息
- 后端新端点:
  - POST /api/tasks/{id}/render：启动渲染（已有，Sprint 6 加入实际渲染逻辑）
  - GET /api/tasks/{id}/render-status：渲染进度（progress 0-100, estimated_seconds）
  - GET /api/tasks/{id}/result：视频信息（时长、大小、分辨率、剪切数）
  - GET /api/tasks/{id}/stream：视频流播放（HTML5 video src）
  - GET /api/tasks/{id}/download：下载 MP4 文件（Content-Disposition: attachment）
  - GET /api/tasks/{id}/subtitles.vtt：WebVTT 字幕文件
  - POST /api/tasks/{id}/feedback：满意度反馈（up/down）
- 前端完成页 P07 (`frontend/src/app/result/[taskId]/page.tsx`):
  - 成功图标 + "视频已完成!" 标题
  - HTML5 视频播放器（含 WebVTT 字幕 track）
  - 视频信息：时长、文件大小、分辨率、口误剪切数
  - 下载按钮（blob download）
  - "视频将在 24 小时后自动删除，请及时下载" 提示
  - "处理新视频" 按钮跳转上传页
  - 满意度反馈 👍👎
  - 渲染失败错误提示 + 重试按钮
  - 移动端响应式（375px 适配）
- 前端处理中页更新:
  - 渲染状态：独立 UI，单进度条 + 百分比 + 预估时间
  - 渲染完成自动跳转到 /result/{taskId}
  - 渲染失败智能重试（区分处理失败 vs 渲染失败）
- 其他修复:
  - FileResponse 命名冲突修复（Pydantic 模型 vs FastAPI import）
  - aiofiles 依赖添加
  - Sprint 5 P2 修复：渲染页不再显示处理阶段步骤

## 下一个具体任务
Evaluator 应测试 Sprint 6 的验收标准。通过后进入 Sprint 7 (支付系统与额度管理)。
