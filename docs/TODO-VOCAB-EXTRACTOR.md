# TODO：标记词提取与词表导出（MVP）

## Phase 0：冻结规格
- [x] 确认架构：主 Agent 调度 + subagent 执行。
- [x] 确认交互：收图仅确认，不自动执行。
- [x] 确认输出字段与 PDF 教学版版式。
- [x] 确认低置信度“疑似区”规则。

## 当前进展（2026-04-29）
- [x] 在 `profiles/heidou/SOUL.md` 与 `skills/heidou/SKILL.md` 写入“收图不自动执行”的强约束。
- [x] 新增 `tools/vocab_extractor` CLI（多模态调用、阈值分区、Markdown/PDF 导出）。
- [x] 新增运行文档 `docs/VOCAB-EXTRACTOR.md` 与脚本 `scripts/vocab_extract.sh`。
- [x] 新增 `scripts/heidou_vocab_router.py`（`#img_xxx` 路由到词汇提取，统一 JSON 输出与状态缓存）。

## Phase 1：主 Agent 门控
- [x] 增加图片接收态：`image_received_pending_intent`。
- [x] 生成图片引用 ID（如 `#img_xxx`）。
- [x] 未识别到显式命令时只回复提示语。
- [x] 增加命令解析：`提取标记词` / `导出词表pdf` / `提取并导出`。

## Phase 2：subagent 与 tool 接口
- [ ] 定义 subagent：`vocab_extractor`。
- [x] 定义 tool 输入：`image_id`、来源类型、provider 参数。
- [x] 定义 tool 输出：统一 JSON（主词表 + 疑似区 + summary）。
- [ ] 补齐错误码与失败降级（超时、鉴权失败、空结果）。

## Phase 3：多模态提取能力
- [ ] 实现图像/PDF 预处理（必要时降噪、裁切）。
- [ ] 接入 Qwen3.6 多模态模型进行“标记词检测 + OCR”。
- [ ] 抽取词条、定位 `page/bbox`、计算 `confidence`。
- [ ] 按阈值分流到主词表区与疑似区。

## Phase 4：词条补全
- [ ] 词形还原（surface -> lemma）。
- [ ] 补全 `phonetic_uk` / `phonetic_us`。
- [ ] 补全 `pos`、`meaning_zh`（词典式完整释义）。
- [ ] 生成 `simple_en_explain`、`example_sentence`、`source_sentence`。

## Phase 5：文档输出
- [ ] 生成 Markdown 教学版词表。
- [ ] Markdown 转 PDF（教学版模板）。
- [ ] 将 Markdown 与 PDF 路径返回主 Agent。
- [ ] 消息端回复中附带下载/查看方式。

## Phase 6：验证与上线
- [ ] 构建 20 份样本集（不同标记方式与拍摄质量）。
- [ ] 人工核验 Precision（目标 >= 85%）。
- [ ] 记录时延（目标 < 15s/页）。
- [ ] 回归测试：门控、并发、超时与错误处理。

## 运维检查项
- [ ] 不在仓库提交任何运行态密钥与会话数据。
- [ ] 关键调用链路可追踪（request_id/task_id/log）。
- [ ] 对外 API 失败时返回可读错误，避免静默失败。
