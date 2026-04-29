# 多 Profile 运行说明（personal / heidou / mei）

## 1. 初始化

```bash
cd /Users/lucas/Documents/hermes-personal

scripts/setup_profile.sh personal
scripts/setup_profile.sh heidou
scripts/setup_profile.sh mei
```

初始化后目录：

- `~/.hermes/profiles/personal`
- `~/.hermes/profiles/heidou`
- `~/.hermes/profiles/mei`

## 2. 填写环境变量

分别编辑：

- `~/.hermes/profiles/personal/.env`
- `~/.hermes/profiles/heidou/.env`
- `~/.hermes/profiles/mei/.env`

建议每个 profile 的 bot 凭证、模型密钥都独立管理。

## 3. 校验配置

```bash
cd /Users/lucas/Documents/hermes-personal

HERMES_PROFILE=personal scripts/check_profile_env.sh
HERMES_PROFILE=heidou scripts/check_profile_env.sh
HERMES_PROFILE=mei scripts/check_profile_env.sh
```

可在 `.env` 显式指定：

- `HERMES_PRIMARY_PLATFORM=feishu`（personal）
- `HERMES_PRIMARY_PLATFORM=qqbot`（heidou）
- `HERMES_PRIMARY_PLATFORM=weixin`（mei）

## 4. 单实例启停

```bash
# gateway
HERMES_PROFILE=personal scripts/gateway_profile.sh start
HERMES_PROFILE=heidou scripts/gateway_profile.sh start
HERMES_PROFILE=mei scripts/gateway_profile.sh start

# dashboard
HERMES_PROFILE=personal HERMES_DASHBOARD_PORT=9129 scripts/dashboard_profile.sh start
HERMES_PROFILE=heidou HERMES_DASHBOARD_PORT=9130 scripts/dashboard_profile.sh start
HERMES_PROFILE=mei HERMES_DASHBOARD_PORT=9131 scripts/dashboard_profile.sh start
```

## 5. 批量启停

```bash
cd /Users/lucas/Documents/hermes-personal

scripts/fleet_profiles.sh start
scripts/fleet_profiles.sh status
scripts/fleet_profiles.sh stop
```

可选环境变量：

- `HERMES_PROFILES="personal heidou mei"`
- `HERMES_DASHBOARD_PORT_MAP="personal=9129,heidou=9130,mei=9131"`
- `START_DASHBOARD=1`（默认 1）

## 6. 同步模板到运行目录

```bash
cd /Users/lucas/Documents/hermes-personal

HERMES_PROFILE=personal scripts/sync_profile.sh
HERMES_PROFILE=heidou scripts/sync_profile.sh
HERMES_PROFILE=mei scripts/sync_profile.sh
```

旧脚本兼容：

- `scripts/setup_personal_profile.sh` -> 转发到 `setup_profile.sh`
- `scripts/sync_personal_profile.sh` -> 转发到 `sync_profile.sh`
