# Homework APIs A/B 对比（智谱 + 百度）

## 目标
- 两个独立 provider：`zhipu_homework`、`baidu_correct_edu`
- 统一输出结构，便于后续做评测、错题分析、训练推荐
- 单条命令同时跑通两个 API

## 文件
- `tools/homework_eval/compare.py`：统一入口
- `tools/homework_eval/providers/baidu_correct_edu.py`：百度实现
- `tools/homework_eval/providers/zhipu_homework.py`：智谱实现
- `tools/homework_eval/schema.py`：统一数据结构
- `tools/homework_eval/output.schema.json`：输出 JSON Schema
- `.env.homework.example`：环境变量模板

## 环境变量
可选两种加载方式：
- `--profile <name>`：读取 `~/.hermes/profiles/<name>/.env`
- `--env-file <path>`：读取指定 env 文件（可重复）

推荐：
1. 复制模板：`cp .env.homework.example .env.homework`
2. 填入两个平台密钥
3. 运行命令时带 `--env-file .env.homework`

## 运行示例
```bash
cd /Users/lucas/Documents/hermes-personal

python3 -m tools.homework_eval.compare \
  --image-url 'https://example.com/homework.jpg' \
  --env-file .env.homework \
  --providers baidu,zhipu \
  --pretty
```

本地图片（百度支持，智谱当前要求 URL）：
```bash
python3 -m tools.homework_eval.compare \
  --image-file '/absolute/path/to/homework.jpg' \
  --env-file .env.homework \
  --providers baidu \
  --pretty
```

## 输出规范（摘要）
顶层：
- `image_url` / `image_file`
- `started_at` / `finished_at`
- `outputs[]`

每个 provider：
- `provider`, `success`, `elapsed_ms`
- `request_id`, `raw_status`, `trace_id`, `task_id`
- `questions[]`, `summary`, `errors[]`
- `raw_payload`（可用 `--no-raw` 关闭）

`questions[]` 统一字段：
- `question_id`
- `recognized_text`
- `student_answer`
- `expected_answer`
- `is_correct`
- `score` / `max_score`
- `reason` / `analysis`
- `bbox` / `confidence`
- `tags[]`
- `extras`（保留 provider 原始字段）

## 说明
- 百度接口采用 `create_task -> get_result` 轮询流程。
- 智谱接口采用作业批改 Agent 主调用，包含 polling/analysis 兜底路径。
- 若字段映射不全，可先看 `raw_payload`，再迭代补映射逻辑。
