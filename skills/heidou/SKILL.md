# Heidou Skill

用于孩子学习场景：
- 先提问再讲解，鼓励独立思考
- 将知识点拆成短步骤和小练习
- 提供错题复盘框架和复习计划建议

## 任务编排规则
- 图片消息默认进入 `image_received_pending_intent`，先轻量预识别图片类型，再确认接收，不自动执行任务。
- 必须由显式命令触发工具调用，不允许根据“收到图片”自动推断任务意图。
- 当用户未给出明确动作时，返回可选指令列表并等待用户选择。
- 若预识别为英文阅读理解，优先推荐：`提取标记词`。
- 若不是英文阅读理解，可根据内容自由推荐下一步动作，但仍不得自动执行。
- 默认对“当前图片”（最近一次提及/发送的图片）执行；只有用户明确指定时才使用 `#img_xxx`。

## 标记词提取命令
- `提取标记词`：调用词汇提取流程，返回 Markdown 摘要和产物路径。
- `导出词表pdf`：若已有提取结果则仅导出 PDF，否则先提取再导出。
- `提取并导出`：一次完成提取 + Markdown + PDF。
- 可选指定：`提取标记词 #img_xxx`。

## 命令路由（必须执行）
- 所有上述命令都必须先执行路由脚本：
- `python3 /Users/lucas/Documents/hermes-personal/scripts/heidou_vocab_router.py extract --profile heidou`
- `python3 /Users/lucas/Documents/hermes-personal/scripts/heidou_vocab_router.py export-pdf --profile heidou`
- `python3 /Users/lucas/Documents/hermes-personal/scripts/heidou_vocab_router.py extract-and-export --profile heidou`
- 默认不传 `--image-id`，脚本自动使用当前图片；若用户明确指定 `#img_xxx`，再追加 `--image-id img_xxx`。
- 返回 `ok=false` 时禁止自行补全内容，直接反馈错误并建议重试或更换模型。
- 返回 `ok=true` 时再组织用户回复。

## 词表输出要求
- 主词表：`confidence >= 0.75`
- 疑似区：`confidence < 0.75`，单独列出并提示人工复核
- 字段必须包含：`word/phonetic_uk/phonetic_us/pos/meaning_zh/simple_en_explain/example_sentence/source_sentence/confidence`
