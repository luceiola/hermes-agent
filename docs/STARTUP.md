# 启动命令说明（hermes-personal）

本文档用于多 profile Hermes Runtime（`personal` / `heidou` / `mei`）的启动、停止、状态检查与常见运维操作。

## 0. 前置条件
- `hermes-agent` 已可用（默认路径：`/Users/lucas/Documents/hermes-agent`）
- 已有飞书机器人应用凭证（`FEISHU_APP_ID` / `FEISHU_APP_SECRET`）

## 1. 首次初始化（只需一次）
```bash
cd /Users/lucas/Documents/hermes-personal
scripts/setup_profile.sh personal
scripts/setup_profile.sh heidou
scripts/setup_profile.sh mei
```

初始化完成后会生成：
- `~/.hermes/profiles/personal/.env`
- `~/.hermes/profiles/personal/config.yaml`
- `~/.hermes/profiles/personal/SOUL.md`
- `~/.hermes/profiles/heidou/*`
- `~/.hermes/profiles/mei/*`

## 2. 配置环境变量
编辑：`~/.hermes/profiles/personal/.env`

至少需要填写：
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `OPENAI_API_KEY`（或其他模型厂商 key）

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
```

仅同步不重启：
```bash
cd /Users/lucas/Documents/hermes-personal
HERMES_PROFILE=personal RESTART_GATEWAY=0 RESTART_DASHBOARD=0 scripts/sync_profile.sh
```

## 7. 与现有 hermes-runtime 并行运行
为了不冲突，请保持以下项不同：
- Profile：`personal`（本项目） vs `orchestrator`（旧项目）
- 飞书 App：不要复用同一个 `FEISHU_APP_ID`
- Dashboard 端口：本项目默认 `9129`，旧项目默认 `9119`
- webhook 端口：本项目默认 `8865`

查看两套实例状态：
```bash
HERMES_PROFILE=personal /Users/lucas/Documents/hermes-personal/scripts/gateway_profile.sh status
HERMES_PROFILE=orchestrator /Users/lucas/Documents/hermes-runtime/scripts/gateway_profile.sh status
```

## 8. 最短启动路径（可直接复制）
```bash
cd /Users/lucas/Documents/hermes-personal
scripts/setup_profile.sh personal
HERMES_PROFILE=personal scripts/check_profile_env.sh
HERMES_PROFILE=personal scripts/gateway_profile.sh start
```

## 9. 三实例批量启停
```bash
cd /Users/lucas/Documents/hermes-personal
scripts/fleet_profiles.sh start
scripts/fleet_profiles.sh status
scripts/fleet_profiles.sh stop
```
