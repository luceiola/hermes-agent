# TODO（本地三实例）

## 1. 配置与目录
- [ ] 新建 `profiles/heidou/`、`profiles/mei/`（含 `SOUL.md`、`config.yaml`、`.env.example`）
- [ ] 通用化脚本里的 `personal` 硬编码（`setup/sync/link` 相关脚本）
- [ ] 在 `~/.hermes/profiles/` 下创建 `personal`、`heidou`、`mei` 三套独立目录

## 2. 环境变量
- [ ] `personal` 填好现有平台密钥
- [ ] `heidou` 填 QQ bot 相关配置
- [ ] `mei` 填微信 clawbot 相关配置
- [ ] 三套 `.env` 做敏感信息隔离（不共用 token）

## 3. 端口与进程
- [ ] 规划 dashboard 端口（如 `9129/9130/9131`）
- [ ] 三个 profile 分别启动 gateway
- [ ] 三个 profile 分别启动 dashboard
- [ ] 增加 `start-all / stop-all / status-all` 便捷命令

## 4. 功能验证
- [ ] `personal`：发送/回复正常
- [ ] `heidou`：QQ 收发、多轮对话正常
- [ ] `mei`：微信收发、多轮对话正常
- [ ] 每个实例连续对话 20 轮无中断

## 5. 隔离验证
- [ ] 停掉 `heidou`，确认 `personal`、`mei` 不受影响
- [ ] 清理 `mei` 会话，确认 `personal`、`heidou` 记忆不变
- [ ] 检查日志目录互不混写

## 6. 运行期观察（1-2 周）
- [ ] 每天记录 CPU/内存峰值
- [ ] 记录消息延迟与失败率
- [ ] 记录异常与恢复步骤（形成 runbook）
