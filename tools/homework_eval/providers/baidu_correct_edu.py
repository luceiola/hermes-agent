from __future__ import annotations

import time
from typing import Any, Optional
from urllib.parse import urlencode

from tools.homework_eval.schema import NormalizedQuestion, ProviderResult
from tools.homework_eval.utils import (
    as_bool,
    as_float,
    as_str,
    dedupe_questions,
    extract_question_candidates,
    find_first,
    http_request,
    now_ms,
    read_image_base64,
)


class BaiduCorrectEduProvider:
    def __init__(
        self,
        env: dict[str, str],
        timeout_sec: int = 30,
        poll_interval_sec: int = 5,
        poll_attempts: int = 24,
    ) -> None:
        self.env = env
        self.timeout_sec = timeout_sec
        self.poll_interval_sec = poll_interval_sec
        self.poll_attempts = poll_attempts
        self.base_url = env.get("BAIDU_CORRECT_EDU_BASE_URL", "https://aip.baidubce.com/rest/2.0/ocr/v1")
        self.oauth_url = env.get("BAIDU_OAUTH_URL", "https://aip.baidubce.com/oauth/2.0/token")
        self.api_key = env.get("BAIDU_OCR_API_KEY") or env.get("BAIDU_API_KEY")
        self.secret_key = env.get("BAIDU_OCR_SECRET_KEY") or env.get("BAIDU_SECRET_KEY")
        self._token_cache = env.get("BAIDU_OCR_ACCESS_TOKEN") or env.get("BAIDU_ACCESS_TOKEN")

    def run(self, image_url: Optional[str], image_file: Optional[str]) -> ProviderResult:
        start_ms = now_ms()
        errors: list[str] = []
        raw_payload: dict[str, Any] = {}

        if not image_url and not image_file:
            return ProviderResult(
                provider="baidu_correct_edu",
                success=False,
                elapsed_ms=now_ms() - start_ms,
                errors=["Baidu provider requires --image-url or --image-file"],
            )

        token = self._get_access_token(errors)
        if not token:
            return ProviderResult(
                provider="baidu_correct_edu",
                success=False,
                elapsed_ms=now_ms() - start_ms,
                errors=errors,
                raw_payload=raw_payload,
            )

        task_payload = self._create_task(token=token, image_url=image_url, image_file=image_file, errors=errors)
        raw_payload["create_task"] = task_payload

        task_id = as_str(find_first(task_payload, ["task_id"]))
        if not task_id:
            errors.append("Baidu create_task did not return task_id")
            return ProviderResult(
                provider="baidu_correct_edu",
                success=False,
                elapsed_ms=now_ms() - start_ms,
                task_id=task_id,
                request_id=as_str(find_first(task_payload, ["log_id", "request_id"])),
                raw_status="create_task_failed",
                errors=errors,
                raw_payload=raw_payload,
            )

        final_payload: dict[str, Any] = {}
        raw_status = "polling_timeout"

        for _ in range(self.poll_attempts):
            poll_payload = self._get_result(token=token, task_id=task_id, errors=errors)
            raw_payload.setdefault("polling", []).append(poll_payload)
            final_payload = poll_payload
            status = self._status_text(poll_payload)
            if self._is_error(poll_payload):
                raw_status = status or "error"
                break
            if self._is_done(poll_payload):
                raw_status = status or "done"
                break
            time.sleep(self.poll_interval_sec)

        questions = self._normalize_questions(final_payload)
        request_id = as_str(find_first(final_payload, ["log_id", "request_id"])) or as_str(
            find_first(task_payload, ["log_id", "request_id"])
        )
        success = (not self._is_error(final_payload)) and bool(questions or self._is_done(final_payload))

        return ProviderResult(
            provider="baidu_correct_edu",
            success=success,
            elapsed_ms=now_ms() - start_ms,
            request_id=request_id,
            raw_status=raw_status,
            task_id=task_id,
            questions=questions,
            summary=self._build_summary(questions),
            errors=errors,
            raw_payload=raw_payload,
        )

    def _get_access_token(self, errors: list[str]) -> Optional[str]:
        if self._token_cache:
            return self._token_cache

        if not self.api_key or not self.secret_key:
            errors.append("Missing BAIDU_OCR_API_KEY/BAIDU_OCR_SECRET_KEY")
            return None

        query = urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.secret_key,
            }
        )
        url = f"{self.oauth_url}?{query}"
        resp = http_request("GET", url, timeout_sec=self.timeout_sec)
        payload = resp.json() or {}

        if not resp.ok:
            errors.append(f"Baidu OAuth failed: {resp.error or resp.status_code}")
            if payload:
                errors.append(str(payload))
            return None

        token = as_str(payload.get("access_token"))
        if not token:
            errors.append("Baidu OAuth response missing access_token")
            return None

        self._token_cache = token
        return token

    def _create_task(
        self,
        token: str,
        image_url: Optional[str],
        image_file: Optional[str],
        errors: list[str],
    ) -> dict[str, Any]:
        url = f"{self.base_url}/correct_edu/create_task?access_token={token}"
        body: dict[str, Any] = {"only_split": "false"}

        if image_file:
            body["image"] = read_image_base64(image_file)
        elif image_url:
            body["url"] = image_url

        resp = http_request("POST", url, form_body=body, timeout_sec=self.timeout_sec)
        payload = resp.json() or {"_raw": resp.body_text}

        if not resp.ok:
            errors.append(f"Baidu create_task HTTP failed: {resp.error or resp.status_code}")
        if self._is_error(payload):
            errors.append(f"Baidu create_task error: {payload}")

        return payload

    def _get_result(self, token: str, task_id: str, errors: list[str]) -> dict[str, Any]:
        url = f"{self.base_url}/correct_edu/get_result?access_token={token}"
        resp = http_request("POST", url, form_body={"task_id": task_id}, timeout_sec=self.timeout_sec)
        payload = resp.json() or {"_raw": resp.body_text}

        if not resp.ok:
            errors.append(f"Baidu get_result HTTP failed: {resp.error or resp.status_code}")

        return payload

    @staticmethod
    def _is_error(payload: dict[str, Any]) -> bool:
        code = find_first(payload, ["error_code", "err_no", "code"])
        if code is None:
            return False
        code_str = str(code)
        return code_str not in {"0", "200", "success"}

    @staticmethod
    def _status_text(payload: dict[str, Any]) -> str:
        status = find_first(
            payload,
            [
                "status",
                "task_status",
                "task_state",
                "process_status",
                "processing_status",
                "state",
            ],
        )
        if status is None:
            return "unknown"
        return str(status)

    def _is_done(self, payload: dict[str, Any]) -> bool:
        is_finish = find_first(payload, ["is_finish", "finished", "done"])
        if as_bool(is_finish) is True:
            return True

        status = self._status_text(payload).strip().lower()
        if status in {"done", "success", "succeeded", "finished", "complete", "completed"}:
            return True
        if status in {"processing", "running", "pending", "queued", "queueing", "unknown", ""}:
            return False

        if find_first(payload, ["result", "results", "data", "items", "question_list"]) is not None:
            return True

        return False

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
                    or item.get("text")
                    or item.get("ocr")
                    or item.get("ocr_text")
                    or item.get("origin_question")
                ),
                student_answer=as_str(item.get("student_answer") or item.get("answer") or item.get("user_answer")),
                expected_answer=as_str(
                    item.get("expected_answer") or item.get("standard_answer") or item.get("right_answer")
                ),
                is_correct=as_bool(item.get("is_correct") or item.get("is_right") or item.get("correct")),
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
        score_sum = sum(q.score for q in questions if q.score is not None)
        max_score_sum = sum(q.max_score for q in questions if q.max_score is not None)

        return {
            "total_questions": total,
            "correct_questions": correct,
            "incorrect_questions": incorrect,
            "unknown_questions": unknown,
            "score_sum": score_sum if score_sum else None,
            "max_score_sum": max_score_sum if max_score_sum else None,
        }
