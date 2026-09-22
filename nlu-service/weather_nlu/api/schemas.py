from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from pydantic.alias_generators import to_camel

from weather_nlu.question_info import (
    Decision,
    DecisionMethod,
    DecisionSource,
    ExtractionExplanation,
    Intent,
    Neighbor,
    TimeKind,
    TimeSlot,
)


class CamelResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)


class UnderstandRequest(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        extra="forbid",
    )

    question: StrictStr = Field(min_length=1, max_length=500)
    current_location_slug: StrictStr | None = None
    today: date | None = None

    @field_validator("question")
    @classmethod
    def question_must_have_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Câu hỏi không được để trống")
        return value.strip()


class TimeSlotResponse(CamelResponse):
    kind: TimeKind
    start_date: date | None
    end_date: date | None

    @classmethod
    def from_slot(cls, slot: TimeSlot) -> Self:
        return cls(kind=slot.kind, start_date=slot.start, end_date=slot.end)


class NeighborResponse(CamelResponse):
    label: str | None
    text: str
    similarity: float

    @classmethod
    def from_neighbor(cls, neighbor: Neighbor[str | None]) -> Self:
        return cls(
            label=neighbor.label,
            text=neighbor.text,
            similarity=round(neighbor.similarity, 3),
        )


class DecisionResponse(CamelResponse):
    method: DecisionMethod
    source: DecisionSource
    matched_text: str | None
    neighbors: list[NeighborResponse]

    @classmethod
    def from_decision(cls, decision: Decision) -> Self:
        return cls(
            method=decision.source.method,
            source=decision.source,
            matched_text=decision.matched_text,
            neighbors=[NeighborResponse.from_neighbor(item) for item in decision.neighbors],
        )


class DebugResponse(CamelResponse):
    """Thông tin giúp hiểu vì sao câu hỏi được đọc như vậy."""

    embedding_text: str
    location_text: str | None
    activity: DecisionResponse
    intent: DecisionResponse

    @classmethod
    def from_explanation(cls, explanation: ExtractionExplanation) -> Self:
        return cls(
            embedding_text=explanation.embedding_text,
            location_text=explanation.location_text,
            activity=DecisionResponse.from_decision(explanation.activity),
            intent=DecisionResponse.from_decision(explanation.intent),
        )


class UnderstandResponse(CamelResponse):
    location_slug: str | None
    location_from_question: bool
    activity_id: str | None
    time: TimeSlotResponse | None
    intent: Intent
    debug: DebugResponse | None


class HealthResponse(CamelResponse):
    status: Literal["ok"]
    extractor: str
