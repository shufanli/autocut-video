# SPRINT_PLAN.md — AI 口播视频自动剪辑 MVP

## 项目概要

- **产品：** AI 口播视频自动剪辑工具
- **MVP 范围：** 机械层（去口误 + 自动字幕 + 多段合并），不含 LLM 创意层
- **技术栈：** 前端 Next.js + Tailwind，后端 Python FastAPI，FFmpeg 视频处理，Whisper 语音识别
- **部署目标：** 阿里云服务器 120.26.41.46，域名 autocut.allinai.asia
- **设计规范：** 见 DESIGN.md

---

## Sprint 0 — 项目脚手架与基础设施（2 天）

### 目标
搭建前后端项目骨架、数据库、开发环境，确保团队能立即开始功能开发。

### 验收标准
- [ ] 前端项目初始化：Next.js 14+ (App Router) + Tailwind CSS + TypeScript，`npm run dev` 可启动，访问 localhost:3000 显示空白首页
- [ ] 后端项目初始化：Python 3.10+ FastAPI，`uvicorn main:app` 可启动，访问 `/docs` 显示 Swagger UI
- [ ] 数据库初始化：SQLite（MVP 简化，后续可迁移 PostgreSQL），创建 users、tasks、task_files、task_results、payments、events 六张表（schema 见 PRD 13.1）
- [ ] 目录结构清晰：`frontend/`、`backend/`、`prd/`、`docs/`
- [ ] 前端可通过 API 请求到后端（CORS 配置正确），`/api/health` 返回 `{"status": "ok"}`
- [ ] FFmpeg 命令可在本地执行（`ffmpeg -version` 正常输出）
- [ ] `.env.example` 包含所有必要的环境变量模板（参考 PRD 17.x 可配置项清单）
- [ ] 前端全局布局组件就绪：导航栏（Logo + 登录按钮占位）、页面容器（最大宽度 1200px 居中）

### 技术要点
- 后端使用 SQLAlchemy + Alembic 管理数据库迁移
- 前端使用 `next/font` 加载 Inter 字体
- 配置 Tailwind 自定义色彩 token（见 DESIGN.md 2.2）

---

## Sprint 1 — 用户认证：手机号 + 验证码登录（3 天）

### 目标
实现完整的手机号验证码登录流程，包含安全防护。

### 页面
- P02 登录页

### 验收标准
- [ ] P02 登录页 UI 完成：手机号输入框、获取验证码按钮、验证码输入框、登录按钮，样式符合 DESIGN.md
- [ ] 点击"获取验证码"：后端调用短信 API 发送 6 位验证码（MVP 可用 mock：控制台打印验证码）
- [ ] 验证码发送后按钮变为"已发送（60s）"倒计时
- [ ] 输入正确验证码后登录成功，后端返回 JWT token，前端存储并跳转
- [ ] 验证码错误：输入框下方显示红色错误提示
- [ ] 连续 3 次错误：锁定 5 分钟（可配置）
- [ ] 同一 IP 每小时验证码发送上限 10 次（可配置）
- [ ] 后端 `/api/auth/send-code`、`/api/auth/login`、`/api/auth/logout`、`/api/auth/me` 四个端点正常工作
- [ ] 前端全局 Auth 状态管理：已登录时导航栏显示用户头像（手机号后 4 位圆形色块），未登录显示"登录"按钮
- [ ] 未登录访问需认证页面时重定向到 `/login`

### 技术要点
- JWT 存储在 httpOnly cookie（安全）或 localStorage（MVP 简化）
- 验证码存储：Redis 或内存缓存（MVP 可用 Python dict + TTL）
- 新用户首次登录时自动创建 users 记录，`free_quota_remaining = 3`

---

## Sprint 2 — 首页与上传页（3 天）

### 目标
实现产品首页和素材上传功能，用户可以拖拽上传多个视频文件并排序。

### 页面
- P01 首页
- P03 上传页

### 验收标准
- [ ] P01 首页 UI 完成：Hero 区域（标题 + 副标题 + CTA 按钮）+ 4 个特性卡片 + 底部版权，符合 DESIGN.md
- [ ] 首页 CTA 按钮：未登录显示"免费试用"→ 跳转登录页；已登录显示"上传素材"→ 跳转上传页
- [ ] 移动端响应式：特性卡片 2x2 → 单列
- [ ] P03 上传页 UI 完成：左侧拖拽上传区 + 已上传文件列表（可拖拽排序）+ 右侧偏好设置（高级设置折叠）
- [ ] 拖拽上传功能正常：支持拖拽和点击选择文件
- [ ] 文件格式校验：仅接受 MP4/MOV/WebM，不支持的格式即时 toast 提示
- [ ] 文件大小校验：单文件 > 500MB 即时 toast 提示
- [ ] 已上传文件可拖拽排序，可删除单个文件
- [ ] 后端 `/api/tasks` 创建任务、`/api/tasks/{id}/files` 上传文件端点正常工作
- [ ] 上传进度条显示每个文件的上传百分比
- [ ] 偏好设置：字幕样式（3 选 1）、字幕位置（上/中/下）
- [ ] "开始处理"按钮：至少上传 1 个文件后可点击，点击后调用 `/api/tasks/{id}/process`
- [ ] 底部显示剩余免费额度："您还有 N 条免费额度"

### 技术要点
- 文件上传使用 multipart/form-data
- 后端存储上传文件到本地磁盘 `./uploads/{task_id}/`
- 拖拽排序使用 `@dnd-kit/sortable` 或原生 HTML5 Drag API

---

## Sprint 3 — 后端处理管线：合并 + 语音识别 + 口误检测 + 字幕（5 天）

### 目标
实现 MVP 核心后端处理管线，从素材合并到口误检测和字幕生成，全流程跑通。

### 验收标准
- [ ] **Stage 0 — 素材合并：** 多个视频文件按用户排序 FFmpeg concat 合并为单个视频，单文件时跳过
- [ ] **Stage 1 — 语音识别：** 调用 Whisper API（或本地 whisper 模型）对视频提取音频并转录，输出 word-level 时间戳 JSON `[{text, start_ms, end_ms, confidence}]`
- [ ] **Stage 2 — 口误检测（规则引擎）：**
  - 重复词检测：连续相同 token → 保留最后一次
  - 填充词检测：匹配可配置填充词列表（嗯/啊/那个/就是/然后）→ 标记为删除
  - 长停顿检测：相邻 token 间隔 > 1500ms → 标记为缩短至 500ms
  - 输出 `[{type, start_ms, end_ms, action}]`
- [ ] **Stage 3 — 字幕生成：** 基于 Whisper 时间戳生成逐句字幕数据 `[{text, start_ms, end_ms, style}]`
- [ ] 处理结果存入 task_results 表（agent_name + result_json）
- [ ] 任务状态流转正确：`uploading → processing → preview`
- [ ] `/api/tasks/{id}/status` 返回当前处理阶段和进度
- [ ] 处理超时（> 15 分钟）自动终止任务，状态设为 `failed`
- [ ] Whisper 低置信度告警：> 30% 片段 confidence < 0.6 时标记任务 `quality_warning`
- [ ] 处理过程中出错保留中间产物，支持重试

### 技术要点
- 使用 Python `subprocess` 调用 FFmpeg
- Whisper：优先使用 `openai.audio.transcriptions` API（word_timestamps=true），本地部署备选
- 口误检测为纯 Python 规则引擎，不依赖 LLM
- 处理任务使用后台线程或进程（MVP 简化，不引入 Celery/RQ）
- 所有可配置参数从环境变量/配置文件读取（PRD 17.2）

---

## Sprint 4 — 处理中页 + 预览页（3 天）

### 目标
用户可以看到处理进度，处理完成后查看文字稿、审核口误、设置字幕样式。

### 页面
- P04 处理中页
- P05 预览页

### 验收标准
- [ ] P04 处理中页 UI 完成：分阶段进度条（合并素材 → 语音识别 → 检测口误 & 生成字幕），当前阶段文字描述
- [ ] 进度条通过轮询 `/api/tasks/{id}/status`（每 3 秒）自动更新
- [ ] 处理完成后自动跳转预览页
- [ ] 处理超时或失败时显示错误信息 + 重试按钮
- [ ] 语音识别质量差时弹窗告警，用户可选择"继续"或"取消"
- [ ] P05 预览页 UI 完成：左侧文字稿预览（口误标红 + 删除线），右侧字幕样式设置
- [ ] 文字稿中每处口误标记可点击切换"删除/保留"
- [ ] 底部统计："共检测到 N 处口误，预计缩短 M 秒"
- [ ] 字幕样式可切换（简洁白字 / 黑底白字 / 彩色高亮），有样式预览
- [ ] 底部操作栏固定："重新处理"按钮 + "确认，开始渲染"按钮
- [ ] `/api/tasks/{id}/preview` 返回文字稿 + 口误标记 + 字幕数据
- [ ] `/api/tasks/{id}/preview` PUT 保存用户对口误的调整
- [ ] 移动端：上下堆叠布局，口误点击区域扩大到整行

### 技术要点
- 预览页数据从 task_results 表读取
- 口误切换状态通过 PUT 请求同步到后端
- 进度轮询使用 `setInterval`（MVP 简化，不用 WebSocket）

---

## Sprint 5 — 视频渲染与导出（3 天）

### 目标
用户确认预览后，后端执行 FFmpeg 渲染（剪切口误 + 烧录字幕），生成成品视频供下载。

### 验收标准
- [ ] 用户点击"确认，开始渲染"后触发 `/api/tasks/{id}/render`
- [ ] **FFmpeg 剪切：** 根据用户确认的口误删除列表，精确剪切视频段落并拼接
  - 优先使用 `-c copy` 无损剪切（最近 I-frame）
  - 若切割误差 > 500ms，回退到重编码模式 `-c:v libx264`
  - 音频拼接点 crossfade 50ms 避免爆音
- [ ] **字幕烧录：** 根据字幕数据和用户选择的样式，用 FFmpeg drawtext 或 ASS 字幕烧录到视频中
- [ ] 输出格式：MP4（H.264 + AAC），保持原始分辨率和比例
- [ ] 渲染进度可通过 `/api/tasks/{id}/render-status` 查询
- [ ] 渲染失败自动重试 1 次，仍失败则通知用户
- [ ] 渲染成功后任务状态变为 `completed`，设置 `expires_at = now + 24h`
- [ ] P06 渲染中页 UI（MVP 简化：可复用 P04 处理中页布局，单进度条）
- [ ] 渲染完成后自动跳转完成页

### 技术要点
- FFmpeg 命令通过 Python subprocess 执行
- 字幕样式预设映射到 FFmpeg drawtext 参数或 ASS 样式
- 渲染为同步阻塞任务（MVP 简化），限制并发数 ≤ 3

---

## Sprint 6 — 完成页 + 下载 + 支付（4 天）

### 目标
用户可以预览成品、下载视频。免费额度用完后触发支付流程。

### 页面
- P07 完成页（含支付弹窗）

### 验收标准
- [ ] P07 完成页 UI 完成：成功图标 + 视频播放器（HTML5 video）+ 视频信息（时长/大小/分辨率）+ 下载按钮
- [ ] 视频播放器可正常播放成品视频
- [ ] **免费额度逻辑：**
  - 有免费额度 → 点击下载 → 扣减额度 → 直接下载
  - 无免费额度 → 点击下载 → 弹出付费弹窗
- [ ] **付费弹窗：** 显示按条价格 ¥9.9 + 支付宝/微信支付选择
- [ ] **支付流程（MVP 简化）：**
  - 后端 `/api/payments/create` 创建订单，返回支付链接/二维码
  - 前端轮询 `/api/payments/{id}/status` 等待支付完成
  - 支付成功 → 弹窗关闭 → 自动开始下载
  - 支付失败/取消 → 提示"支付未完成"
- [ ] 后端 `/api/tasks/{id}/download` 返回文件流（有额度或已付费）或 `payment_required` 错误
- [ ] 灰色小字提示："视频将在 24 小时后自动删除，请及时下载"
- [ ] "处理新视频"按钮跳转上传页
- [ ] payments 表记录支付信息
- [ ] 满意度反馈：👍👎 按钮，点 👎 展开文本框（选填）

### 技术要点
- 支付接入：MVP 可先用 mock 支付（点击即成功），真实支付宝/微信支付需要商户号和审核
- 下载使用 `StreamingResponse` 返回大文件
- 视频播放器使用原生 `<video>` 标签

---

## Sprint 7 — 安全防护 + 内容审核 + 埋点（3 天）

### 目标
加入基础安全措施、内容审核和数据埋点，达到上线最低安全标准。

### 验收标准
- [ ] **反作弊：**
  - 验证码发送前增加图形验证码/滑块验证（可用简单数学题 MVP 简化）
  - 同一 IP 每小时验证码上限 10 次
  - 设备指纹识别，同一设备限制注册 2 个账号
- [ ] **内容审核：**
  - 文字稿阶段敏感词过滤（内置基础敏感词库）
  - 上传阶段视频帧抽样审核（MVP 可用简单规则或跳过，标记为 TODO）
- [ ] **安全加固：**
  - API 请求频率限制（rate limiting）
  - 文件上传类型和大小的后端二次校验
  - JWT token 过期和刷新机制
  - SQL 注入防护（SQLAlchemy 参数化查询）
  - CORS 配置仅允许前端域名
- [ ] **埋点系统：**
  - 前端埋点 SDK：封装 `trackEvent(name, params)` 方法
  - 后端 `/api/events` 批量上报端点
  - 实现 PRD 14.3 中 MVP 相关的核心事件（page_view、login_success、file_upload_start/success、process_start/complete、download_click/success、payment_start/success、satisfaction_vote）
  - events 表正常写入
- [ ] 过期视频自动清理：定时任务每小时扫描 `expires_at < now` 的任务，删除对应文件

### 技术要点
- Rate limiting 使用 slowapi 或自实现（基于 IP + 时间窗口）
- 敏感词过滤使用 DFA 算法或简单的关键词匹配
- 文件清理使用 APScheduler 或 cron job

---

## Sprint 8 — 部署上线 + 端到端测试（3 天）

### 目标
将产品部署到阿里云服务器，域名可访问，端到端流程跑通。

### 验收标准
- [ ] **服务器环境准备：**
  - 阿里云 ECS 120.26.41.46 安装 Python 3.10+（当前 3.6.8 需升级）
  - 安装 FFmpeg
  - 安装 Node.js 22+（已有）
  - 安装 PM2（进程管理）
  - 安装 Nginx（已有 1.26.1）
- [ ] **部署配置：**
  - Nginx 反向代理：`autocut.allinai.asia` → 前端 Next.js (port 3000) + 后端 FastAPI (port 8000)
  - SSL 证书配置（Let's Encrypt）
  - 上传文件目录权限正确
- [ ] **应用部署：**
  - 前端 `npm run build` + PM2 管理 Next.js 进程
  - 后端 `uvicorn` + PM2 管理 FastAPI 进程
  - 环境变量通过 `.env` 文件管理
- [ ] **端到端验证：**
  - 浏览器访问 `https://autocut.allinai.asia`，首页正常显示
  - 手机号登录流程正常（mock 验证码）
  - 上传一个真实口播视频（MP4，1-3 分钟）
  - AI 处理完成：语音识别 + 口误检测 + 字幕生成
  - 预览页正常显示文字稿和口误标记
  - 确认渲染 → 成品视频可下载播放
  - 成品视频：口误已去除、字幕正确显示、音视频同步
- [ ] **性能基线：**
  - 3 分钟视频端到端处理时间 < 5 分钟
  - 首页 Lighthouse Performance ≥ 90
- [ ] **监控基础：**
  - 应用日志输出到文件（`/var/log/autocut/`）
  - PM2 进程崩溃自动重启
  - Nginx 访问日志和错误日志

### 技术要点
- 使用 `scp` 或 `rsync` 部署代码（MVP 不引入 CI/CD）
- Nginx 配置文件上传大小限制 `client_max_body_size 600m`
- 后端文件存储路径：`/data/autocut/uploads/`

---

## Sprint 总览

| Sprint | 名称 | 天数 | 累计天数 | 核心产出 |
|--------|------|------|---------|---------|
| 0 | 项目脚手架与基础设施 | 2 | 2 | 前后端骨架 + 数据库 |
| 1 | 用户认证 | 3 | 5 | 登录页 + JWT + 安全 |
| 2 | 首页与上传页 | 3 | 8 | 首页 + 拖拽上传 + 偏好 |
| 3 | 后端处理管线 | 5 | 13 | 合并 + Whisper + 口误检测 + 字幕 |
| 4 | 处理中页 + 预览页 | 3 | 16 | 进度展示 + 口误审核 |
| 5 | 视频渲染与导出 | 3 | 19 | FFmpeg 剪切 + 字幕烧录 |
| 6 | 完成页 + 下载 + 支付 | 4 | 23 | 下载 + 免费额度 + 支付 |
| 7 | 安全 + 审核 + 埋点 | 3 | 26 | 反作弊 + 埋点 + 清理 |
| 8 | 部署上线 + E2E 测试 | 3 | 29 | 线上可访问、流程跑通 |

**总计：约 29 个工作日（6 周），符合 PRD 中 4-6 周交付预期。**

---

## 依赖与阻塞项

| 依赖 | 状态 | 影响 Sprint | 备注 |
|------|------|------------|------|
| Whisper API Key (OpenAI) | 需确认 | Sprint 3 | 无 key 则使用本地 whisper 模型 |
| 短信 API（阿里云/腾讯云） | 需确认 | Sprint 1 | MVP 可用 mock（控制台打印验证码） |
| 支付商户号（支付宝/微信） | 需申请 | Sprint 6 | MVP 先用 mock 支付 |
| 域名 SSL 证书 | 需配置 | Sprint 8 | Let's Encrypt 免费证书 |
| 服务器 Python 升级 | 需操作 | Sprint 8 | 当前 3.6.8 → 需 3.10+ |
| 服务器 FFmpeg 安装 | 需操作 | Sprint 8 | 当前未安装 |

---

## MVP 之后 (v1.1 范围，不在本计划内)

以下功能在 PRD 中标记为 v1.1，不在 MVP Sprint 计划中：

- LLM 内容理解 Agent（分析内容结构、识别关键时刻）
- 智能配乐 Agent（自动选曲 + 音量调节）
- 特效 Agent（zoom_in / shake / fade / lower_third）
- 口误清理 LLM 层（错误后重说检测）
- 完整偏好系统（视频风格 / 节奏感 / 特效强度 / 配乐开关）
- 批量任务队列
- 多比例导出（9:16 + 16:9）
- OpenClaw Skill 封装
- 历史记录页（P08）
- 账户设置页（P09）
- 推送通知
- 微信扫码登录
