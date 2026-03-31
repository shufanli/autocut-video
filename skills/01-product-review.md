# 产品审视技能

## 概述

从 PRD 出发，通过三轮审视建立产品基线：明确产品价值、用户路径、MVP 范围和视觉设计方向。

## 需要的 Skills

这些是 Claude Code 内置的 gstack skills，直接用斜杠命令调用：

| Skill | 命令 | 用途 |
|-------|------|------|
| Office Hours | `/office-hours` | 产品价值梳理、核心问题定义、用户画像 |
| CEO Review | `/plan-ceo-review` | 挑战前提假设、明确核心价值、关键路径、MVP 定义 |
| Design Review | `/plan-design-review` | 设计维度评分、UI/UX 方向确定 |
| Design Consultation | `/design-consultation` | 创建设计系统（配色、字体、间距、动效） |

## 使用流程

### Step 1: Office Hours

```
/office-hours
```

输入 PRD 的产品概述部分。回答六个核心问题：
- 用户是谁？他们现在怎么解决这个问题？
- 为什么现在是做这个的时机？
- 你的独特洞察是什么？

产出物：`docs/office-hours-output.md`

### Step 2: CEO Review

```
/plan-ceo-review
```

基于 Office Hours 的产出和 PRD，进行 CEO 视角审视：
- 这个产品的核心价值是什么？一句话说清楚
- 用户的关键路径是什么？最短几步完成核心体验？
- MVP 的边界在哪？哪些功能必须有，哪些可以砍？

产出物：`docs/ceo-review-output.md`

### Step 3: Design Review

```
/plan-design-review
```

审视 PRD 中的页面设计，评分并优化：
- 视觉层级是否清晰？
- 关键操作路径是否无脑？
- Mobile-first 是否落实？

产出物：`docs/design-review-output.md`

### Step 4: Design System

```
/design-consultation
```

基于审视结论，创建项目的设计系统：
- 配色方案
- 字体选择
- 间距规范
- 组件风格

产出物：`DESIGN.md`

## 状态：✅ 可直接使用
