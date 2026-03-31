# 下一步

## 当前进度
- 已完成：Sprint 1 (项目基础设施与首页), Sprint 2 (用户认证：手机号 + 验证码登录), Sprint 3 (素材上传与文件管理), Sprint 4 (AI 处理引擎), Sprint 5 (预览页：口误审核 + 字幕样式), Sprint 6 (视频渲染与完成页), Sprint 7 (支付系统与额度管理), Sprint 8 (部署与线上环境搭建)
- 当前 Sprint：Sprint 8 已完成，准备进入 Sprint 9

## 已完成的内容

### Sprint 8
- 服务器环境搭建：
  - Python 3.8.17 安装（从 yum python38 包）
  - FFmpeg 7.0.2 静态二进制安装
  - PM2 6.0.14 安装（npm global）
  - Certbot 3.0.1 安装（pip3.8）
  - rsync 安装
- 部署配置文件 (`deploy/`):
  - `nginx-autocut.conf`: Nginx 反向代理（前端 :3000 + 后端 :8000），SSL 443，gzip，安全头
  - `ecosystem.config.js`: PM2 进程管理（frontend fork + backend fork）
  - `start-backend.sh`: 后端启动脚本（venv + uvicorn single worker）
  - `deploy.sh`: 一键部署脚本（build + rsync + install deps + restart）
  - `setup-server.sh`: 服务器初始环境安装脚本
  - `.env.production`: 生产环境变量
- 代码修改：
  - `frontend/next.config.mjs`: 添加 `output: "standalone"` 用于生产部署
  - `backend/auth.py`: 修复 Python 3.8 兼容性（`dict[str, dict]` -> `Dict[str, dict]`）
  - `backend/requirements.txt`: 放宽 aiofiles 版本约束（`>=23.1.0`）
- SSL 证书：
  - Let's Encrypt 证书成功获取并部署到 Nginx
  - HTTP -> HTTPS 自动重定向
  - 自动续期 cron 任务已配置
- 线上验证：
  - https://autocut.allinai.asia 可访问
  - https://autocut.allinai.asia/api/health 返回 200
  - 登录流程正常（send-code + login + get-me）
  - 任务创建 API 正常
  - 所有页面路由返回 200

## 下一个具体任务
Evaluator 应测试 Sprint 8 的验收标准。通过后进入 Sprint 9 (端到端集成测试)。
