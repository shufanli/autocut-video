# 后端开发技能

## 概述

使用 FastAPI (Python) 或 Node.js 构建 API 服务，搭配 SQLite/PostgreSQL 数据库。

## 需要的 Skills

### ClawHub Skills（需安装）

| Skill | 安装命令 | 下载量 | 说明 |
|-------|---------|--------|------|
| **FastAPI** | `npx clawhub@latest install ivangdavila/fastapi` | 1,659 | async + Pydantic 验证 + 依赖注入 + 错误处理 + 测试 |
| **SQL Toolkit** | `npx clawhub@latest install gitgoodordietrying/sql-toolkit` | 11,700 | SQLite / PostgreSQL / MySQL 全覆盖，含 schema 设计、迁移、查询优化 |

### MCP Server（需配置）

| MCP | 配置方式 | 说明 |
|-----|---------|------|
| **dbhub** | 见 `mcp/mcp-config.md` | 零依赖数据库 MCP，支持多种数据库 |

## 技术栈要求

```
API: FastAPI (Python 3.11+) 或 Next.js API Routes
数据库: SQLite（开发阶段）→ PostgreSQL（生产）
ORM: SQLAlchemy 或 Prisma
认证: JWT / Session
```

## 关键原则

1. **API 先行**：先定义 API 接口，再实现逻辑
2. **数据库迁移**：使用 Alembic 或 Prisma Migrate，不要手动改 schema
3. **错误处理**：所有 API 有统一的错误响应格式
4. **环境隔离**：dev 和 prod 使用不同数据目录

## 状态：✅ 可直接使用
