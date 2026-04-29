from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class NormalizedQuestion:
    question_id: Optional[str] = None
    recognized_text: Optional[str] = None
    student_answer: Optional[str] = None
    expected_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    score: Optional[float] = None
    max_score: Optional[float] = None
    reason: Optional[str] = None
    analysis: Optional[str] = None
    bbox: Optional[dict[str, Any]] = None
    confidence: Optional[float] = None
    tags: list[str] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderResult:
    provider: str
    success: bool
    elapsed_ms: int
    request_id: Optional[str] = None
    raw_status: Optional[str] = None
    trace_id: Optional[str] = None
    task_id: Optional[str] = None
    questions: list[NormalizedQuestion] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    raw_payload: Optional[Any] = None

    def to_dict(self, include_raw: bool = True) -> dict[str, Any]:
        data = asdict(self)
        if not include_raw:
            data.pop("raw_payload", None)
        return data


@dataclass
class CompareOutput:
    image_url: Optional[str]
    image_file: Optional[str]
    started_at: str
    finished_at: str
    outputs: list[ProviderResult]

    def to_dict(self, include_raw: bool = True) -> dict[str, Any]:
        return {
            "image_url": self.image_url,
            "image_file": self.image_file,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "outputs": [item.to_dict(include_raw=include_raw) for item in self.outputs],
        }
