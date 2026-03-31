# Vendor Skills

本目录包含实验所需的所有第三方 skills，已下载到仓库内，Agent 可直接读取使用。

## Skills 清单

### 前端开发

| 目录 | 来源 | 说明 |
|------|------|------|
| `skills/frontend-design-3` | ClawHub | React 18 + TypeScript + Tailwind + shadcn/ui + Framer Motion，Mobile-first |
| `skills/anthropics-frontend-design` | ClawHub (Anthropic 官方) | Anthropic 前端设计 skill |
| `skills/anthropic-frontend-design` | GitHub anthropics/skills | Anthropic 前端设计 skill（GitHub 版） |
| `skills/anthropic-web-artifacts-builder` | GitHub anthropics/skills | React + Tailwind 构建复杂页面 |
| `skills/nextjs-expert` | ClawHub | Next.js 14/15 App Router 专家 |
| `skills/tailwindcss` | ClawHub | Tailwind CSS 完整参考 |
| `skills/vercel-react-best-practices` | GitHub vercel-labs | React 最佳实践（含 70+ rules） |
| `skills/vercel-composition-patterns` | GitHub vercel-labs | React 组件组合模式 |

### 后端开发

| 目录 | 来源 | 说明 |
|------|------|------|
| `skills/fastapi` | ClawHub | FastAPI async + Pydantic + 测试 |
| `skills/sql-toolkit` | ClawHub | SQLite/PostgreSQL/MySQL 全覆盖 |

### 支付

| 目录 | 来源 | 说明 |
|------|------|------|
| `skills/stripe-api` | ClawHub | Stripe API 集成 + OAuth |
| `skills/stripe-best-practices` | GitHub stripe/ai（官方） | Stripe 官方最佳实践（payments/billing/connect/treasury） |
| `skills/stripe-upgrade` | GitHub stripe/ai（官方） | Stripe SDK/API 升级指南 |

### 部署

| 目录 | 来源 | 说明 |
|------|------|------|
| `skills/docker` | ClawHub | Dockerfile + Compose + 网络/Volume + 安全 |

## 使用方式

Agent 在开发过程中，根据当前阶段读取对应的 SKILL.md 文件：

```
# 做前端时
读取 vendor/skills/frontend-design-3/SKILL.md
读取 vendor/skills/vercel-react-best-practices/SKILL.md

# 做后端时
读取 vendor/skills/fastapi/SKILL.md
读取 vendor/skills/sql-toolkit/SKILL.md

# 做支付时
读取 vendor/skills/stripe-best-practices/SKILL.md
读取 vendor/skills/stripe-api/SKILL.md

# 做部署时
读取 vendor/skills/docker/SKILL.md
```
