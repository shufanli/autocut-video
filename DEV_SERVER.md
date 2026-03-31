# Dev Server

## 本地开发

### 后端
```bash
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 前端
```bash
cd frontend
npm run dev
```

## 依赖
- Backend: `pip install -r backend/requirements.txt`
- Frontend: `cd frontend && npm install`
- FFmpeg: 必须安装 (`brew install ffmpeg` on macOS)

## 端口
- Frontend: 3000
- Backend: 8000

## API 代理
前端 Next.js 通过 `next.config.mjs` 中的 rewrites 将 `/api/*` 请求代理到后端 `http://localhost:8000/api/*`。

## 健康检查
- 后端直接: `curl http://localhost:8000/api/health`
- 前端代理: `curl http://localhost:3000/api/health`

---

## 线上环境

### 服务器信息
- IP: 120.26.41.46
- 域名: https://autocut.allinai.asia
- SSH: `ssh -i ~/.ssh/Evan_mac_air_openclaw.pem root@120.26.41.46`

### 部署目录
```
/www/wwwroot/autocut-video/
  backend/       # FastAPI 后端 + Python venv
  frontend/      # Next.js standalone build
  logs/          # PM2 日志
  ecosystem.config.js  # PM2 配置
  start-backend.sh     # 后端启动脚本
```

### 进程管理 (PM2)
```bash
pm2 list                    # 查看所有进程
pm2 logs                    # 实时日志
pm2 restart all             # 重启所有
pm2 restart autocut-backend # 重启后端
pm2 restart autocut-frontend # 重启前端
```

### 一键部署（从本地）
```bash
cd deploy
./deploy.sh
```

### Nginx 配置
- 配置文件: `/etc/nginx/conf.d/autocut.conf`
- 前端: Nginx -> :3000 (Next.js standalone)
- 后端: Nginx -> :8000 (Uvicorn)
- SSL: Let's Encrypt (自动续期)

### SSL 证书
- 证书路径: `/etc/letsencrypt/live/autocut.allinai.asia/`
- 自动续期: cron `0 0 1 * * certbot renew --quiet`
- 手动续期: `certbot renew`

### 线上健康检查
```bash
curl https://autocut.allinai.asia/api/health
```

## 认证测试
- 发送验证码: `curl -X POST http://localhost:8000/api/auth/send-code -H "Content-Type: application/json" -d '{"phone":"13800138000"}'`
- 登录 (mock 验证码 123456): `curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"phone":"13800138000","code":"123456"}'`
- 获取当前用户: `curl http://localhost:8000/api/auth/me -H "Authorization: Bearer <token>"`

## 任务与文件上传测试
- 创建任务: `curl -X POST http://localhost:8000/api/tasks -H "Authorization: Bearer <token>"`
- 上传文件: `curl -X POST http://localhost:8000/api/tasks/<task_id>/files -H "Authorization: Bearer <token>" -F "files=@test.mp4"`
- 获取任务: `curl http://localhost:8000/api/tasks/<task_id> -H "Authorization: Bearer <token>"`
- 删除文件: `curl -X DELETE http://localhost:8000/api/tasks/<task_id>/files/<file_id> -H "Authorization: Bearer <token>"`
- 排序文件: `curl -X PUT http://localhost:8000/api/tasks/<task_id>/files/reorder -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"file_ids":["id1","id2"]}'`
- 获取额度: `curl http://localhost:8000/api/quota -H "Authorization: Bearer <token>"`

## 处理管线测试 (Sprint 4)
- 触发处理: `curl -X POST http://localhost:8000/api/tasks/<task_id>/process -H "Authorization: Bearer <token>"`
- 查询状态: `curl http://localhost:8000/api/tasks/<task_id>/status -H "Authorization: Bearer <token>"`
- 处理完成后任务 status 变为 "preview"，结果存在 task_results 表中

## 预览页测试 (Sprint 5)
- 获取预览数据: `curl http://localhost:8000/api/tasks/<task_id>/preview -H "Authorization: Bearer <token>"`
- 更新口误标记和字幕样式: `curl -X PUT http://localhost:8000/api/tasks/<task_id>/preview -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"stutter_updates":[{"index":0,"action":"keep"}],"subtitle_style":"black-bg"}'`
- 预览页 URL: http://localhost:3000/preview/<task_id>

## 渲染与完成页测试 (Sprint 6)
- 启动渲染: `curl -X POST http://localhost:8000/api/tasks/<task_id>/render -H "Authorization: Bearer <token>"`
- 查询渲染进度: `curl http://localhost:8000/api/tasks/<task_id>/render-status -H "Authorization: Bearer <token>"`
- 获取结果信息: `curl http://localhost:8000/api/tasks/<task_id>/result -H "Authorization: Bearer <token>"`
- 下载视频: `curl -o output.mp4 http://localhost:8000/api/tasks/<task_id>/download -H "Authorization: Bearer <token>"`
- 播放视频流: `curl http://localhost:8000/api/tasks/<task_id>/stream -H "Authorization: Bearer <token>"`
- 获取 VTT 字幕: `curl http://localhost:8000/api/tasks/<task_id>/subtitles.vtt -H "Authorization: Bearer <token>"`
- 提交满意度反馈: `curl -X POST http://localhost:8000/api/tasks/<task_id>/feedback -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"rating":"up"}'`
- 完成页 URL: http://localhost:3000/result/<task_id>

## 支付系统测试 (Sprint 7)
- 检查下载权限: `curl http://localhost:8000/api/payments/check-download/<task_id> -H "Authorization: Bearer <token>"`
- 使用免费额度: `curl -X POST http://localhost:8000/api/payments/use-quota/<task_id> -H "Authorization: Bearer <token>"`
- 创建支付订单: `curl -X POST http://localhost:8000/api/payments/create -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"task_id":"<task_id>","payment_channel":"alipay"}'`
- 查询支付状态: `curl http://localhost:8000/api/payments/<payment_id>/status -H "Authorization: Bearer <token>"`
- 模拟支付完成: `curl -X POST http://localhost:8000/api/payments/<payment_id>/mock-pay -H "Authorization: Bearer <token>"`
- 取消支付: `curl -X POST http://localhost:8000/api/payments/<payment_id>/cancel -H "Authorization: Bearer <token>"`
- 支付流程: 有免费额度时直接下载(扣减额度); 无额度时弹出付费弹窗(9.9元)，MVP 使用 mock 支付(自动完成)

## 环境变量
- `OPENAI_API_KEY`: 可选。设置后使用 OpenAI Whisper API 进行语音识别；未设置则使用 mock 数据。
- 详见 `.env.example`

## 注意事项
- FFmpeg 如果未安装 libass（如 Homebrew 默认安装），字幕不会烧录到视频中，但会通过 WebVTT track 在播放器中显示
- 渲染失败会自动重试 1 次
- 完成的视频默认 24 小时后过期
- 线上环境使用单 worker（因为验证码存在内存中，多 worker 会导致验证码丢失）
