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
