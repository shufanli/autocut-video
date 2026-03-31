# 下一步

## 当前进度
- 已完成：Sprint 1 (项目基础设施与首页), Sprint 2 (用户认证：手机号 + 验证码登录), Sprint 3 (素材上传与文件管理), Sprint 4 (AI 处理引擎), Sprint 5 (预览页：口误审核 + 字幕样式), Sprint 6 (视频渲染与完成页), Sprint 7 (支付系统与额度管理)
- 当前 Sprint：Sprint 7 已完成，准备进入 Sprint 8

## 已完成的内容

### Sprint 7
- 后端支付模块 (`backend/payments.py`):
  - POST /api/payments/create：创建支付订单（支持 alipay/wechat channel）
  - GET /api/payments/{id}/status：查询支付状态（前端轮询用）
  - POST /api/payments/{id}/mock-pay：MVP mock 支付（模拟用户完成支付）
  - POST /api/payments/{id}/cancel：取消待支付订单
  - POST /api/payments/callback/{channel}：支付回调（MVP 占位）
  - GET /api/payments/check-download/{task_id}：检查下载权限（free_quota/paid/needs_payment）
  - POST /api/payments/use-quota/{task_id}：扣减免费额度（防重复扣减）
- 后端 main.py：注册 payments router
- 前端 PaymentModal 组件 (`frontend/src/components/payment-modal.tsx`):
  - 4 步骤：选择支付方式 -> 等待支付 -> 支付成功 -> 支付失败
  - 支付方式选择：支付宝/微信支付，radio 按钮样式
  - 价格展示：¥9.9，居中突出显示
  - Mock QR 区域：显示 loading 动画模拟扫码
  - 支付状态轮询：1.5s 间隔轮询 payment status
  - MVP mock：创建订单后 2s 自动触发 mock-pay
  - 支付成功后 1.2s 延迟展示 success UI 再自动下载
  - 取消支付时自动 cancel pending 订单
- 前端完成页更新 (`frontend/src/app/result/[taskId]/page.tsx`):
  - 下载按钮集成额度检查：先 check-download，有 free_quota 则 use-quota + download
  - 无额度时弹出 PaymentModal
  - 支付成功后 modal 关闭 + 自动下载
  - 支付取消/失败 toast "支付未完成，可稍后重新下载"
  - 下载按钮显示上下文信息（剩余额度/已付费/需付费）
  - useRef 防双击下载
  - refreshUser() 更新 auth context 中的额度
- CSS 新增 modal-in 动画（scale 0.95 -> 1）
- 数据库 payments 表已存在（Sprint 1 建表时已创建）

## 下一个具体任务
Evaluator 应测试 Sprint 7 的验收标准。通过后进入 Sprint 8 (部署与线上环境搭建)。
