# Design System -- AI 口播视频自动剪辑

## 1. 设计哲学

- **简洁专业**：面向内容创作者，界面干净不花哨，让用户聚焦在"素材进、成品出"的核心体验
- **Mobile-first**：目标用户中微商群体大量使用手机，所有页面优先适配移动端
- **零学习成本**：不引入剪辑概念（时间线、关键帧），交互以文字稿和列表为主
- **信任感优先**：口误标记可逐条审核，每一步都让用户感到掌控

## 2. 色彩体系

### 主色（Primary）
- **Primary**: `#2563EB` (Blue-600) -- CTA 按钮、主要交互元素、进度条
- **Primary Hover**: `#1D4ED8` (Blue-700) -- 按钮悬停态
- **Primary Light**: `#DBEAFE` (Blue-100) -- 浅色背景、选中态背景
- **Primary Ultra Light**: `#EFF6FF` (Blue-50) -- 卡片悬停背景

### 功能色（Semantic）
- **Success**: `#16A34A` (Green-600) -- 上传成功、处理完成、"AI 自动决定"标签
- **Success Light**: `#DCFCE7` (Green-100) -- 成功状态背景
- **Danger**: `#DC2626` (Red-600) -- 口误标记背景、错误提示、删除按钮
- **Danger Light**: `#FEE2E2` (Red-100) -- 口误标记浅色背景（文字稿中）
- **Warning**: `#F59E0B` (Amber-500) -- 音频质量告警、额度即将用尽
- **Warning Light**: `#FEF3C7` (Amber-100) -- 告警背景

### 中性色（Neutral）
- **Background**: `#FFFFFF` -- 页面主背景
- **Surface**: `#F9FAFB` (Gray-50) -- 卡片背景、区块背景
- **Border**: `#E5E7EB` (Gray-200) -- 边框、分割线
- **Border Hover**: `#D1D5DB` (Gray-300) -- 输入框聚焦边框
- **Text Primary**: `#111827` (Gray-900) -- 标题、正文
- **Text Secondary**: `#6B7280` (Gray-500) -- 副文本、说明文字
- **Text Disabled**: `#D1D5DB` (Gray-300) -- 禁用态文本
- **Text Placeholder**: `#9CA3AF` (Gray-400) -- 输入框占位文本

### 使用规则
- CTA 按钮统一使用 Primary
- 口误标记使用 Danger Light 背景 + Danger 删除线
- 处理阶段完成使用 Success 打勾
- 文字说明使用 Text Secondary
- 不超过 3 种颜色同时出现在同一视区

## 3. 字体体系

### 字体族（Font Family）
```
主字体：Inter, -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif
等宽字体：JetBrains Mono, Fira Code, monospace（用于技术信息如文件大小、时长等）
```

### 字号比例（Type Scale）
| Token | 大小 | 行高 | 用途 |
|-------|------|------|------|
| `text-xs` | 12px | 16px | 辅助信息、版权、限制说明 |
| `text-sm` | 14px | 20px | 表单标签、按钮文字、卡片描述 |
| `text-base` | 16px | 24px | 正文、文字稿内容 |
| `text-lg` | 18px | 28px | 卡片标题、区块标题 |
| `text-xl` | 20px | 28px | 页面副标题 |
| `text-2xl` | 24px | 32px | 页面标题（移动端 Hero） |
| `text-3xl` | 30px | 36px | Hero 标题（桌面端） |
| `text-4xl` | 36px | 40px | 首页 Hero 大标题（桌面端） |

### 字重比例（Font Weight）
| Token | 值 | 用途 |
|-------|-----|------|
| `font-normal` | 400 | 正文、文字稿内容 |
| `font-medium` | 500 | 按钮文字、表单标签、卡片描述 |
| `font-semibold` | 600 | 区块标题、卡片标题、统计数字 |
| `font-bold` | 700 | 页面标题、Hero 标题 |

## 4. 间距系统

### 基准单位
- 基准单位：4px
- 所有间距均为 4 的倍数

### 间距比例
| Token | 值 | 用途 |
|-------|-----|------|
| `space-1` | 4px | 图标与文字间距、极小间隔 |
| `space-2` | 8px | 表单元素内部间距、列表项间 |
| `space-3` | 12px | 按钮内边距（水平）、紧凑组间距 |
| `space-4` | 16px | 卡片内边距、表单组间距 |
| `space-6` | 24px | 区块间距、卡片间间隔 |
| `space-8` | 32px | 大区块间距 |
| `space-12` | 48px | 页面 section 间距 |
| `space-16` | 64px | Hero 区域上下内边距 |

### 页面布局
- 最大内容宽度：1200px
- 页面水平内边距：16px（移动端）/ 24px（平板）/ 32px（桌面端）
- 导航栏高度：64px

## 5. 圆角系统

| Token | 值 | 用途 |
|-------|-----|------|
| `rounded-sm` | 4px | 小元素（标签、Badge） |
| `rounded` | 6px | 输入框、下拉选择器 |
| `rounded-md` | 8px | 按钮 |
| `rounded-lg` | 12px | 卡片、弹窗 |
| `rounded-xl` | 16px | 上传区域、大型容器 |
| `rounded-full` | 9999px | 用户头像、进度指示圆点 |

## 6. 阴影系统

| Token | 值 | 用途 |
|-------|-----|------|
| `shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | 输入框、小元素 |
| `shadow` | `0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)` | 卡片默认态 |
| `shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | 卡片悬停态、下拉菜单 |
| `shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | 弹窗、付费弹窗 |

## 7. 组件样式

### 7.1 按钮（Button）

**主按钮（Primary）**
```
背景：#2563EB → hover: #1D4ED8
文字：#FFFFFF
内边距：12px 24px
圆角：8px (rounded-md)
字号：14px, font-medium
过渡：transition-colors 150ms
禁用态：opacity 0.5, cursor not-allowed
加载态：文字替换为 spinner + "加载中..."
```

**次按钮（Secondary）**
```
背景：transparent → hover: #F9FAFB
边框：1px solid #E5E7EB → hover: #D1D5DB
文字：#374151 (Gray-700)
其余同主按钮
```

**危险按钮（Danger）**
```
背景：#DC2626 → hover: #B91C1C
文字：#FFFFFF
其余同主按钮
```

**文字按钮（Ghost）**
```
背景：transparent → hover: #F9FAFB
文字：#2563EB → hover: #1D4ED8
无边框
内边距：8px 12px
```

### 7.2 输入框（Input）

```
背景：#FFFFFF
边框：1px solid #E5E7EB → focus: 2px solid #2563EB（蓝色聚焦环）
圆角：6px (rounded)
内边距：10px 14px
字号：16px（移动端防止自动缩放）
占位文字：#9CA3AF
错误态：边框 #DC2626 + 输入框下方红色错误文字（14px）
禁用态：背景 #F9FAFB, 文字 #D1D5DB
```

### 7.3 卡片（Card）

```
背景：#FFFFFF
边框：1px solid #E5E7EB
圆角：12px (rounded-lg)
内边距：24px（桌面端）/ 16px（移动端）
阴影：shadow（默认态）→ shadow-md（悬停态）
过渡：transition-shadow 200ms
```

**特性卡片（Feature Card，首页使用）**
```
同上 + 顶部 48px 图标区域
标题：18px font-semibold #111827
描述：14px font-normal #6B7280
图标颜色：#2563EB
```

### 7.4 弹窗（Modal / Dialog）

```
遮罩层：rgba(0, 0, 0, 0.5)
弹窗容器：
  背景：#FFFFFF
  圆角：12px (rounded-lg)
  阴影：shadow-lg
  最大宽度：480px
  内边距：32px
  居中显示（vertically + horizontally）
标题：20px font-semibold
关闭按钮：右上角 X 图标
```

### 7.5 Toast 消息

```
位置：顶部居中，距顶部 24px
容器：
  背景：#111827（深色）
  文字：#FFFFFF
  圆角：8px
  内边距：12px 20px
  阴影：shadow-md
自动消失：3 秒
错误 toast：背景 #DC2626
成功 toast：背景 #16A34A
```

### 7.6 进度条（Progress Bar）

```
轨道背景：#E5E7EB
填充色：#2563EB
高度：8px
圆角：4px (rounded-sm)
过渡：width transition 300ms ease
分阶段模式（P04 处理中页）：
  已完成阶段：#2563EB 实心 + 绿色勾号
  当前阶段：#2563EB 动画（脉冲）
  未开始阶段：#E5E7EB 空心
```

### 7.7 上传区域（Upload Zone）

```
边框：2px dashed #E5E7EB → dragover: 2px dashed #2563EB
背景：#FFFFFF → dragover: #EFF6FF
圆角：16px (rounded-xl)
内边距：48px
居中内容：上传图标(48px) + 文字 + 限制说明
```

### 7.8 文字稿口误标记

```
正常文字：#111827，无背景
口误标记（将删除）：
  背景：#FEE2E2 (Red-100)
  文字：#DC2626 + 删除线
  圆角：2px
  cursor: pointer
口误标记（已恢复保留）：
  背景：transparent
  文字：#111827（正常）
  圆角：2px
  cursor: pointer
  左侧小标记：绿色竖线 2px
```

## 8. 响应式断点（Mobile-first）

| 断点 | 值 | 目标设备 |
|------|-----|---------|
| 默认 | 0px+ | 手机竖屏 |
| `sm` | 640px+ | 手机横屏、小平板 |
| `md` | 768px+ | 平板 |
| `lg` | 1024px+ | 桌面端 |
| `xl` | 1280px+ | 大桌面端 |

### 布局适配规则

**首页（P01）**
- 移动端：单列布局，特性卡片 2x2 网格
- 桌面端：单列布局，特性卡片 1x4 网格

**上传页（P03）**
- 移动端：上传区域和偏好设置纵向堆叠（100% 宽度）
- 桌面端：左右分栏（60% / 40%）

**预览页（P05）**
- 移动端：文字稿区域和字幕设置纵向堆叠
- 桌面端：左右分栏（60% / 40%）

**导航栏**
- 移动端：Logo + 右侧汉堡菜单（展开后全屏覆盖）
- 桌面端：Logo + 导航项 + 用户头像

## 9. 动效规范

| 场景 | 属性 | 时长 | 缓动函数 |
|------|------|------|---------|
| 按钮悬停 | background-color | 150ms | ease |
| 卡片悬停 | box-shadow | 200ms | ease |
| 弹窗出现 | opacity + transform(scale) | 200ms | ease-out |
| 弹窗消失 | opacity + transform(scale) | 150ms | ease-in |
| Toast 出现 | transform(translateY) + opacity | 200ms | ease-out |
| Toast 消失 | opacity | 150ms | ease-in |
| 进度条推进 | width | 300ms | ease |
| 口误标记切换 | background-color + text-decoration | 200ms | ease |
| 页面骨架屏 | background shimmer | 1.5s | linear (infinite) |

## 10. 图标规范

- 图标库：Lucide React（已安装在前端依赖中）
- 默认大小：20px（按钮内图标）、24px（导航图标）、48px（特性卡片图标）
- 颜色：跟随文本颜色或使用 Primary
- 描边宽度：1.5px（默认）

### 常用图标映射
| 场景 | 图标名 |
|------|--------|
| 上传 | `Upload` |
| 删除 | `Trash2` |
| 拖拽排序 | `GripVertical` |
| 处理中 | `Loader2`（旋转动画） |
| 完成 | `CheckCircle` |
| 失败 | `XCircle` |
| 下载 | `Download` |
| 口误标记 | `Scissors` |
| 字幕 | `Captions` |
| 设置 | `Settings` |
| 用户头像 | `User` |
| 退出 | `LogOut` |
| 返回 | `ChevronLeft` |
| 展开/折叠 | `ChevronDown` / `ChevronUp` |
| 播放 | `Play` |
| 暂停 | `Pause` |
