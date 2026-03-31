# 微信 H5 开发技能

## 概述

微信生态内的裂变链路：用户在微信里看到分享 → 点击打开 H5 页面 → 使用产品 → 分享成绩到微信群/朋友圈。这需要微信 JS-SDK 的分享能力。

## 当前状态：🔴 无现成 skill，需要自建

社区搜索结果：
- ClawHub：无微信 H5 JS-SDK skill
- MCP 市场：无微信 JS-SDK MCP
- GitHub：有微信消息读写的 MCP（WeChat-MCP），但无 H5 开发相关

## 需要自建的能力

### 微信 JS-SDK 分享功能

#### 后端（签名服务）

```python
# FastAPI 示例
import hashlib, time, requests

@app.get("/api/wechat/signature")
async def get_wx_signature(url: str):
    # 1. 获取 access_token
    token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
    access_token = requests.get(token_url).json()["access_token"]

    # 2. 获取 jsapi_ticket
    ticket_url = f"https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token={access_token}&type=jsapi"
    ticket = requests.get(ticket_url).json()["ticket"]

    # 3. 生成签名
    noncestr = "random_string"
    timestamp = str(int(time.time()))
    sign_str = f"jsapi_ticket={ticket}&noncestr={noncestr}&timestamp={timestamp}&url={url}"
    signature = hashlib.sha1(sign_str.encode()).hexdigest()

    return {"appId": APPID, "timestamp": timestamp, "nonceStr": noncestr, "signature": signature}
```

#### 前端（JS-SDK 调用）

```javascript
// 1. 引入 JS-SDK
<script src="https://res.wx.qq.com/open/js/jweixin-1.6.0.js"></script>

// 2. 配置
const config = await fetch(`/api/wechat/signature?url=${encodeURIComponent(location.href)}`).then(r => r.json())
wx.config({
  debug: false,
  appId: config.appId,
  timestamp: config.timestamp,
  nonceStr: config.nonceStr,
  signature: config.signature,
  jsApiList: ['updateAppMessageShareData', 'updateTimelineShareData']
})

// 3. 设置分享内容（根据 PRD 调整文案和链接）
wx.ready(() => {
  // 分享给朋友
  wx.updateAppMessageShareData({
    title: '分享标题（由 PRD 定义）',
    desc: '分享描述',
    link: `https://YOUR_DOMAIN/share/${userId}`,
    imgUrl: 'https://YOUR_DOMAIN/share-cover.png'
  })

  // 分享到朋友圈
  wx.updateTimelineShareData({
    title: '朋友圈标题（由 PRD 定义）',
    link: `https://YOUR_DOMAIN/share/${userId}`,
    imgUrl: 'https://YOUR_DOMAIN/share-cover.png'
  })
})
```

### 关键注意事项

1. **域名需要在微信公众号后台配置 JS 安全域名**
2. **access_token 和 jsapi_ticket 需要缓存**（7200 秒有效期），不要每次请求都重新获取
3. **URL 必须完全匹配**：签名用的 URL 必须和当前页面 URL 完全一致（包括 query 参数）
4. **微信内调试**：可以用 `wx.config({ debug: true })` 在微信开发者工具中调试

## 降级方案

如果没有微信公众号权限，使用 Web Share API 兜底：
```javascript
if (navigator.share) {
  navigator.share({ title, text, url })
} else {
  // 复制链接到剪贴板
  navigator.clipboard.writeText(url)
}
```

## 相关 MCP（可辅助使用）

| MCP | 用途 |
|-----|------|
| WeChat-MCP (128 star) | 读写微信消息，可用于测试通知 |
| weapp-dev-mcp (83 star) | 微信小程序开发者工具自动化 |

## 需要人类提供的资源

- [ ] 微信公众号 AppID
- [ ] 微信公众号 AppSecret
- [ ] 在公众号后台配置 JS 安全域名

## 状态：🔴 需要自建 + 需要微信公众号权限
