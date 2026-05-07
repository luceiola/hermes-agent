from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

from tools.vocab_extractor.doubao_client import QwenVisionClient
from tools.vocab_extractor.io_utils import normalize_image_inputs
from tools.vocab_extractor.schema import VocabExtractionResult, VocabItem


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def clamp_confidence(value: Any) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    if v < 0:
        return 0.0
    if v > 1:
        return 1.0
    return v


def coerce_item(raw: dict[str, Any], page: int) -> VocabItem:
    word = normalize_word(raw.get("word"))
    return VocabItem(
        word=word,
        phonetic_uk=_to_str(raw.get("phonetic_uk")),
        phonetic_us=_to_str(raw.get("phonetic_us")),
        pos=_to_str(raw.get("pos")),
        meaning_zh=_to_str(raw.get("meaning_zh")),
        simple_en_explain=_to_str(raw.get("simple_en_explain")),
        example_sentence=_to_str(raw.get("example_sentence")),
        source_sentence=_to_str(raw.get("source_sentence")),
        confidence=clamp_confidence(raw.get("confidence")),
        page=_to_int(raw.get("page")) or page,
        bbox=raw.get("bbox") if isinstance(raw.get("bbox"), dict) else None,
        extras={k: v for k, v in raw.items() if k not in {
            "word", "phonetic_uk", "phonetic_us", "pos", "meaning_zh", "simple_en_explain", "example_sentence", "source_sentence", "confidence", "page", "bbox"
        }},
    )


def _to_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_word(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    # Keep a single English token to avoid phrase-style outputs.
    m = re.search(r"[A-Za-z][A-Za-z'-]*", text)
    if not m:
        return ""
    return m.group(0)


def dedupe_items(items: list[VocabItem]) -> list[VocabItem]:
    seen: set[tuple[str, str | None, int | None]] = set()
    result: list[VocabItem] = []

    for item in items:
        key = (item.word.lower(), item.source_sentence, item.page)
        if not item.word:
            continue
        if key in seen:
            continue
        seen.add(key)
        result.append(item)

    return result


def _word_key(word: str) -> str:
    base = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", (word or "")).strip().lower()
    return base or (word or "").strip().lower()


def apply_enrichment(items: list[VocabItem], enrich_map: dict[str, dict[str, Any]]) -> None:
    for item in items:
        key = _word_key(item.word)
        enrich = enrich_map.get(key)
        if not enrich:
            continue

        item.phonetic_uk = _to_str(enrich.get("phonetic_uk")) or item.phonetic_uk
        item.phonetic_us = _to_str(enrich.get("phonetic_us")) or item.phonetic_us
        item.pos = _to_str(enrich.get("pos")) or item.pos
        item.meaning_zh = _to_str(enrich.get("meaning_zh")) or item.meaning_zh
        item.simple_en_explain = _to_str(enrich.get("simple_en_explain")) or item.simple_en_explain
        item.example_sentence = _to_str(enrich.get("example_sentence")) or item.example_sentence


def run_extraction(
    client: QwenVisionClient,
    image_url: str | None,
    image_file: str | None,
    threshold: float,
    max_pages: int,
    task_prefix: str = "vocab",
) -> tuple[VocabExtractionResult, dict[str, Any]]:
    source_type, image_refs = normalize_image_inputs(image_url=image_url, image_file=image_file, max_pages=max_pages)
    task_id = f"{task_prefix}_{utc_now()}"

    all_items: list[VocabItem] = []
    errors: list[str] = []
    provider_raw: dict[str, Any] = {"pages": []}

    for idx, ref in enumerate(image_refs, start=1):
        page_items, page_errors, raw_payload = client.extract_marked_words(image_ref=ref, page=idx)
        provider_raw["pages"].append({
            "page": idx,
            "raw": raw_payload,
        })

        errors.extend([f"page_{idx}: {msg}" for msg in page_errors])

        for raw in page_items:
            if not isinstance(raw, dict):
                continue
            all_items.append(coerce_item(raw, page=idx))

    deduped = dedupe_items(all_items)
    enrich_map: dict[str, dict[str, Any]] = {}
    enrich_raw: dict[str, Any] = {}

    if deduped:
        enrich_words = []
        seen_keys: set[str] = set()
        for item in deduped:
            k = _word_key(item.word)
            if not k or k in seen_keys:
                continue
            seen_keys.add(k)
            enrich_words.append(item.word)

        enrich_map, enrich_errors, enrich_raw = client.enrich_words(enrich_words)
        errors.extend([f"enrich: {msg}" for msg in enrich_errors])
        apply_enrichment(deduped, enrich_map)

    items_main = [item for item in deduped if item.confidence >= threshold]
    items_suspected = [item for item in deduped if item.confidence < threshold]

    summary = {
        "total_detected": len(deduped),
        "main_count": len(items_main),
        "suspected_count": len(items_suspected),
        "pages": len(image_refs),
    }

    result = VocabExtractionResult(
        task_id=task_id,
        source_type=source_type,
        image_refs=[_mask_image_ref(x) for x in image_refs],
        threshold=threshold,
        items_main=items_main,
        items_suspected=items_suspected,
        summary=summary,
        errors=errors,
    )
    if enrich_raw:
        provider_raw["enrichment"] = enrich_raw
    return result, provider_raw


def _mask_image_ref(ref: str) -> str:
    if ref.startswith("data:"):
        return "data:image/..."
    return ref


def result_to_jsonable(result: VocabExtractionResult) -> dict[str, Any]:
    data = result.to_dict()
    data["items_main"] = [asdict(x) for x in result.items_main]
    data["items_suspected"] = [asdict(x) for x in result.items_suspected]
    return data


def ensure_output_dir(output_dir: str) -> Path:
    path = Path(output_dir).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path
