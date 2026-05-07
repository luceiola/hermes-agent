# 标记词提取工具（Qwen3.6 多模态）

## 功能
- 输入英文阅读图片或 PDF。
- 抽取被标记单词（下划线/高亮/圈画）。
- 产出教学版 Markdown 与 PDF。
- 按 `confidence` 分主词表和疑似区。

## 环境变量
- `VOCAB_API_KEY`：词汇提取独立调用 key（推荐单独配置）。
- `VOCAB_MODEL`：视觉模型 ID（如 `qwen3.6-plus`）。
- `VOCAB_BASE_URL`：词汇提取独立调用 endpoint。

回退顺序（兼容旧配置）：
1. `VOCAB_*`
2. `API_KEY / BASE_URL / MODEL`（主链路配置）

可放在以下任一位置：
1. `~/.hermes/profiles/<profile>/.env`
2. `--env-file <path>` 指定文件
3. 当前目录 `.env.vocab`

## 运行
```bash
cd /Users/lucas/Documents/hermes-personal

# URL 图片
HERMES_PROFILE=heidou scripts/vocab_extract.sh \
  --image-url 'https://example.com/reading.jpg' \
  --pretty

# 本地图片
HERMES_PROFILE=heidou scripts/vocab_extract.sh \
  --image-file '/absolute/path/reading.jpg' \
  --pretty

# PDF（最多前3页，可调整）
HERMES_PROFILE=heidou scripts/vocab_extract.sh \
  --image-file '/absolute/path/reading.pdf' \
  --max-pages 3 \
  --pretty
```

## Heidou 路由命令（用于聊天指令）
当用户在 QQ 聊天中发送 `提取标记词 #img_xxx` 等命令时，建议通过统一路由脚本执行：

```bash
cd /Users/lucas/Documents/hermes-personal

# 提取
python3 scripts/heidou_vocab_router.py \
  extract \
  --profile heidou

# 仅导出 PDF（若无历史结果会自动先提取）
python3 scripts/heidou_vocab_router.py \
  export-pdf \
  --profile heidou

# 可选：指定某张历史图片
python3 scripts/heidou_vocab_router.py \
  extract \
  --profile heidou \
  --image-id img_xxx
```

状态缓存文件：`~/.hermes/profiles/heidou/cache/vocab_router_state.json`

## 输出
默认输出目录：`artifacts/vocab_extractor/`
- `<task_id>.json`：结构化结果
- `<task_id>.md`：Markdown
- `<task_id>.pdf`：PDF
- `<task_id>.raw.json`：模型原始回包（调试用）

## 阈值
- 默认阈值 `0.75`
- `confidence >= 0.75` -> 主词表
- `confidence < 0.75` -> 疑似区

可通过 `--threshold` 调整。

## 注意
- 工具只负责执行，不负责聊天门控。
- 门控由主 Agent 在 `profiles/heidou/SOUL.md` 与 `skills/heidou/SKILL.md` 执行。
