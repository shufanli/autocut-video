# QA 测试 + 安全审计技能

## 概述

对产品进行功能测试、视觉测试、性能测试和安全审计，确保上线质量。

## Claude Code 内置 Skills（直接可用）

### QA 测试

| Skill | 命令 | 说明 |
|-------|------|------|
| **QA 测试** | `/qa` | 系统性功能测试 → 发现 bug → 修复 → 验证。三档：Quick / Standard / Exhaustive |
| **QA 报告** | `/qa-only` | 只报告不修复，产出 bug 清单和健康分 |
| **浏览器测试** | `/browse` | 无头浏览器，导航页面、交互元素、截图、验证状态 |
| **性能基准** | `/benchmark` | Lighthouse / Core Web Vitals / 资源大小基准 |

### 安全

| Skill | 命令 | 说明 |
|-------|------|------|
| **安全审计** | `/cso` | OWASP Top 10 + STRIDE 威胁建模 + 密钥检测 + 依赖 CVE 扫描 |

### 代码审查

| Skill | 命令 | 说明 |
|-------|------|------|
| **PR Review** | `/review` | 分析 diff，检查 SQL 安全、LLM 信任边界、条件副作用 |
| **Codex 二审** | `/codex` | 独立的第二意见，adversarial 模式尝试打破你的代码 |

### 设计 QA

| Skill | 命令 | 说明 |
|-------|------|------|
| **设计审视** | `/design-review` | 视觉一致性、间距、层级、AI slop 检测，逐个修复并截图验证 |

## 使用流程

### 开发阶段

每完成一个功能模块：

```
1. /qa-only          → 产出 bug 报告
2. /qa               → 自动修复发现的 bug
3. /review           → 审查代码质量
4. /design-review    → 审查视觉质量
```

### 上线前

```
1. /qa exhaustive    → 全面测试（含 cosmetic 级别）
2. /benchmark        → 性能基准测试
3. /cso              → 安全审计
4. /codex challenge  → adversarial 模式尝试打破
```

### 上线后

```
1. /canary           → 持续监控线上健康
```

## 关键原则

1. **生成和评估分离**（来自 Anthropic harness 设计博文）：不要自己评价自己的代码，用独立的 QA/Review skill
2. **每个功能都测**：不要攒到最后集中测
3. **安全不是最后一步**：开发过程中就用 `/cso` 检查

## 状态：✅ 全部内置，直接可用
