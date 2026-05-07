# 官方渠道接入（仅 QQ / Weixin）

本项目明确只使用官方支持方式，不使用第三方转发/协议方案。

## 1) heidou -> QQ Bot（官方 API v2）

官方路径：

- OpenClaw 官方文档：`https://docs.openclaw.ai/channels/qqbot`
- 腾讯 QQ Bot 官方 API：`https://bot.q.qq.com/wiki/develop/api-v2`

运行依赖（在 Hermes venv 安装）：

```bash
cd /Users/lucas/Documents/hermes-agent
.venv/bin/pip install aiohttp httpx
```

`heidou` 的 `.env` 最小配置：

```bash
HERMES_PRIMARY_PLATFORM=qqbot
QQ_APP_ID=...
QQ_CLIENT_SECRET=...
API_KEY=...
BASE_URL=...
MODEL=qwen3.6-plus
```

## 2) mei -> Weixin（官方 iLink Bot）

官方路径：

- OpenClaw 官方文档：`https://docs.openclaw.ai/channels/wechat`
- Hermes 官方文档（Weixin）：`https://hermesagent.com/docs/user-guide/messaging/weixin`
- iLink 官方域名（API）：`https://ilinkai.weixin.qq.com`

运行依赖（在 Hermes venv 安装）：

```bash
cd /Users/lucas/Documents/hermes-agent
.venv/bin/pip install aiohttp cryptography
# 可选：终端二维码显示
.venv/bin/pip install qrcode
```

`mei` 的 `.env` 最小配置：

```bash
HERMES_PRIMARY_PLATFORM=weixin
WEIXIN_ACCOUNT_ID=...
WEIXIN_TOKEN=...
API_KEY=...
BASE_URL=...
MODEL=qwen3.6-plus
```

## 3) profile 与平台绑定建议

- `personal` -> Feishu
- `heidou` -> QQ Bot
- `mei` -> Weixin

避免跨 profile 复用同一平台 token，防止多进程抢占连接。
