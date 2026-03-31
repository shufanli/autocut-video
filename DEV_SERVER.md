# Dev Server

## 启动方式

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

## 环境变量
- `OPENAI_API_KEY`: 可选。设置后使用 OpenAI Whisper API 进行语音识别；未设置则使用 mock 数据。
- 详见 `.env.example`

## 注意事项
- FFmpeg 如果未安装 libass（如 Homebrew 默认安装），字幕不会烧录到视频中，但会通过 WebVTT track 在播放器中显示
- 渲染失败会自动重试 1 次
- 完成的视频默认 24 小时后过期
