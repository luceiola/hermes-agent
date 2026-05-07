# Operations

## 常用命令
```bash
cd /Users/lucas/Documents/hermes-personal

# personal: 启动/重启/状态/日志
HERMES_PROFILE=personal scripts/gateway_profile.sh start
HERMES_PROFILE=personal scripts/gateway_profile.sh restart
HERMES_PROFILE=personal scripts/gateway_profile.sh status
HERMES_PROFILE=personal scripts/gateway_profile.sh logs-follow

# Dashboard（可选）
HERMES_PROFILE=personal HERMES_DASHBOARD_PORT=9129 scripts/dashboard_profile.sh start
HERMES_PROFILE=personal HERMES_DASHBOARD_PORT=9129 scripts/dashboard_profile.sh status

# 五实例批量管理
scripts/fleet_profiles.sh start
scripts/fleet_profiles.sh status
scripts/fleet_profiles.sh stop
```

## 首次初始化
```bash
cd /Users/lucas/Documents/hermes-personal
scripts/setup_profile.sh personal
scripts/setup_profile.sh heidou
scripts/setup_profile.sh mei
scripts/setup_profile.sh orchestrator
scripts/setup_profile.sh video
HERMES_PROFILE=personal scripts/check_profile_env.sh
HERMES_PROFILE=personal scripts/gateway_profile.sh start
```

## 同步 profile 资产（改了 SOUL/config/skills 后）
```bash
cd /Users/lucas/Documents/hermes-personal
HERMES_PROFILE=personal scripts/sync_profile.sh
HERMES_PROFILE=heidou scripts/sync_profile.sh
HERMES_PROFILE=mei scripts/sync_profile.sh
HERMES_PROFILE=orchestrator scripts/sync_profile.sh
HERMES_PROFILE=video scripts/sync_profile.sh
```

## 故障排查最小步骤
1. `HERMES_PROFILE=personal scripts/gateway_profile.sh status`
2. `HERMES_PROFILE=personal scripts/gateway_profile.sh logs`
3. 检查 `~/.hermes/profiles/personal/.env`
4. 若 webhook 模式，确认飞书后台回调地址与 `FEISHU_WEBHOOK_*` 一致
