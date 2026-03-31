# 前端开发技能

## 概述

使用 React + Tailwind + shadcn/ui 构建 Mobile-first 的 H5 页面，适配微信生态内的分享和访问场景。

## 需要的 Skills

### ClawHub Skills（需安装）

| Skill | 安装命令 | 下载量 | 说明 |
|-------|---------|--------|------|
| **Frontend Design Ultimate** | `npx clawhub@latest install kesslerio/frontend-design-ultimate` | 11,560 | React 18 + TypeScript + Tailwind + shadcn/ui + Framer Motion，Mobile-first，anti-AI-slop 风格 |
| **Tailwind CSS** | `npx clawhub@latest install lb-tailwindcss-skill` | 1,300+ | Tailwind 完整文档参考，utility classes / 响应式 / 暗色模式 |
| **Next.js Expert** | `npx clawhub@latest install openclaw-skills-nextjs-expert` | — | Next.js 14/15 App Router + Server Components + Server Actions |

### Vercel 官方 Skills（GitHub 安装）

| Skill | 来源 | 说明 |
|-------|------|------|
| react-best-practices | `github.com/vercel-labs/agent-skills/skills/react-best-practices` | React 组件最佳实践 |
| composition-patterns | `github.com/vercel-labs/agent-skills/skills/composition-patterns` | 组件组合和复用模式 |

### Anthropic 官方 Skills

| Skill | 来源 | 说明 |
|-------|------|------|
| frontend-design | `github.com/anthropics/skills/skills/frontend-design` | Anthropic 官方前端设计 skill |
| web-artifacts-builder | `github.com/anthropics/skills/skills/web-artifacts-builder` | React + Tailwind 构建复杂页面 |

## 技术栈要求

```
框架: Next.js 14+ (App Router)
UI: Tailwind CSS + shadcn/ui
语言: TypeScript (strict mode)
动效: Framer Motion
适配: Mobile-first，375px 基准宽度
```

## 关键原则

1. **Mobile-first**：所有页面先做移动端，适配微信内访问场景
2. **Anti-AI-slop**：不要紫色渐变白色卡片，要有独特的设计语言
3. **性能优先**：首屏加载 < 2s，Lighthouse Performance > 90
4. **无障碍**：语义化 HTML，足够的对比度

## 状态：✅ 可直接使用
