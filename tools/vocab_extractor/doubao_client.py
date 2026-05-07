from __future__ import annotations

import json
import re
from typing import Any

from tools.homework_eval.utils import http_request


DETECT_PROMPT = """你是英文阅读图片里的“标记词检测器”。\
只做检测，不做词义讲解。\
\
任务：找出图片中被标记的英文“单词”（下划线/高亮/圈画/手写标注）。\
\
严格要求：\
1) 只返回 JSON，不要任何解释文字。\
2) 返回格式必须是：{"items":[...]}。\
3) 每个 item 只包含字段：word, confidence。\
4) word 必须是单个英文单词，不要短语，不要空格。\
5) 每个单词最多出现一次；按在文中出现顺序输出；最多输出 30 个。\
6) confidence 为 0~1 数字。\
7) 若无法识别，返回 {"items":[]}。\
"""

ENRICH_PROMPT = """你是英文词汇教学补全助手。\
输入是一组英文单词，你需要补全词汇学习字段。\
\
严格要求：\
1) 只返回 JSON，不要任何解释文字。\
2) 返回格式必须是：{"items":[...]}。\
3) 每个 item 字段：word, phonetic_uk, phonetic_us, pos, meaning_zh, simple_en_explain, example_sentence。\
4) 字段无法确定时填 null。\
5) example_sentence 给简短教学例句即可。\
"""


class QwenVisionClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        timeout_sec: int = 60,
        enrich_api_key: str | None = None,
        enrich_model: str | None = None,
        enrich_base_url: str | None = None,
        enrich_timeout_sec: int | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec
        self.enrich_api_key = (enrich_api_key or api_key).strip()
        self.enrich_model = (enrich_model or model).strip()
        self.enrich_base_url = (enrich_base_url or base_url).rstrip("/")
        self.enrich_timeout_sec = enrich_timeout_sec or timeout_sec

    def extract_marked_words(self, image_ref: str, page: int) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
        payload = {
            "model": self.model,
            "temperature": 0,
            "max_output_tokens": 1400,
            "reasoning": {"effort": "low"},
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": DETECT_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "请识别这页英文阅读材料里被标记的英文单词，"
                                "严格按 JSON 返回。"
                            ),
                        },
                        {"type": "input_image", "image_url": image_ref},
                    ],
                },
            ],
        }

        resp = http_request(
            method="POST",
            url=f"{self.base_url}/responses",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json_body=payload,
            timeout_sec=self.timeout_sec,
        )

        raw_payload = resp.json() if resp.body_text else None
        errors: list[str] = []

        if not resp.ok:
            errors.append(f"Vision API HTTP failed: {resp.error or resp.status_code}")
            if raw_payload is not None:
                errors.append(str(raw_payload))
            return [], errors, raw_payload or {"_raw": resp.body_text}

        if raw_payload is None:
            errors.append("Vision API returned empty body")
            return [], errors, {"_raw": resp.body_text}

        text = self._extract_text(raw_payload)
        parsed = self._parse_json(text)

        if not isinstance(parsed, dict) or not isinstance(parsed.get("items"), list):
            errors.append("Vision response JSON does not contain items[]")
            errors.append(f"raw_text={text[:3000]}")
            return [], errors, raw_payload

        return parsed["items"], errors, raw_payload

    def enrich_words(self, words: list[str]) -> tuple[dict[str, dict[str, Any]], list[str], dict[str, Any]]:
        clean_words = [w.strip() for w in words if isinstance(w, str) and w.strip()]
        if not clean_words:
            return {}, [], {"items": []}

        errors: list[str] = []
        merged: dict[str, dict[str, Any]] = {}
        raw_batches: list[dict[str, Any]] = []

        # qwen3.5-plus in this environment becomes unstable on large batches.
        # Keep per-request word count small to avoid timeout / non-JSON drift.
        batch_size = 5
        for idx in range(0, len(clean_words), batch_size):
            batch = clean_words[idx : idx + batch_size]
            parsed, batch_errors, raw_payload = self._enrich_batch(batch)
            raw_batches.append({"words": batch, "raw": raw_payload})
            errors.extend([f"batch_{idx // batch_size + 1}: {msg}" for msg in batch_errors])
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                word = str(item.get("word") or "").strip()
                if not word:
                    continue
                merged[_word_key(word)] = item

        if errors and not merged:
            return {}, errors, {"batches": raw_batches}

        return merged, errors, {"batches": raw_batches}

    def _enrich_batch(self, words: list[str]) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
        payload = {
            "model": self.enrich_model,
            "temperature": 0,
            "max_output_tokens": 1200,
            "reasoning": {"effort": "low"},
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": ENRICH_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "请补全下列单词字段并输出 JSON：\n"
                                + json.dumps({"words": words}, ensure_ascii=False)
                            ),
                        },
                    ],
                },
            ],
        }

        resp = http_request(
            method="POST",
            url=f"{self.enrich_base_url}/responses",
            headers={
                "Authorization": f"Bearer {self.enrich_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json_body=payload,
            timeout_sec=self.enrich_timeout_sec,
        )

        raw_payload = resp.json() if resp.body_text else None
        errors: list[str] = []

        if not resp.ok:
            errors.append(f"Enrich API HTTP failed: {resp.error or resp.status_code}")
            if raw_payload is not None:
                errors.append(str(raw_payload))
            return [], errors, raw_payload or {"_raw": resp.body_text}

        if raw_payload is None:
            errors.append("Enrich API returned empty body")
            return [], errors, {"_raw": resp.body_text}

        text = self._extract_text(raw_payload)
        parsed = self._parse_json(text)
        if not isinstance(parsed, dict) or not isinstance(parsed.get("items"), list):
            errors.append("Enrich response JSON does not contain items[]")
            errors.append(f"raw_text={text[:3000]}")
            return [], errors, raw_payload

        out_items: list[dict[str, Any]] = []
        for item in parsed["items"]:
            if not isinstance(item, dict):
                continue
            word = str(item.get("word") or "").strip()
            if not word:
                continue
            out_items.append(item)

        return out_items, errors, raw_payload

    @staticmethod
    def _extract_text(payload: dict[str, Any]) -> str:
        if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
            return payload["output_text"].strip()

        out = payload.get("output")
        if isinstance(out, list):
            parts: list[str] = []
            for block in out:
                content = block.get("content") if isinstance(block, dict) else None
                if not isinstance(content, list):
                    continue
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    text = item.get("text")
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())
            if parts:
                return "\n".join(parts)

        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _parse_json(text: str) -> Any:
        raw = text.strip()

        # try direct parse first
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # try fenced code block
        match = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", raw, flags=re.IGNORECASE)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # try first {...} block
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            candidate = raw[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # Partial JSON fallback for truncated outputs:
        # recover complete item objects like {"word":"...","confidence":0.9}
        # from a cut-off {"items":[... sequence.
        if '"items"' in raw and '"word"' in raw:
            recovered: list[dict[str, Any]] = []
            for match in re.finditer(r"\{[^{}]*\"word\"[^{}]*\}", raw):
                snippet = match.group(0)
                try:
                    obj = json.loads(snippet)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict) and obj.get("word"):
                    recovered.append(obj)
            if recovered:
                return {"items": recovered}

        # Fallback: recover numbered word lists from free-form reasoning text,
        # e.g. "1. Pyramid ... 2. surface ..."
        numbered = re.findall(r"(?:^|[\n\r])\s*\d+\.\s*([A-Za-z][A-Za-z'-]{0,63})\b", raw)
        if numbered:
            seen: set[str] = set()
            items: list[dict[str, Any]] = []
            for word in numbered:
                key = _word_key(word)
                if not key or key in seen:
                    continue
                seen.add(key)
                items.append({"word": word, "confidence": 0.85})
            if items:
                return {"items": items}

        return {"_raw": raw}


def _word_key(word: str) -> str:
    base = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", word).strip().lower()
    return base or word.strip().lower()


# Backward-compatible alias for older imports.
DoubaoVisionClient = QwenVisionClient
