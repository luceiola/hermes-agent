from __future__ import annotations

from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from tools.vocab_extractor.schema import VocabExtractionResult, VocabItem


def build_markdown(result: VocabExtractionResult) -> str:
    lines: list[str] = []
    lines.append(f"# 标记词词表（教学版）")
    lines.append("")
    lines.append(f"- 任务ID：`{result.task_id}`")
    lines.append(f"- 来源类型：`{result.source_type}`")
    lines.append(f"- 阈值：`{result.threshold}`")
    lines.append(f"- 总识别：`{result.summary.get('total_detected', 0)}`")
    lines.append(f"- 主词表：`{result.summary.get('main_count', 0)}`")
    lines.append(f"- 疑似区：`{result.summary.get('suspected_count', 0)}`")
    lines.append("")

    lines.append("## 主词表")
    lines.append("")
    if not result.items_main:
        lines.append("（空）")
    else:
        for idx, item in enumerate(result.items_main, start=1):
            lines.extend(_item_markdown(item, idx))

    lines.append("")
    lines.append("## 疑似区（建议人工复核）")
    lines.append("")
    if not result.items_suspected:
        lines.append("（空）")
    else:
        for idx, item in enumerate(result.items_suspected, start=1):
            lines.extend(_item_markdown(item, idx))

    if result.errors:
        lines.append("")
        lines.append("## 处理告警")
        lines.append("")
        for err in result.errors:
            lines.append(f"- {err}")

    return "\n".join(lines).strip() + "\n"


def _item_markdown(item: VocabItem, idx: int) -> list[str]:
    lines = [f"### {idx}. {item.word}"]
    lines.append(f"- 音标（UK/US）：`{item.phonetic_uk or '-'} / {item.phonetic_us or '-'}`")
    lines.append(f"- 词性：`{item.pos or '-'}`")
    lines.append(f"- 释义：{item.meaning_zh or '-'}")
    lines.append(f"- 英文解释：{item.simple_en_explain or '-'}")
    lines.append(f"- 原文句：{item.source_sentence or '-'}")
    lines.append(f"- 例句：{item.example_sentence or '-'}")
    lines.append(f"- 置信度：`{item.confidence:.2f}`")
    if item.page is not None:
        lines.append(f"- 页码：`{item.page}`")
    if item.bbox:
        lines.append(f"- 坐标：`{item.bbox}`")
    lines.append("")
    return lines


def write_markdown(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def build_pdf(result: VocabExtractionResult, path: Path) -> None:
    # Built-in CJK font for Chinese rendering.
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        font_name = "STSong-Light"
    except Exception:
        font_name = "Helvetica"

    styles = getSampleStyleSheet()
    normal = ParagraphStyle(
        "NormalCJK",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=14,
    )
    h1 = ParagraphStyle(
        "H1CJK",
        parent=styles["Heading1"],
        fontName=font_name,
        fontSize=16,
        leading=20,
    )
    h2 = ParagraphStyle(
        "H2CJK",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=13,
        leading=16,
    )

    doc = SimpleDocTemplate(str(path), pagesize=A4, title="标记词词表")
    story = []

    story.append(Paragraph("标记词词表（教学版）", h1))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"任务ID：{escape(result.task_id)}", normal))
    story.append(Paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal))
    story.append(Paragraph(f"来源类型：{escape(result.source_type)}", normal))
    story.append(Paragraph(
        f"统计：总识别 {result.summary.get('total_detected', 0)} / 主词表 {result.summary.get('main_count', 0)} / 疑似区 {result.summary.get('suspected_count', 0)}",
        normal,
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph("主词表", h2))
    story.extend(_item_pdf_block(result.items_main, normal))

    story.append(Spacer(1, 10))
    story.append(Paragraph("疑似区（建议人工复核）", h2))
    story.extend(_item_pdf_block(result.items_suspected, normal))

    if result.errors:
        story.append(Spacer(1, 10))
        story.append(Paragraph("处理告警", h2))
        for err in result.errors:
            story.append(Paragraph(f"- {escape(err)}", normal))

    doc.build(story)


def _item_pdf_block(items: list[VocabItem], style: ParagraphStyle):
    blocks = []
    if not items:
        blocks.append(Paragraph("（空）", style))
        return blocks

    for idx, item in enumerate(items, start=1):
        blocks.append(Spacer(1, 6))
        blocks.append(Paragraph(f"{idx}. {escape(item.word)}", style))
        blocks.append(Paragraph(f"音标：{escape(item.phonetic_uk or '-')} / {escape(item.phonetic_us or '-')}", style))
        blocks.append(Paragraph(f"词性：{escape(item.pos or '-')}", style))
        blocks.append(Paragraph(f"释义：{escape(item.meaning_zh or '-')}", style))
        blocks.append(Paragraph(f"英文解释：{escape(item.simple_en_explain or '-')}", style))
        blocks.append(Paragraph(f"原文句：{escape(item.source_sentence or '-')}", style))
        blocks.append(Paragraph(f"例句：{escape(item.example_sentence or '-')}", style))
        blocks.append(Paragraph(f"置信度：{item.confidence:.2f}", style))
        if item.page is not None:
            blocks.append(Paragraph(f"页码：{item.page}", style))

    return blocks
