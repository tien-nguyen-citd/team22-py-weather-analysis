from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from pydantic.alias_generators import to_camel

from weather_nlu.question_info import TimeKind, TimeSlot


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


class UnderstandResponse(CamelResponse):
    location_slug: str | None
    location_from_question: bool
    activity_id: str | None
    time: TimeSlotResponse | None


class HealthResponse(CamelResponse):
    status: Literal["ok"]
    extractor: str
