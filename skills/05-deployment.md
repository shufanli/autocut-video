# 部署技能

## 概述

将应用部署到服务器，使用 Docker 容器化。部署方式由 `.env.dev` 中的服务器配置决定（如腾讯云 TAT、SSH、Vercel 等）。

## 部署方案：Docker 容器化

```
本地 Docker build → 推送代码到服务器 → 远程执行 docker-compose up
```

### 准备工作

1. 读 `.env.dev` 获取服务器信息（IP、实例 ID、Region 等）
2. 确保服务器上有 Docker 和 docker-compose
3. 准备 Dockerfile 和 docker-compose.yml

### 部署步骤

#### Step 1: 在服务器上执行命令

根据 `.env.dev` 中的服务器类型选择方式：

**腾讯云 TAT（推荐，不需要 SSH）：**
```bash
tccli tat RunCommand \
  --InstanceIds '["<INSTANCE_ID>"]' \
  --Content "$(echo -n '<COMMAND>' | base64)" \
  --CommandType SHELL \
  --Timeout 600 \
  --Region <REGION>
```

**SSH 方式：**
```bash
ssh user@server "cd /path/to/app && git pull && docker-compose up -d"
```

#### Step 2: 验证部署

```bash
# 确认前端和后端都可访问
curl -s http://<SERVER_IP>:3000 | head -20
curl -s http://<SERVER_IP>:8000/docs | head -20
```

### 首次部署（Hello World）

**部署应该是第一天的事，不是最后一步。** 第一个 commit 就应该部署一个空的 Hello World 到服务器。

## 需要的 Skills

### ClawHub Skills（需安装）

| Skill | 安装命令 | 下载量 | 说明 |
|-------|---------|--------|------|
| **Docker** | `npx clawhub@latest install ivangdavila/docker` | 7,922 | Dockerfile + Compose + 安全加固 |

### Claude Code 内置 Skills

| Skill | 命令 | 说明 |
|-------|------|------|
| Canary | `/canary` | 上线后健康监控 |

## 域名配置

域名信息在 `.env.dev` 中。通过 DNS 控制台配置 A 记录指向服务器 IP。用 Nginx + Let's Encrypt 配置 HTTPS。

## 关键原则

1. **第一天就部署** — 先部署空项目，之后增量更新
2. **容器化** — 用 Docker，不要裸跑
3. **HTTPS** — Let's Encrypt 自动续签
4. **健康检查** — 部署后验证服务可访问 + `/canary` 监控

## 需要人类提供的资源

- [ ] 服务器信息（IP、登录凭证或 TAT 实例 ID）— 写入 `.env.dev`
- [ ] 域名 DNS 管理权限

## 状态：✅ 可用，需要 .env.dev 中的服务器配置
