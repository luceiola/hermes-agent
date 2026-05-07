# hermes-personal

个人多 Profile Hermes 运行时仓库（control plane）。

目标：在同一个仓库下运行多个隔离 profile（`personal` / `heidou` / `mei` / `orchestrator` / `video`），统一管理与开发。

## 设计原则
- 复用你现有 `hermes-agent` 的网关运行方式（与 `hermes-runtime` 同实现风格）
- profile 隔离：会话、日志、技能、环境变量相互独立
- 默认 profile：`personal`（你）、`heidou`（孩子）、`mei`（媳妇）、`orchestrator`（视频编排）、`video`（视频执行）
- 默认 dashboard 端口：`9129` / `9130` / `9131` / `9132` / `9133`
- 平台接入遵循官方渠道：QQ Bot（官方 API v2）、Weixin（官方 iLink Bot）

## 目录
- `profiles/*/`: 五套 profile 模板
- `skills/*/`: 五套技能入口
- `scripts/`: 启停、初始化、同步脚本
- `docs/`: 架构与运维文档

## 快速开始
```bash
cd /Users/lucas/Documents/hermes-personal

# 1) 初始化某个 profile（首次）
scripts/setup_profile.sh personal
scripts/setup_profile.sh heidou
scripts/setup_profile.sh mei
scripts/setup_profile.sh orchestrator
scripts/setup_profile.sh video

# 2) 编辑环境变量（平台凭据 + 模型 key）
$HOME/.hermes/profiles/personal/.env
$HOME/.hermes/profiles/heidou/.env
$HOME/.hermes/profiles/mei/.env
$HOME/.hermes/profiles/orchestrator/.env
$HOME/.hermes/profiles/video/.env

# 3) 校验配置
HERMES_PROFILE=personal scripts/check_profile_env.sh
HERMES_PROFILE=heidou scripts/check_profile_env.sh
HERMES_PROFILE=mei scripts/check_profile_env.sh
HERMES_PROFILE=orchestrator scripts/check_profile_env.sh
HERMES_PROFILE=video scripts/check_profile_env.sh

# 4) 启动 gateway（单实例）
HERMES_PROFILE=personal scripts/gateway_profile.sh start

# 5) 启动 dashboard（可选）
HERMES_PROFILE=personal HERMES_DASHBOARD_PORT=9129 scripts/dashboard_profile.sh start

# 6) 五实例批量启停（可选）
scripts/fleet_profiles.sh start
scripts/fleet_profiles.sh status
scripts/fleet_profiles.sh stop
```

## 与现有 hermes-runtime 并行运行
只要保持下列项不同，就不会冲突：
- `HERMES_PROFILE`（建议固定 `personal|heidou|mei|orchestrator|video`）
- 平台凭证（不要跨 profile 复用同一 bot 凭证）
- `HERMES_DASHBOARD_PORT`（`9129/9130/9131/9132/9133`）
- 若使用 webhook：对应 webhook 端口

## 文档
- `docs/ARCHITECTURE.md`
- `docs/OPERATIONS.md`
- `docs/STARTUP.md`
- `docs/PROFILES.md`
- `docs/CHANNELS-OFFICIAL.md`
- `docs/HOMEWORK-APIS.md`
- `docs/REQUIREMENTS-VOCAB-EXTRACTOR.md`
- `docs/TODO-VOCAB-EXTRACTOR.md`
- `docs/VOCAB-EXTRACTOR.md`
