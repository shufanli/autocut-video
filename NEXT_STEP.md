# 下一步

## 当前进度
- 全部 9 个 Sprint 已完成并通过最终验收
- 产品已部署上线：https://autocut.allinai.asia
- 语音识别已优化：从 SenseVoiceSmall (无时间戳) 切换到 TeleSpeechASR (段落级时间戳)

## 完成的 Sprint
1. Sprint 1 -- 项目基础设施 + 首页
2. Sprint 2 -- 用户认证
3. Sprint 3 -- 文件上传与管理
4. Sprint 4 -- AI 处理管线
5. Sprint 5 -- 预览页 + 口误审核
6. Sprint 6 -- 视频渲染 + 完成页
7. Sprint 7 -- 支付系统
8. Sprint 8 -- 服务器部署
9. Sprint 9 -- 端到端集成测试

## 最近变更 (2026-04-01)
- P1 Bug 修复: processing 页面轮询卡住不跳转到 result 页面
  - 前端: fetchStatus 的 useCallback 依赖包含 router/showToast，导致每次 re-render 重建回调函数，useEffect 重建 interval，打断了 clearInterval + setTimeout 跳转逻辑
  - 修复方案: router/showToast 改为 ref 访问，移出 useCallback 依赖；新增 redirectingRef 守卫，一旦检测到终态即永久停止轮询
  - 后端: GET /api/tasks/{id}/status 缺少 completed 状态的处理分支，补充完整的 stage/progress 响应字段
  - 已部署上线: https://autocut.allinai.asia

- 语音识别质量优化：
  - 默认模型从 FunAudioLLM/SenseVoiceSmall 切换到 TeleAI/TeleSpeechASR
  - SenseVoiceSmall 只返回纯文本(无时间戳)，TeleSpeechASR 返回段落级时间戳
  - 新增中文正向最大匹配分词器，替代逐字符拆分
  - 分词器包含 100+ 常用中文口语词汇(成功/反正/不是/没有 等)
  - 标点符号在分词时被过滤，不再生成独立的词段
- 口误检测增强：
  - 扩展填充词列表：嗯/啊/呃/哦/那个/就是/然后/这个/就是说/怎么说/也就是
  - 新增三连重复检测(X X X)
  - 新增填充词间隔重复检测(X 嗯 X)
  - 新增部分重复/自我纠正检测(我 -> 我们)
  - 新增标记去重(避免同一词被 filler 和 repeat 双重标记)
- 已在线上服务器部署并通过端到端测试
  - 真实视频测试：318 词段，17 处口误标记(4 填充词，5 重复，8 长停顿)
  - 可删减 21.2 秒内容

## 状态：产品就绪

## 遗留 P2 优化项（非阻塞）
1. Lighthouse 性能测试待执行
2. 登录页 "MVP 测试阶段" 提示上线前应移除
3. 付费价格文案改为 "9.9 / 条"
4. 手机号输入框加 maxLength=11
5. 可考虑接入 OpenAI whisper-1 获取 word-level 时间戳(更高精度但成本更高)
