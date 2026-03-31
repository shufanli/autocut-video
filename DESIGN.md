# DESIGN.md — AI 口播视频自动剪辑 MVP 设计规范

## 1. 设计理念

**核心原则：** 零学习成本、极简操作、信任感优先。

用户画像是"技术小白的口播创作者"，界面必须：
- 不出现任何剪辑专业术语（时间线、关键帧、码率等）
- 每一步只有 1 个主要操作（上传→等待→审核→下载）
- AI 的每处修改都可见、可撤回，传达安全感

## 2. 品牌与色彩

### 2.1 品牌调性
- **关键词：** 专业、高效、可信赖
- **语气：** 友好但不花哨，像一个靠谱的助手

### 2.2 色彩系统

| 角色 | 色值 | 用途 |
|------|------|------|
| Primary | `#2563EB` (Blue-600) | CTA 按钮、主要交互元素 |
| Primary Hover | `#1D4ED8` (Blue-700) | 按钮 hover 状态 |
| Success | `#16A34A` (Green-600) | 成功状态、完成标记 |
| Danger / Delete | `#DC2626` (Red-600) | 口误标记、删除操作、错误提示 |
| Warning | `#F59E0B` (Amber-500) | 告警提示 |
| Background | `#FFFFFF` | 页面主背景 |
| Surface | `#F9FAFB` (Gray-50) | 卡片、区块背景 |
| Border | `#E5E7EB` (Gray-200) | 边框、分割线 |
| Text Primary | `#111827` (Gray-900) | 主要文字 |
| Text Secondary | `#6B7280` (Gray-500) | 辅助文字、说明文字 |
| Text Disabled | `#D1D5DB` (Gray-300) | 禁用状态文字 |

### 2.3 暗色模式
MVP 不做暗色模式。

## 3. 排版

### 3.1 字体
- **中文：** `"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif`
- **英文/数字：** `"Inter", -apple-system, BlinkMacSystemFont, sans-serif`
- **代码/等宽：** `"JetBrains Mono", "Fira Code", monospace`（仅用于技术信息如 task_id）

### 3.2 字号体系

| 级别 | 桌面端 | 移动端 | 行高 | 用途 |
|------|--------|--------|------|------|
| H1 | 36px / 2.25rem | 28px / 1.75rem | 1.2 | 首页主标题 |
| H2 | 24px / 1.5rem | 20px / 1.25rem | 1.3 | 页面标题 |
| H3 | 18px / 1.125rem | 16px / 1rem | 1.4 | 区块标题 |
| Body | 16px / 1rem | 15px / 0.9375rem | 1.6 | 正文、文字稿 |
| Small | 14px / 0.875rem | 13px / 0.8125rem | 1.5 | 辅助信息、时间戳 |
| Caption | 12px / 0.75rem | 12px / 0.75rem | 1.5 | 极小提示 |

### 3.3 字重
- Regular 400: 正文
- Medium 500: 按钮文字、标签
- Semibold 600: 标题
- Bold 700: 强调（极少使用）

## 4. 间距系统

基于 4px 网格：

| Token | 值 | 用途 |
|-------|------|------|
| `space-1` | 4px | 图标与文字间距 |
| `space-2` | 8px | 紧凑元素间距 |
| `space-3` | 12px | 表单元素内部 |
| `space-4` | 16px | 卡片内边距、列表项间距 |
| `space-6` | 24px | 区块间距 |
| `space-8` | 32px | 大区块分隔 |
| `space-12` | 48px | 页面区块分隔 |
| `space-16` | 64px | 首页大区块分隔 |

## 5. 组件规范

### 5.1 按钮

| 类型 | 样式 | 用途 |
|------|------|------|
| Primary | `bg-blue-600 text-white rounded-lg px-6 py-3` | CTA、主操作（"开始处理"、"确认渲染"、"下载视频"） |
| Secondary | `bg-white text-gray-700 border border-gray-300 rounded-lg px-6 py-3` | 次要操作（"重新处理"、"取消"） |
| Danger | `bg-red-600 text-white rounded-lg px-4 py-2` | 危险操作（删除文件） |
| Text | `text-blue-600 underline-offset-2` | 文字链接（"高级设置"、"联系客服"） |
| Disabled | `bg-gray-200 text-gray-400 cursor-not-allowed` | 禁用状态 |

**按钮规则：**
- 最小宽度 120px（桌面端）/ 全宽（移动端）
- 圆角 8px (`rounded-lg`)
- Loading 状态：文字替换为 spinner + "处理中..."
- 禁止重复点击：点击后立即 disable

### 5.2 输入框

```
border border-gray-300 rounded-lg px-4 py-3 text-base
focus: border-blue-500 ring-2 ring-blue-500/20
error: border-red-500 ring-2 ring-red-500/20
```

- 错误提示文字：红色，显示在输入框下方，`text-sm text-red-600`

### 5.3 卡片

```
bg-white rounded-xl shadow-sm border border-gray-100 p-6
```

- 内边距 24px
- hover 效果（如可点击）：`hover:shadow-md transition-shadow`

### 5.4 上传区域（拖拽区）

```
border-2 border-dashed border-gray-300 rounded-xl p-12 text-center
hover: border-blue-400 bg-blue-50/50
dragging: border-blue-500 bg-blue-50
```

### 5.5 进度条

```
bg-gray-200 rounded-full h-2
进度填充: bg-blue-600 rounded-full transition-all duration-500
```

### 5.6 Toast 通知

- 位置：右上角，距顶部 24px
- 自动消失：3 秒
- 类型：success (绿色边框)、error (红色边框)、info (蓝色边框)

### 5.7 弹窗 (Modal)

```
背景遮罩: bg-black/50
弹窗体: bg-white rounded-2xl shadow-xl p-8 max-w-md mx-auto
```

## 6. 布局

### 6.1 响应式断点

| 断点 | 宽度 | 布局 |
|------|------|------|
| Mobile | < 768px | 单列布局，操作按钮全宽 |
| Tablet | 768px - 1024px | 双列布局开始 |
| Desktop | > 1024px | 完整双列布局（上传页/预览页 60:40） |

### 6.2 导航栏

- 高度：64px
- 背景：白色 + 底部 1px 灰色分割线
- Logo 左对齐，用户操作右对齐
- 移动端：Logo 居中，汉堡菜单右上角

### 6.3 页面最大宽度

- 内容区最大宽度：1200px，居中
- 首页 hero 区域：全宽背景色，内容 1200px 居中

## 7. 关键页面设计要点

### 7.1 P01 首页
- Hero 区域垂直居中，CTA 按钮醒目
- 特性卡片 4 列（桌面）→ 2x2（平板）→ 单列（手机）
- 首屏必须包含 CTA，不需要滚动

### 7.2 P03 上传页
- 左右分栏（60:40），移动端上下堆叠
- 拖拽区域要足够大（至少 300px 高），视觉焦点
- 已上传文件列表：每项一行，拖拽排序手柄在左侧
- "高级设置"默认折叠，降低决策负担

### 7.3 P05 预览页
- 左右分栏（60:40），移动端上下堆叠
- 文字稿中口误高亮：`bg-red-100 text-red-800 line-through cursor-pointer`
- 口误已恢复状态：`bg-green-50 text-green-800 no-underline`
- 每处口误可点击切换，无需额外按钮
- 底部操作栏固定（sticky），不被文字稿内容遮挡

### 7.4 P07 完成页
- 成功大图标 + 庆祝感
- 视频播放器居中，宽度不超过 640px
- 下载按钮大而醒目

## 8. 动效规范

- 页面切换：无动效（MVP 简化）
- 按钮 hover：`transition-colors duration-150`
- 进度条推进：`transition-all duration-500 ease-out`
- Toast 出现/消失：`transition-opacity duration-300`
- 口误标记切换：`transition-colors duration-200`

**原则：** 动效仅用于反馈（用户操作后的即时反馈），不用于装饰。

## 9. 可访问性

- 所有交互元素可键盘访问（Tab 顺序合理）
- 按钮有 focus ring（`focus:ring-2 focus:ring-blue-500`）
- 颜色对比度符合 WCAG AA（正文 ≥ 4.5:1，大字 ≥ 3:1）
- 图标配合文字，不单独用图标传达关键信息
- 上传区域支持键盘触发文件选择

## 10. 移动端适配要点

- Touch target 最小 44x44px
- 手机号输入框使用 `inputmode="numeric"`
- 验证码输入框使用 `inputmode="numeric"` + `autocomplete="one-time-code"`
- 文字稿口误标记：点击区域扩大到整行（而非仅文字范围）
- 底部操作栏在移动端固定底部，增加安全区域 padding

## 11. 技术实现约定

- **CSS 框架：** Tailwind CSS v3
- **组件库：** 不引入第三方 UI 库，自建组件（减少依赖）
- **图标：** Lucide Icons（轻量、开源）
- **字体加载：** Inter 通过 `next/font` 内置加载，中文使用系统字体
- **图片格式：** WebP 优先，PNG fallback
- **暗色模式：** MVP 不支持，代码中不需要 `dark:` 类名

## 12. 部署相关

- **域名：** `autocut.allinai.asia`
- **服务器：** 阿里云 ECS `120.26.41.46`
- **前端：** Next.js SSR，Nginx 反向代理
- **后端：** Python FastAPI，Nginx 反向代理
- **静态资源：** 通过 Nginx 直接服务，启用 gzip
