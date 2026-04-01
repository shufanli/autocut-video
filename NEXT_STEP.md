# 下一步

## 当前进度
- 已完成：Sprint 1 (项目基础设施与首页), Sprint 2 (用户认证), Sprint 3 (素材上传), Sprint 4 (AI 处理引擎), Sprint 5 (预览页), Sprint 6 (视频渲染与完成页), Sprint 7 (支付系统), Sprint 8 (部署与线上环境), Sprint 9 (端到端集成测试)
- 当前 Sprint：Sprint 9 P0/P1 bug 已修复并部署到线上

## 已修复的问题（Sprint 9 最终验收）

### P0 修复
- **视频播放器无法播放成品视频** -- 根因: `<video src="/api/tasks/{id}/stream">` 无法发送 Authorization header，导致 401
  - 修复: 后端 `_extract_token()` 函数同时支持 Authorization header 和 `?token=` query parameter 认证
  - 前端 result 页的 `<video>` 和 `<track>` 元素 URL 附带 `?token=xxx`
  - 已在线上验证: stream 和 subtitles.vtt 端点均可通过 token query param 正常认证

### P1 修复
1. **渲染页面标题显示矛盾** -- 根因: 从 rendering -> completed 状态转换时，`isRendering` 变为 false 导致标题显示"处理完成"
   - 修复: 添加 `sawRenderingRef` 追踪是否经历过渲染阶段，preview 页跳转时附带 `?mode=render` 参数
   - 现在渲染阶段正确显示"正在渲染您的视频"标题和渲染进度条
   - 渲染完成后正确显示"渲染完成"

2. **短信验证码限流太严格** -- 根因: IP 级别每小时限制 10 次
   - 修复: IP_SMS_HOURLY_LIMIT 从 10 提升到 50，LOGIN_LOCKOUT_MIN 从 5 分钟降至 2 分钟
   - 已在线上验证: 连续发送 9+ 条验证码无触发限流

## 下一个具体任务
Evaluator 应复测 Sprint 9 的验收标准，重点验证:
1. 结果页视频播放器是否能正常播放成品视频（P0 修复）
2. 渲染中页面标题和内容是否正确（P1 修复）
3. 连续发送验证码是否不会过早被限流（P1 修复）
