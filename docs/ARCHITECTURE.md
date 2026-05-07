# Architecture

`hermes-personal` 是一个运行时配置仓库，本身不实现 Agent 推理逻辑。

## 组件
- `hermes-agent`：实际执行推理和平台接入（外部仓库，默认路径 `/Users/lucas/Documents/hermes-agent`）
- `profiles/*`：本仓库模板同步到 `~/.hermes/profiles/<profile>`
- `gateway_profile.sh`：启动 Hermes gateway（飞书消息入口）
- `dashboard_profile.sh`：启动 Hermes dashboard（可选）

## 运行流
1. 通过 `setup_profile.sh <profile>` 初始化 profile。
2. 在 `~/.hermes/profiles/<profile>/.env` 配置平台与模型密钥。
3. `gateway_profile.sh start` 启动对应 gateway。
4. 对应平台消息进入 Hermes adapter，由 Hermes Agent 处理并回包。

## 隔离策略
- 进程隔离：`--profile <name>`
- 配置隔离：`~/.hermes/profiles/<name>/*`
- 端口隔离：dashboard 建议固定端口映射（`9129-9133`）
- 日志隔离：`~/.hermes/profiles/<name>/logs/*`
