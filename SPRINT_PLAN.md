# Sprint 计划

## 产品概述

**核心价值主张：** 口播视频创作者上传原始素材，AI 自动去口误、加字幕，几分钟输出可直接发布的成品视频。

**目标用户：** 口播日更/周更的内容创作者（知识博主、个人 IP、微商），技术小白，需要"量大够用"而非"极致精美"。

**MVP 范围：** 素材上传与合并 -> 语音识别 -> 口误检测（规则层） -> 字幕生成 -> 用户预览审核 -> 视频渲染导出 -> 付费下载。

**明确不在 MVP 范围内：**
- LLM 创意层（内容理解 Agent、配乐 Agent、特效 Agent）
- 方言支持、4K 视频、多比例导出
- 视频时间线编辑器、实时预览
- OpenClaw Skill、风格模板市场
- 推送通知、团队功能、国际化
- 历史记录页（P08）、账户设置页（P09）-- 归入 v1.1

---

## Sprint 1: 项目基础设施与首页

**目标：** 用户访问网站能看到完整的产品首页，了解产品功能，点击 CTA 按钮可跳转（前端脚手架 + 后端初始化 + 首页实现）

**包含页面/功能：**
- 前端：全局布局（导航栏、页脚）、首页 P01（Hero 区域、特性卡片、CTA 按钮）
- 后端：FastAPI 项目初始化（项目结构、数据库连接、健康检查接口）
- 数据库：SQLite（MVP 阶段，后续可迁移）基础表结构
- 全局样式：基于 DESIGN.md 的 Tailwind 配置确认

**验收标准：**
- [ ] 浏览器访问 `http://localhost:3000`，看到首页 Hero 区域，包含标题"口播视频，AI 一键出片"、副标题文案、CTA 按钮"免费试用"
- [ ] 首页展示 4 张特性卡片（智能去口误、自动加字幕、逐条可审核、一键出片），每张有图标、标题、描述
- [ ] 页面底部显示版权信息
- [ ] 顶部导航栏左侧显示 Logo/产品名称，右侧显示"登录"按钮
- [ ] 在手机宽度（375px）下，特性卡片变为 2x2 网格布局，页面无横向滚动
- [ ] 后端健康检查接口 `GET /api/health` 返回 200 状态码

**文件范围：**
- `frontend/src/app/` -- 首页、全局布局
- `frontend/src/components/` -- Navbar、Footer 组件
- `backend/` -- FastAPI 项目初始化、数据库模型
- `DESIGN.md` -- 设计规范（已生成）

**依赖：** 无

---

## Sprint 2: 用户认证（手机号 + 验证码登录）

**目标：** 用户可以用手机号和验证码完成登录/注册，登录后导航栏显示用户状态，已登录用户可以访问需要认证的页面

**包含页面/功能：**
- 前端：登录页 P02（手机号输入、验证码发送/输入、登录按钮、倒计时）
- 前端：AuthContext（登录状态管理）、AuthGuard（路由保护）
- 前端：导航栏登录/用户状态切换
- 后端：发送验证码 API（`POST /api/auth/send-code`，MVP 阶段用 mock 验证码如 123456）
- 后端：登录 API（`POST /api/auth/login`）、获取当前用户 API（`GET /api/auth/me`）、退出登录 API
- 后端：JWT token 认证中间件
- 数据库：users 表

**验收标准：**
- [ ] 浏览器访问 `http://localhost:3000/login`，看到登录卡片，包含手机号输入框、验证码输入框、发送验证码按钮、登录按钮
- [ ] 输入 11 位手机号后，"获取验证码"按钮变为可点击状态；点击后按钮变为"已发送(60s)"倒计时
- [ ] 输入手机号和验证码（MVP 用 mock 码 123456），点击"登录"，成功后自动跳转到上传页 `/upload`
- [ ] 登录成功后，导航栏右侧"登录"按钮变为用户头像（手机号后 4 位的圆形色块），点击展开下拉菜单（含"退出登录"）
- [ ] 未登录状态访问 `/upload`，自动跳转到登录页
- [ ] 点击"退出登录"后，导航栏恢复为"登录"按钮，再次访问 `/upload` 会跳转登录页
- [ ] 首页 CTA 按钮：未登录时显示"免费试用"，点击跳转登录页；已登录时显示"上传素材"，点击跳转上传页

**文件范围：**
- `frontend/src/app/login/` -- 登录页
- `frontend/src/lib/` -- AuthContext、API 客户端
- `frontend/src/components/` -- AuthGuard、Navbar 用户状态
- `backend/app/routers/auth.py` -- 认证路由
- `backend/app/models/` -- User 模型
- `backend/app/middleware/` -- JWT 中间件

**依赖：** Sprint 1

---

## Sprint 3: 素材上传与文件管理

**目标：** 已登录用户可以上传视频文件（支持多文件、拖拽排序），系统进行格式和大小校验，上传成功后可以开始处理

**包含页面/功能：**
- 前端：上传页 P03（拖拽上传区域、文件列表、拖拽排序、文件删除、偏好设置、"开始处理"按钮）
- 后端：创建任务 API（`POST /api/tasks`）
- 后端：文件上传 API（`POST /api/tasks/{id}/files`，multipart）
- 后端：文件排序 API（`PUT /api/tasks/{id}/files/reorder`）
- 后端：文件存储（本地磁盘，MVP 阶段）
- 数据库：tasks 表、task_files 表

**验收标准：**
- [ ] 已登录用户访问 `/upload`，看到拖拽上传区域（虚线边框 + "拖拽视频文件到此处，或点击上传"）和右侧偏好设置区域
- [ ] 点击上传区域或拖拽文件到区域，可以选择/添加视频文件，上传后文件列表显示文件名、文件大小、上传进度条
- [ ] 上传非视频文件（如 .txt），出现 toast 提示"不支持的文件格式，请上传 MP4/MOV/WebM"
- [ ] 上传完成后，文件列表中每项显示绿色勾号，可通过拖拽手柄调整文件顺序
- [ ] 文件列表每项有删除按钮，点击可移除该文件
- [ ] 右侧显示"让 AI 自动决定"标签（绿色勾号），点击"高级设置"可展开字幕样式和字幕位置选择
- [ ] 至少上传 1 个文件后，"开始处理"按钮变为可点击状态；无文件时按钮为灰色禁用
- [ ] 底部显示"您还有 N 条免费额度"提示
- [ ] 在手机宽度下，上传区域和偏好设置纵向堆叠

**文件范围：**
- `frontend/src/app/upload/` -- 上传页
- `frontend/src/components/` -- UploadZone、FileList、PreferencePanel 组件
- `backend/app/routers/tasks.py` -- 任务和文件路由
- `backend/app/models/` -- Task、TaskFile 模型
- `backend/app/services/` -- 文件存储服务

**依赖：** Sprint 2

---

## Sprint 4: AI 处理引擎（语音识别 + 口误检测 + 字幕生成）

**目标：** 用户点击"开始处理"后，系统完成素材合并、语音识别、口误检测、字幕生成的完整 Pipeline，用户在处理中页看到实时进度

**包含页面/功能：**
- 前端：处理中页 P04（分阶段进度条、当前阶段描述、预估剩余时间、取消处理）
- 后端：开始处理 API（`POST /api/tasks/{id}/process`）
- 后端：处理进度查询 API（`GET /api/tasks/{id}/status`）
- 后端：处理引擎 Pipeline（后台任务）
  - Stage 0: 素材合并（FFmpeg concat）
  - Stage 1: 语音识别（Whisper API 或 Mock）
  - Stage 2: 口误检测（规则引擎：重复词、填充词、长停顿）
  - Stage 3: 字幕生成（基于 Whisper 时间戳）
- 数据库：task_results 表（存储各 Agent 输出 JSON）

**验收标准：**
- [ ] 在上传页点击"开始处理"后，自动跳转到 `/processing/{task_id}`，看到分阶段进度条（合并素材 -> 语音识别 -> 检测口误&生成字幕）
- [ ] 进度条随处理推进，已完成阶段显示绿色勾号，当前阶段显示动画效果
- [ ] 页面显示"正在{当前阶段名称}..."文字和预估剩余时间
- [ ] 处理完成后，自动跳转到预览页 `/preview/{task_id}`
- [ ] 后端 `GET /api/tasks/{id}/status` 返回当前状态（stage、progress、estimated_time）
- [ ] 如果处理超时（>15 分钟），页面显示"处理超时" + "重试"按钮
- [ ] 点击"取消处理"弹出确认弹窗，确认后返回上传页

**文件范围：**
- `frontend/src/app/processing/[taskId]/` -- 处理中页
- `frontend/src/components/` -- ProgressSteps 组件
- `backend/app/routers/tasks.py` -- 处理和状态查询路由
- `backend/app/services/pipeline.py` -- 处理引擎编排
- `backend/app/services/merge.py` -- 素材合并（FFmpeg）
- `backend/app/services/transcribe.py` -- 语音识别（Whisper）
- `backend/app/services/stutter.py` -- 口误检测（规则引擎）
- `backend/app/services/subtitle.py` -- 字幕生成
- `backend/app/models/` -- TaskResult 模型

**依赖：** Sprint 3

---

## Sprint 5: 预览页（口误审核 + 字幕样式）

**目标：** 用户在预览页逐条审核口误标记（切换删除/保留），调整字幕样式，确认后开始渲染

**包含页面/功能：**
- 前端：预览页 P05（左侧文字稿 + 口误标记交互、右侧字幕设置、底部操作栏）
- 后端：获取预览数据 API（`GET /api/tasks/{id}/preview`）
- 后端：更新用户调整 API（`PUT /api/tasks/{id}/preview`）

**验收标准：**
- [ ] 处理完成后跳转到 `/preview/{task_id}`，左侧展示文字稿，口误片段以红色背景 + 删除线标记
- [ ] 点击某个口误标记，该标记切换为"保留"状态（红色背景消失，文字恢复正常，左侧出现绿色竖线），再次点击切回"删除"状态
- [ ] 底部显示统计："共检测到 N 处口误，预计缩短 M 秒"，当用户切换口误状态时统计实时更新
- [ ] 右侧显示字幕样式预览（当前样式名称），可通过"更换样式"切换 3 套预设（简洁白字/黑底白字/彩色高亮）
- [ ] 底部操作栏包含"重新处理"（次要按钮）和"确认，开始渲染"（主按钮）
- [ ] 点击"确认，开始渲染"后跳转到渲染/处理中页面
- [ ] 点击"重新处理"返回上传页，已上传的素材保留
- [ ] 在手机宽度下，文字稿区域和字幕设置纵向堆叠

**文件范围：**
- `frontend/src/app/preview/[taskId]/` -- 预览页
- `frontend/src/components/` -- Transcript、StutterMark、SubtitlePreview 组件
- `backend/app/routers/tasks.py` -- 预览数据和调整路由

**依赖：** Sprint 4

---

## Sprint 6: 视频渲染与完成页（下载）

**目标：** 用户确认后系统渲染成品视频（FFmpeg 剪切 + 字幕烧录），渲染完成后用户可以预览播放和下载成品

**包含页面/功能：**
- 前端：渲染进度展示（复用 P04 处理中页或独立渲染页 P06）
- 前端：完成页 P07（视频播放器、视频信息、下载按钮、满意度反馈）
- 后端：开始渲染 API（`POST /api/tasks/{id}/render`）
- 后端：渲染进度查询 API（`GET /api/tasks/{id}/render-status`）
- 后端：下载 API（`GET /api/tasks/{id}/download`）
- 后端：FFmpeg 渲染引擎（剪切 + 字幕烧录 + 音频 crossfade）
- 后端：渲染失败自动重试（1 次）

**验收标准：**
- [ ] 点击"确认，开始渲染"后进入渲染等待页面，显示渲染进度条（0%-100%）和"正在渲染视频..."文字
- [ ] 渲染完成后自动跳转到 `/result/{task_id}`，显示"视频已完成!"成功提示
- [ ] 完成页内嵌视频播放器，可播放成品视频（HTML5 video player）
- [ ] 完成页显示视频信息（时长、文件大小、分辨率）
- [ ] 点击"下载视频"按钮，浏览器开始下载 MP4 文件
- [ ] 页面显示"处理新视频"按钮，点击跳转到上传页
- [ ] 灰色小字显示"视频将在 24 小时后自动删除，请及时下载"
- [ ] 如果渲染失败，显示"渲染失败，请重试"和重试按钮

**文件范围：**
- `frontend/src/app/rendering/[taskId]/` -- 渲染中页（或复用 processing 页）
- `frontend/src/app/result/[taskId]/` -- 完成页
- `frontend/src/components/` -- VideoPlayer、SatisfactionFeedback 组件
- `backend/app/services/render.py` -- FFmpeg 渲染引擎
- `backend/app/routers/tasks.py` -- 渲染和下载路由

**依赖：** Sprint 5

---

## Sprint 7: 支付系统与额度管理

**目标：** 用户免费额度用尽后，点击下载时弹出付费弹窗，完成支付后可下载成品视频；系统正确管理免费额度和付费状态

**包含页面/功能：**
- 前端：付费弹窗（价格展示、支付方式选择、支付二维码、支付状态轮询）
- 前端：额度显示（上传页底部、完成页下载按钮状态）
- 后端：创建支付订单 API（`POST /api/payments/create`）
- 后端：查询支付状态 API（`GET /api/payments/{id}/status`）
- 后端：支付回调 API（`POST /api/payments/callback/{channel}`）
- 后端：额度管理（免费额度扣减、订阅检查）
- 后端：下载鉴权（检查额度/付费状态）
- 数据库：payments 表

**验收标准：**
- [ ] 新用户注册后，上传页底部显示"您还有 3 条免费额度"
- [ ] 有免费额度时，完成页点击"下载视频"直接开始下载，下载后额度减 1
- [ ] 免费额度为 0 时，完成页点击"下载视频"弹出付费弹窗，显示价格（按条 9.9 元）和支付方式选择（支付宝/微信支付）
- [ ] 付费弹窗中选择支付方式后显示支付二维码（MVP 可用 mock 支付流程）
- [ ] 支付成功后弹窗关闭，自动开始下载视频
- [ ] 支付取消/失败后弹窗关闭，提示"支付未完成，可稍后重新下载"
- [ ] 上传页底部的额度提示在额度变化后正确更新

**文件范围：**
- `frontend/src/components/` -- PaymentModal、QuotaDisplay 组件
- `frontend/src/app/result/[taskId]/` -- 完成页集成付费逻辑
- `backend/app/routers/payments.py` -- 支付路由
- `backend/app/services/payment.py` -- 支付服务
- `backend/app/services/quota.py` -- 额度管理服务
- `backend/app/models/` -- Payment 模型

**依赖：** Sprint 6

---

## Sprint 8: 部署与线上环境搭建

**目标：** 产品部署到阿里云服务器，用户可以通过域名访问完整的产品功能

**包含页面/功能：**
- 服务器环境搭建（Python 3.10+、FFmpeg、Nginx 反向代理、PM2 进程管理）
- 前端 Next.js 构建和部署
- 后端 FastAPI 部署（Gunicorn + Uvicorn workers）
- Nginx 配置（前端静态文件 + 后端 API 代理）
- 域名和 HTTPS 配置
- 环境变量和配置文件管理
- 基础运维（日志、进程守护）

**验收标准：**
- [ ] 通过域名（如 `https://allinai.asia` 或配置的子域名）访问，看到产品首页
- [ ] 首页加载完成，CTA 按钮可点击，跳转到登录页
- [ ] 登录流程正常（发送验证码 -> 输入验证码 -> 登录成功 -> 跳转上传页）
- [ ] 上传视频文件 -> 处理 -> 预览 -> 渲染 -> 下载，完整流程可在线上走通
- [ ] HTTPS 证书有效，浏览器无安全警告
- [ ] 后端 API 通过 Nginx 代理正常响应（`https://域名/api/health` 返回 200）

**文件范围：**
- `deploy/` -- 部署脚本、Nginx 配置、systemd 服务文件
- `backend/` -- 生产环境配置
- `.env.production` -- 生产环境变量

**依赖：** Sprint 7

---

## Sprint 9: 端到端集成测试

**目标：** 在已部署的线上产品上，走通完整用户旅程，验证所有 PRD 中定义的核心功能正常工作

**包含页面/功能：**
- 完整用户旅程测试（首次使用流程 + 老用户快速流程）
- 异常场景测试（格式校验、大小校验、网络错误提示）
- 移动端适配测试（375px 宽度）
- 性能基线检查（Lighthouse）
- 安全基线检查（API 鉴权、XSS、CSRF）
- Bug 修复和体验优化

**验收标准：**
- [ ] 首次使用旅程：访问首页 -> 点击"免费试用" -> 登录 -> 上传视频 -> 处理 -> 预览（审核口误、调整字幕）-> 渲染 -> 下载成品，全流程无阻塞
- [ ] 免费额度用尽后，下载时弹出付费弹窗，支付流程正常
- [ ] 上传非视频格式文件，出现"不支持的文件格式"提示
- [ ] 未登录访问 `/upload`，自动跳转到登录页
- [ ] 在 375px 宽度下访问所有页面，无横向滚动，布局正常
- [ ] Lighthouse Performance 得分 >= 90
- [ ] 未携带认证 token 访问 `/api/tasks` 等需认证接口，返回 401 状态码
- [ ] 口误标记可逐条切换删除/保留，统计数据正确更新
- [ ] 成品视频可在播放器中正常播放，画质和音质无明显劣化

**文件范围：** 全部代码（修复 bug 和优化涉及的文件不确定）

**依赖：** Sprint 8
