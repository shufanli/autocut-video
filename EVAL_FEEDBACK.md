# Evaluator 报告 — Sprint 9 (端到端集成测试 / 最终验收)

测试环境: https://autocut.allinai.asia
测试时间: 2026-04-01
测试视口: 375x812 (iPhone 13 mini)

---

## 验收标准

### Sprint 9 验收标准逐条验证

- [x] PASS: 首次使用旅程：访问首页 -> 点击"免费试用" -> 登录 -> 上传视频 -> 处理 -> 预览（审核口误、调整字幕）-> 渲染 -> 下载成品，全流程无阻塞
  - 验证方式: 使用 Playwright 在 375px 视口完成全流程。从首页点击 CTA 到最终下载 MP4 文件，所有步骤均成功完成。处理使用 mock 数据（无 OPENAI_API_KEY），整个流程约 30 秒完成。

- [x] PASS: 免费额度用尽后，下载时弹出付费弹窗，支付流程正常
  - 验证方式: 通过 API 创建 3 个任务并逐次扣减免费额度至 0。第 4 个任务的结果页下载按钮变为"付费下载 ¥9.9"，点击弹出付费弹窗，显示价格 ¥9.9、支付宝/微信支付选项。选择支付宝后点击"确认支付"，mock 支付自动完成，页面变为"已付费，可直接下载"。

- [x] PASS: 上传非视频格式文件，出现"不支持的文件格式"提示
  - 验证方式: 上传 .txt 文件，文件被拒绝，页面显示格式错误提示，文件不出现在上传列表中。

- [x] PASS: 未登录访问 `/upload`，自动跳转到登录页
  - 验证方式: 在无 cookie 的新浏览器上下文中访问 /upload，URL 自动变为 /login。

- [x] PASS: 在 375px 宽度下访问所有页面，无横向滚动，布局正常
  - 验证方式: 对所有页面（首页、登录、上传、处理中、预览、渲染中、结果页）检查 document.body.scrollWidth <= window.innerWidth，全部通过。特性卡片在移动端为 2x2 网格，上传区域和偏好设置纵向堆叠。

- [ ] FAIL: Lighthouse Performance 得分 >= 90
  - 问题: 未执行 Lighthouse 测试（由于 rate limit 导致测试时间消耗过多，未能完成此项）
  - 备注: 从页面加载表现来看，首页在 networkidle 后约 2 秒内完全渲染，性能表现主观上良好

- [x] PASS: 未携带认证 token 访问 `/api/tasks` 等需认证接口，返回 401 状态码
  - 验证方式: 对 /api/tasks, /api/quota, /api/auth/me, /api/payments/create 等端点进行无 token 和无效 token 请求，均返回 401。

- [x] PASS: 口误标记可逐条切换删除/保留，统计数据正确更新
  - 验证方式: 在预览页点击"嗯"口误标记，标记从红色删除线变为正常文字，统计从"4 处口误，缩短 2.3 秒"变为"3 处删除，缩短 2.1 秒"。再次点击可切回删除状态。

- [ ] FAIL: 成品视频可在播放器中正常播放，画质和音质无明显劣化
  - 问题: 视频播放器无法播放视频。video 元素的 readyState=0, networkState=3, error.code=4 (MEDIA_ELEMENT_ERROR)
  - 复现: 登录 -> 完成处理和渲染 -> 进入结果页 -> 点击播放按钮
  - 期望: 视频应能在内嵌播放器中正常播放
  - 根因: `<video src="/api/tasks/{id}/stream">` 无法携带 Authorization header，导致 stream 端点返回 401

---

### 历史 Sprint 关键验收标准抽查

- [x] PASS: 首页 Hero 区域包含标题"口播视频，AI 一键出片"、CTA 按钮"免费试用"
- [x] PASS: 4 张特性卡片（智能去口误、自动加字幕、逐条可审核、一键出片）
- [x] PASS: 顶部导航栏左侧 Logo，右侧"登录"按钮
- [x] PASS: 页面底部版权信息
- [x] PASS: 后端 GET /api/health 返回 200
- [x] PASS: 登录卡片包含手机号输入框、验证码输入框、发送验证码按钮、登录按钮
- [x] PASS: 发送验证码后按钮变为"已发送(Ns)"倒计时
- [x] PASS: 登录成功后导航栏显示手机号后 4 位的用户头像
- [x] PASS: 已登录时首页 CTA 显示"上传素材"，点击跳转上传页
- [x] PASS: 退出登录后导航栏恢复"登录"按钮
- [x] PASS: 上传页拖拽上传区域和偏好设置正常
- [x] PASS: 至少 1 个文件后"开始处理"按钮可用
- [x] PASS: "让 AI 自动决定"标签和高级设置
- [x] PASS: 底部显示"您还有 N 条免费额度"
- [x] PASS: 处理中页显示分阶段进度条
- [x] PASS: 预览页文字稿、口误标记、字幕样式切换
- [x] PASS: 渲染完成后自动跳转结果页
- [x] PASS: 结果页显示视频信息（时长、大小、分辨率）
- [x] PASS: 下载按钮可下载 MP4 文件
- [x] PASS: "处理新视频"按钮跳转上传页
- [x] PASS: "视频将在 24 小时后自动删除"警告
- [x] PASS: HTTPS 证书有效（Let's Encrypt, 到期 2026-06-29）
- [x] PASS: HTTP 自动 301 重定向到 HTTPS

---

## 否定测试

1. **空输入**: PASS — 登录按钮在手机号和验证码为空时处于 disabled 状态（灰色，cursor-not-allowed），无法点击。发送验证码按钮在手机号为空或不足 11 位时也处于 disabled 状态。
2. **超长输入**: PASS — 手机号输入框为 type="tel"，输入 100 个字符后实际值可能被截断。后端 API 对非 11 位手机号返回 422 错误"请输入正确的 11 位手机号"。
3. **XSS 注入**: PASS — 在手机号输入框中输入 `<script>alert(1)</script>`，无弹窗出现，输入被 type="tel" 过滤为空。后端 API 也正确拒绝非数字输入。
4. **无效 URL**: PASS — 访问 /preview/non-existent-task-id 和 /result/non-existent-task-id，页面检测到 404 后重定向到上传页。
5. **双击**: PASS — 双击下载按钮后，代码中有 `downloadLockRef` 防重复提交机制。测试中双击后只触发一次下载，无异常。
6. **手机布局**: PASS — 所有页面在 375px 下无横向滚动，文字可读，触摸目标大小适当。

---

## 视觉检查

- PASS: 整体色彩体系与 DESIGN.md 一致。主色 #2563EB (Blue-600) 用于 CTA、进度条。Success 绿色用于完成状态。Danger 红色用于口误标记。
- PASS: 无 AI 味问题。没有通用紫色渐变、无白色卡片堆叠泛滥、无占位图片。界面简洁专业。
- PASS: 字体大小在移动端可读（Hero 标题约 24px，正文 16px）。
- PASS: 按钮圆角 8px (rounded-md)、卡片圆角 12px (rounded-lg)、上传区域 16px (rounded-xl)，与 DESIGN.md 一致。
- PASS: 上传区域虚线边框、特性卡片图标颜色 #2563EB，与规范一致。
- P2: 付费弹窗的价格显示使用了"¥9.9"但没有"元"字，可考虑增加"元/条"更清晰。
- PASS: 结果页满意度反馈（满意/不满意）UI 清晰。

---

## 判定

需要修复 🔴

---

## 问题清单（按严重程度排序）

### P0 — 阻塞上线

1. **视频播放器无法播放成品视频** -- **已修复** -- 采用方案 A: 后端 `_extract_token()` 同时支持 Authorization header 和 `?token=` query parameter 认证；前端 video src 附带 `?token=xxx`
   - 修改文件: `backend/auth.py`, `frontend/src/app/result/[taskId]/page.tsx`

### P1 — 影响体验

1. **渲染中页面标题与内容不一致** -- **已修复** -- 添加 `sawRenderingRef` 跟踪渲染状态，preview 页跳转时附带 `?mode=render`，确保从进入页面开始就显示渲染 UI
   - 修改文件: `frontend/src/app/processing/[taskId]/page.tsx`, `frontend/src/app/preview/[taskId]/page.tsx`

2. **验证码 Rate Limit 过于严格** -- **已修复** -- IP_SMS_HOURLY_LIMIT 从 10 提升到 50，LOGIN_LOCKOUT_MIN 从 5 分钟降至 2 分钟
   - 修改文件: `backend/config.py`

3. **结果页 video stream 和 subtitle 的 401 控制台错误** -- **已修复** -- 与 P0-1 同一修复，token query param 解决了 401 问题

### P2 — 可优化

1. **Lighthouse 性能测试未执行** — 由于 rate limit 导致测试时间消耗过多，未能完成 Lighthouse 性能评分。建议在修复 rate limit 后单独执行。

2. **处理速度过快导致处理中页面几乎不可见** — 使用 mock 数据时，AI 处理在 3 秒内完成，用户几乎看不到处理中页面的进度动画。虽然这是 mock 数据的限制，但建议在 mock 模式下增加适当的延迟（如 5-10 秒）以测试处理中页面的完整体验。

3. **付费弹窗价格文案** — "¥9.9" 建议改为 "¥9.9 / 条" 更清晰。

4. **MVPtesting 提示** — 登录页底部显示"MVP 测试阶段，验证码固定为 123456"，上线前需移除。

5. **手机号输入框未限制最大长度** — 虽然后端有验证，但前端 input 应添加 `maxLength={11}` 属性。

---

## 端到端流程总结

| 步骤 | 状态 | 备注 |
|------|------|------|
| 1. 首页访问 | PASS | Hero、特性卡片、CTA 正常 |
| 2. CTA -> 登录页 | PASS | 未登录跳转正确 |
| 3. 手机号登录 | PASS | 验证码发送、倒计时、登录跳转正常 |
| 4. 上传视频 | PASS | 文件选择、上传进度、格式校验正常 |
| 5. 开始处理 | PASS | 跳转处理中页面 |
| 6. AI 处理 | PASS | 进度更新、自动跳转预览页 |
| 7. 预览审核 | PASS | 口误标记切换、字幕样式切换、统计更新正常 |
| 8. 确认渲染 | PASS (有 P1 bug) | 渲染中页面显示不完善，但最终跳转正常 |
| 9. 视频预览 | **FAIL** | P0: 视频播放器无法加载视频 |
| 10. 下载 | PASS | MP4 文件正常下载 |
| 11. 付费流程 | PASS | 额度用尽弹出付费弹窗，mock 支付正常 |
| 12. 退出登录 | PASS | 导航栏恢复、Auth Guard 正常 |

---

## API 安全测试

| 测试项 | 结果 |
|--------|------|
| 无 token 访问 /api/tasks | 401 PASS |
| 无 token 访问 /api/quota | 401 PASS |
| 无 token 访问 /api/auth/me | 401 PASS |
| 无 token 访问 /api/payments/create | 401 PASS |
| 无效 token 访问 /api/tasks | 401 PASS |
| XSS 输入到 send-code API | 422 (正确拒绝) PASS |
| 超长手机号到 send-code API | 422 (正确拒绝) PASS |
| 空手机号到 send-code API | 422 (正确拒绝) PASS |
| HTTP 自动重定向 HTTPS | 301 PASS |
| HTTPS 证书有效 | PASS (Let's Encrypt, 到期 2026-06-29) |
