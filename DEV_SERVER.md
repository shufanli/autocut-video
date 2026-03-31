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
