from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class VocabItem:
    word: str
    phonetic_uk: Optional[str] = None
    phonetic_us: Optional[str] = None
    pos: Optional[str] = None
    meaning_zh: Optional[str] = None
    simple_en_explain: Optional[str] = None
    example_sentence: Optional[str] = None
    source_sentence: Optional[str] = None
    confidence: float = 0.0
    page: Optional[int] = None
    bbox: Optional[dict[str, Any]] = None
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class VocabExtractionResult:
    task_id: str
    source_type: str
    image_refs: list[str]
    threshold: float
    items_main: list[VocabItem] = field(default_factory=list)
    items_suspected: list[VocabItem] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "source_type": self.source_type,
            "image_refs": self.image_refs,
            "threshold": self.threshold,
            "items_main": [asdict(item) for item in self.items_main],
            "items_suspected": [asdict(item) for item in self.items_suspected],
            "summary": self.summary,
            "artifacts": self.artifacts,
            "errors": self.errors,
        }
