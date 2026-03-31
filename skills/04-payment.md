# 支付集成技能

## 概述

使用 Stripe 实现支付功能，包括一次性付款和订阅。具体价格和套餐由 PRD 定义。优先用 Stripe 而非支付宝，因为 Stripe 的自动化测试和 API 生态更成熟。

## 需要的 Skills

### ClawHub Skills（需安装）

| Skill | 安装命令 | 下载量 | 说明 |
|-------|---------|--------|------|
| **Stripe API** | `npx clawhub@latest install byungkyu/stripe-api` | 18,800 | Stripe API 集成 + OAuth，管理 customers/subscriptions/invoices/payments |

### GitHub Skills（需手动引入）

| Skill | 来源 | 说明 |
|-------|------|------|
| **stripe-best-practices** | `github.com/stripe/ai/skills/stripe-best-practices` | Stripe 官方出品，指导 API 选型（Checkout Sessions vs PaymentIntents）、订阅管理、webhook 集成 |
| **upgrade-stripe** | `github.com/stripe/ai/skills/upgrade-stripe` | Stripe SDK 和 API 版本升级指南 |

### MCP Server（需配置）

| MCP | 配置方式 | 说明 |
|-----|---------|------|
| **Stripe MCP** | `npx -y @stripe/mcp --api-key=sk_test_xxx` | Stripe 官方 MCP Server，25 个工具覆盖全部支付场景 |

也可使用远程 MCP：`mcp.stripe.com`（支持 OAuth）

## 实现方案

### 一次性付款

```
推荐方案: Stripe Checkout Session (mode: 'payment')
流程: 用户点击付费按钮 → 跳转 Stripe Checkout 页面 → 支付成功 → Webhook 回调 → 发放权益
```

### 订阅

```
推荐方案: Stripe Checkout Session (mode: 'subscription')
流程: 用户点击订阅按钮 → 跳转 Stripe Checkout → 订阅成功 → Webhook 管理续费/取消
```

### 测试

```
测试卡号: 4242 4242 4242 4242
测试密钥: sk_test_xxx（需人类提供）
Webhook 本地测试: stripe listen --forward-to localhost:8000/webhook
```

## 关键原则

1. **先跑通测试环境**：用 Stripe 测试密钥和测试卡号走通全流程
2. **Webhook 是核心**：不要轮询 API 检查支付状态，用 Webhook 异步通知
3. **幂等性**：Webhook 可能重复发送，处理逻辑必须幂等
4. **降级方案**：Stripe 不可用时的兜底（展示"支付暂时不可用"而非白屏）

## 需要人类提供的资源

- [ ] Stripe API Key（测试环境 sk_test_xxx）
- [ ] Stripe Webhook Signing Secret
- [ ] 生产环境 API Key（上线前提供）

如未获得以上资源，记录到 `BLOCKED.md` 等待人类处理。

## 状态：✅ Skill 可用，⚠️ 需要 API Key 才能实际运行
