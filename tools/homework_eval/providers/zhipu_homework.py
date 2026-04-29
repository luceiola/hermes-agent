from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

from tools.homework_eval.schema import NormalizedQuestion, ProviderResult
from tools.homework_eval.utils import (
    as_bool,
    as_float,
    as_str,
    dedupe_questions,
    extract_question_candidates,
    find_first,
    http_request,
    iter_dict_nodes,
    now_ms,
    parse_event_stream,
)


class ZhipuHomeworkProvider:
    def __init__(self, env: dict[str, str], timeout_sec: int = 30) -> None:
        self.env = env
        self.timeout_sec = timeout_sec
        self.api_key = env.get("ZHIPU_API_KEY") or env.get("BIGMODEL_API_KEY")
        self.base_url = env.get("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/v1")
        self.agent_correction_id = env.get(
            "ZHIPU_CORRECTION_AGENT_ID", "intelligent_education_correction_agent"
        )
        self.agent_polling_id = env.get(
            "ZHIPU_POLLING_AGENT_ID", "intelligent_education_correction_polling"
        )
        self.agent_analysis_id = env.get(
            "ZHIPU_ANALYSIS_AGENT_ID", "intelligent_education_correction_analysis"
        )

    def run(self, image_url: Optional[str], image_file: Optional[str]) -> ProviderResult:
        start_ms = now_ms()
        errors: list[str] = []
        raw_payload: dict[str, Any] = {}

        if not self.api_key:
            return ProviderResult(
                provider="zhipu_homework",
                success=False,
                elapsed_ms=now_ms() - start_ms,
                errors=["Missing ZHIPU_API_KEY"],
            )

        if not image_url:
            errors.append("Zhipu homework agent currently requires --image-url")
            return ProviderResult(
                provider="zhipu_homework",
                success=False,
                elapsed_ms=now_ms() - start_ms,
                errors=errors,
            )

        initial_payload = self._call_correction(image_url=image_url, errors=errors)
        raw_payload["initial"] = initial_payload

        trace_id = as_str(find_first(initial_payload, ["trace_id"]))
        unfinished = self._extract_unfinished(initial_payload)

        polling_payload: Optional[dict[str, Any]] = None
        if trace_id and unfinished:
            polling_payload = self._call_polling(trace_id=trace_id, unfinished=unfinished, errors=errors)
            raw_payload["polling"] = polling_payload

        analysis_payloads: list[dict[str, Any]] = []
        if trace_id and unfinished:
            for item in unfinished:
                if not item.get("question") or not item.get("image_id") or not item.get("uuid"):
                    continue
                response = self._call_analysis(trace_id=trace_id, item=item, errors=errors)
                if response:
                    analysis_payloads.append(response)
            if analysis_payloads:
                raw_payload["analysis"] = analysis_payloads

        merged_payload = {
            "initial": initial_payload,
            "polling": polling_payload,
            "analysis": analysis_payloads,
        }
        questions = self._normalize_questions(merged_payload)

        success = bool(questions) and not self._has_error(raw_payload)
        request_id = as_str(find_first(raw_payload, ["request_id", "id"]))

        return ProviderResult(
            provider="zhipu_homework",
            success=success,
            elapsed_ms=now_ms() - start_ms,
            request_id=request_id,
            raw_status="done" if success else "partial_or_failed",
            trace_id=trace_id,
            questions=questions,
            summary=self._build_summary(questions),
            errors=errors,
            raw_payload=raw_payload,
        )

    def _headers(self) -> dict[str, str]:
        key = self.api_key or ""
        return {
            "Authorization": f"Bearer {key}",
            "X-Api-Key": key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _parse_response_payload(self, body_text: str, content_type: str) -> dict[str, Any]:
        if "text/event-stream" in content_type:
            stream = parse_event_stream(body_text)
            return {"_stream": stream, "_raw": body_text}

        try:
            import json

            return json.loads(body_text)
        except Exception:
            return {"_raw": body_text}

    def _post(self, path: str, body: dict[str, Any], errors: list[str]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        resp = http_request(
            method="POST",
            url=url,
            headers=self._headers(),
            json_body=body,
            timeout_sec=self.timeout_sec,
        )

        content_type = resp.headers.get("content-type", "")
        payload = self._parse_response_payload(resp.body_text, content_type)

        if not resp.ok:
            errors.append(f"Zhipu {path} HTTP failed: {resp.error or resp.status_code}")
            if payload:
                errors.append(str(payload))
        elif self._has_error(payload):
            errors.append(f"Zhipu {path} API error: {payload}")
        return payload

    def _call_correction(self, image_url: str, errors: list[str]) -> dict[str, Any]:
        body = {
            "agent_id": self.agent_correction_id,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "image_url", "image_url": image_url}],
                }
            ],
        }
        return self._post("/agents", body, errors)

    def _call_polling(self, trace_id: str, unfinished: list[dict[str, str]], errors: list[str]) -> dict[str, Any]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for item in unfinished:
            image_id = item.get("image_id")
            uuid = item.get("uuid")
            if not image_id or not uuid:
                continue
            grouped[image_id].append(uuid)

        images = [{"image_id": image_id, "uuids": uuids} for image_id, uuids in grouped.items()]
        body = {
            "agent_id": self.agent_polling_id,
            "custom_variables": {
                "trace_id": trace_id,
                "images": images,
            },
        }
        return self._post("/agents/async-result", body, errors)

    def _call_analysis(self, trace_id: str, item: dict[str, str], errors: list[str]) -> dict[str, Any]:
        body = {
            "agent_id": self.agent_analysis_id,
            "custom_variables": {
                "question": item["question"],
                "image_id": item["image_id"],
                "uuid": item["uuid"],
                "trace_id": trace_id,
            },
        }
        return self._post("/agents", body, errors)

    @staticmethod
    def _extract_unfinished(payload: dict[str, Any]) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        for node in iter_dict_nodes(payload):
            if "is_finish" not in node:
                continue
            is_finish = as_bool(node.get("is_finish"))
            if is_finish is True:
                continue
            uuid = as_str(node.get("uuid"))
            image_id = as_str(node.get("image_id"))
            question = as_str(node.get("question") or node.get("ocr") or node.get("text"))
            if uuid and image_id:
                items.append({"uuid": uuid, "image_id": image_id, "question": question or ""})
        return items

    @staticmethod
    def _has_error(payload: dict[str, Any]) -> bool:
        code = find_first(payload, ["error_code", "code"])
        if code is None:
            return False
        code_str = str(code).strip().lower()
        return code_str not in {"0", "200", "ok", "success"}

    def _normalize_questions(self, payload: dict[str, Any]) -> list[NormalizedQuestion]:
        candidates = dedupe_questions(extract_question_candidates(payload))
        questions: list[NormalizedQuestion] = []

        for index, item in enumerate(candidates, start=1):
            question = NormalizedQuestion(
                question_id=as_str(
                    item.get("question_id")
                    or item.get("uuid")
                    or item.get("id")
                    or item.get("index")
                    or index
                ),
                recognized_text=as_str(
                    item.get("question")
                    or item.get("ocr")
                    or item.get("text")
                    or item.get("question_text")
                ),
                student_answer=as_str(item.get("student_answer") or item.get("answer") or item.get("user_answer")),
                expected_answer=as_str(
                    item.get("expected_answer") or item.get("right_answer") or item.get("standard_answer")
                ),
                is_correct=as_bool(
                    item.get("is_correct")
                    or item.get("is_right")
                    or item.get("correct")
                    or item.get("judge_result")
                ),
                score=as_float(item.get("score") or item.get("got_score")),
                max_score=as_float(item.get("max_score") or item.get("full_score") or item.get("total_score")),
                reason=as_str(item.get("reason") or item.get("comment") or item.get("explain")),
                analysis=as_str(item.get("analysis") or item.get("analysis_text") or item.get("suggestion")),
                bbox=item.get("bbox") or item.get("position") or item.get("rect"),
                confidence=as_float(item.get("confidence") or item.get("probability")),
                extras=item,
            )
            questions.append(question)

        return questions

    @staticmethod
    def _build_summary(questions: list[NormalizedQuestion]) -> dict[str, Any]:
        total = len(questions)
        correct = sum(1 for q in questions if q.is_correct is True)
        incorrect = sum(1 for q in questions if q.is_correct is False)
        unknown = total - correct - incorrect

        return {
            "total_questions": total,
            "correct_questions": correct,
            "incorrect_questions": incorrect,
            "unknown_questions": unknown,
        }
