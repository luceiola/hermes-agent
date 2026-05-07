# 启动命令说明（hermes-personal）

本文档用于多 profile Hermes Runtime（`personal` / `heidou` / `mei` / `orchestrator` / `video`）的启动、停止、状态检查与常见运维操作。

## 0. 前置条件
- `hermes-agent` 已可用（默认路径：`/Users/lucas/Documents/hermes-agent`）
- 已有飞书机器人应用凭证（`FEISHU_APP_ID` / `FEISHU_APP_SECRET`）

## 1. 首次初始化（只需一次）
```bash
cd /Users/lucas/Documents/hermes-personal
scripts/setup_profile.sh personal
scripts/setup_profile.sh heidou
scripts/setup_profile.sh mei
scripts/setup_profile.sh orchestrator
scripts/setup_profile.sh video
```

初始化完成后会生成：
- `~/.hermes/profiles/personal/.env`
- `~/.hermes/profiles/personal/config.yaml`
- `~/.hermes/profiles/personal/SOUL.md`
- `~/.hermes/profiles/heidou/*`
- `~/.hermes/profiles/mei/*`
- `~/.hermes/profiles/orchestrator/*`
- `~/.hermes/profiles/video/*`

## 2. 配置环境变量
编辑：`~/.hermes/profiles/personal/.env`

至少需要填写：
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `API_KEY`
- `BASE_URL`
- `MODEL`（建议 `qwen3.6-plus`）

可选：
- `FEISHU_CONNECTION_MODE=websocket`（默认，推荐）
- webhook 模式下设置 `FEISHU_WEBHOOK_PORT=8865` 与 `FEISHU_WEBHOOK_PATH=/feishu/personal/webhook`

若配置 `heidou`（QQ）或 `mei`（Weixin），请参考：
- `docs/PROFILES.md`
- `docs/CHANNELS-OFFICIAL.md`

## 3. 校验配置
```bash
cd /Users/lucas/Documents/hermes-personal
HERMES_PROFILE=personal scripts/check_profile_env.sh
```

## 4. 启动 Gateway（飞书消息入口）
```bash
cd /Users/lucas/Documents/hermes-personal
HERMES_PROFILE=personal scripts/gateway_profile.sh start
```

常用 Gateway 命令：
```bash
HERMES_PROFILE=personal scripts/gateway_profile.sh stop
HERMES_PROFILE=personal scripts/gateway_profile.sh restart
HERMES_PROFILE=personal scripts/gateway_profile.sh status
HERMES_PROFILE=personal scripts/gateway_profile.sh logs
HERMES_PROFILE=personal scripts/gateway_profile.sh logs-follow
```

## 5. 启动 Dashboard（可选）
默认端口是 `9129`。
```bash
cd /Users/lucas/Documents/hermes-personal
HERMES_PROFILE=personal HERMES_DASHBOARD_PORT=9129 scripts/dashboard_profile.sh start
```

常用 Dashboard 命令：
```bash
HERMES_PROFILE=personal HERMES_DASHBOARD_PORT=9129 scripts/dashboard_profile.sh stop
HERMES_PROFILE=personal HERMES_DASHBOARD_PORT=9129 scripts/dashboard_profile.sh restart
HERMES_PROFILE=personal HERMES_DASHBOARD_PORT=9129 scripts/dashboard_profile.sh status
HERMES_PROFILE=personal HERMES_DASHBOARD_PORT=9129 scripts/dashboard_profile.sh logs
HERMES_PROFILE=personal HERMES_DASHBOARD_PORT=9129 scripts/dashboard_profile.sh logs-follow
```

## 6. 同步配置并重启（改了 SOUL / config / skills 后）
```bash
cd /Users/lucas/Documents/hermes-personal
HERMES_PROFILE=personal scripts/sync_profile.sh
HERMES_PROFILE=heidou scripts/sync_profile.sh
HERMES_PROFILE=mei scripts/sync_profile.sh
HERMES_PROFILE=orchestrator scripts/sync_profile.sh
HERMES_PROFILE=video scripts/sync_profile.sh
```

仅同步不重启：
```bash
cd /Users/lucas/Documents/hermes-personal
HERMES_PROFILE=personal RESTART_GATEWAY=0 RESTART_DASHBOARD=0 scripts/sync_profile.sh
```

## 7. 统一管理 5 个 profile
本仓库可直接统一管理：`personal`、`heidou`、`mei`、`orchestrator`、`video`。

默认 Dashboard 端口建议：
- `personal=9129`
- `heidou=9130`
- `mei=9131`
- `orchestrator=9132`
- `video=9133`

## 8. 最短启动路径（可直接复制）
```bash
cd /Users/lucas/Documents/hermes-personal
scripts/setup_profile.sh personal
HERMES_PROFILE=personal scripts/check_profile_env.sh
HERMES_PROFILE=personal scripts/gateway_profile.sh start
```

## 9. 五实例批量启停
```bash
cd /Users/lucas/Documents/hermes-personal
scripts/fleet_profiles.sh start
scripts/fleet_profiles.sh status
scripts/fleet_profiles.sh stop
```
