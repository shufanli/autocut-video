# DEV_SERVER.md — 开发环境启动指南

## 前置条件

- Node.js 22+ (`node --version`)
- Python 3.9+ (`python3 --version`)
- FFmpeg (`ffmpeg -version`)

## 后端启动

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后：
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

## 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端启动后：
- 页面: http://localhost:3000
- API 代理: http://localhost:3000/api/* → http://localhost:8000/api/*

## 数据库迁移

```bash
cd backend
python3 -m alembic upgrade head        # 执行迁移
python3 -m alembic revision --autogenerate -m "描述"  # 生成新迁移
```

## 目录结构

```
autocut-video/
├── frontend/          # Next.js 14 + Tailwind CSS + TypeScript
│   ├── src/
│   │   ├── app/       # App Router 页面
│   │   └── components/  # 共享组件
│   └── ...
├── backend/           # Python FastAPI
│   ├── main.py        # 入口
│   ├── models.py      # SQLAlchemy 模型 (6 tables)
│   ├── database.py    # DB engine & session
│   ├── config.py      # 环境变量配置 (PRD 17.x)
│   ├── alembic/       # 数据库迁移
│   └── requirements.txt
├── prd/               # PRD 文档
├── docs/              # 设计文档
├── .env.example       # 环境变量模板
└── DESIGN.md          # 设计规范
```
