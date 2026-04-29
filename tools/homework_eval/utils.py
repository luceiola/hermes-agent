from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class HttpResponse:
    ok: bool
    status_code: int
    body_text: str
    headers: dict[str, str]
    error: Optional[str] = None

    def json(self) -> Optional[Any]:
        if not self.body_text:
            return None
        try:
            return json.loads(self.body_text)
        except json.JSONDecodeError:
            return None


def now_ms() -> int:
    return int(time.time() * 1000)


def as_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def as_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        norm = value.strip().lower()
        if norm in {"true", "1", "yes", "y", "correct", "right", "ok"}:
            return True
        if norm in {"false", "0", "no", "n", "wrong", "incorrect"}:
            return False
    return None


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def http_request(
    method: str,
    url: str,
    headers: Optional[dict[str, str]] = None,
    json_body: Optional[dict[str, Any]] = None,
    form_body: Optional[dict[str, Any]] = None,
    timeout_sec: int = 30,
) -> HttpResponse:
    if json_body is not None and form_body is not None:
        raise ValueError("json_body and form_body are mutually exclusive")

    req_headers = dict(headers or {})
    data = None

    if json_body is not None:
        data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    elif form_body is not None:
        data = urlencode(form_body).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    request = Request(url=url, method=method.upper(), data=data, headers=req_headers)

    try:
        with urlopen(request, timeout=timeout_sec) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            headers_out = {k.lower(): v for k, v in resp.headers.items()}
            return HttpResponse(ok=True, status_code=resp.getcode(), body_text=body, headers=headers_out)
    except HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return HttpResponse(
            ok=False,
            status_code=exc.code,
            body_text=body,
            headers={},
            error=f"HTTPError {exc.code}",
        )
    except URLError as exc:
        return HttpResponse(ok=False, status_code=0, body_text="", headers={}, error=f"URLError: {exc}")
    except Exception as exc:
        return HttpResponse(ok=False, status_code=0, body_text="", headers={}, error=f"Error: {exc}")


def parse_event_stream(body_text: str) -> list[Any]:
    items: list[Any] = []
    for raw in body_text.splitlines():
        line = raw.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            items.append(json.loads(payload))
        except json.JSONDecodeError:
            items.append(payload)
    return items


def find_first(obj: Any, keys: Iterable[str]) -> Any:
    keyset = set(keys)
    for node in iter_dict_nodes(obj):
        for key in keyset:
            if key in node:
                return node[key]
    return None


def iter_dict_nodes(obj: Any) -> Iterator[dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from iter_dict_nodes(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_dict_nodes(item)


def extract_question_candidates(obj: Any) -> list[dict[str, Any]]:
    triggers = {
        "question",
        "question_id",
        "uuid",
        "is_correct",
        "is_right",
        "correct",
        "student_answer",
        "answer",
        "score",
        "ocr",
        "text",
    }
    result: list[dict[str, Any]] = []
    for node in iter_dict_nodes(obj):
        if len(node) < 2:
            continue
        if not any(key in node for key in triggers):
            continue
        # Skip orchestration wrappers that may contain nested result blocks.
        if {"initial", "polling", "analysis"}.issubset(set(node.keys())):
            continue
        result.append(node)
    return result


def dedupe_questions(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in candidates:
        marker = json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)
        if marker in seen:
            continue
        seen.add(marker)
        out.append(item)
    return out


def read_image_base64(path: str) -> str:
    with open(path, "rb") as handle:
        return base64.b64encode(handle.read()).decode("ascii")


def load_env_file(path: Path) -> dict[str, str]:
    envs: dict[str, str] = {}
    if not path.exists():
        return envs
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        envs[key] = value
    return envs


def merge_env(paths: list[Path]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for path in paths:
        merged.update(load_env_file(path))
    for key, value in os.environ.items():
        merged[key] = value
    return merged
