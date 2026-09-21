from datetime import date
from typing import Literal, Self

from pydantic import ConfigDict, Field, StrictInt, StrictStr

from weather_analysis.advisory.models import (
    AdvisoryRequest,
    DestinationRanking,
    DestinationRequest,
    DestinationResult,
    MonthRange,
)
from weather_analysis.api.schemas import CamelResponse


class MonthRangeRequest(CamelResponse):
    model_config = ConfigDict(extra="forbid")

    start_month: StrictStr = Field(description="Tháng bắt đầu, định dạng YYYY-MM")
    end_month: StrictStr = Field(description="Tháng kết thúc, định dạng YYYY-MM")


class AdviceRequest(CamelResponse):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "locationSlug": "ha-noi",
                    "time": {"startMonth": "2027-01", "endMonth": "2027-03"},
                    "activityId": "wedding",
                    "topK": 3,
                }
            ],
        },
    )

    location_slug: StrictStr = Field(description="Slug của địa điểm trong danh mục")
    time: MonthRangeRequest | None = Field(
        default=None,
        description="Tối đa 12 tháng; bỏ trống để tìm từ tháng kế tiếp",
    )
    activity_id: StrictStr | None = Field(
        default=None, description="Bỏ trống để dùng nhu cầu chung"
    )
    top_k: StrictInt = Field(
        default=3, ge=1, le=3, description="Số đề xuất, từ 1 đến 3"
    )

    def to_request(self) -> AdvisoryRequest:
        return AdvisoryRequest(
            location_slug=self.location_slug,
            time=None
            if self.time is None
            else MonthRange(self.time.start_month, self.time.end_month),
            activity_id=self.activity_id,
            top_k=self.top_k,
        )


class NormalizedRequestResponse(CamelResponse):
    location_slug: str
    time: MonthRangeRequest
    activity_id: str
    top_k: int


class ActivityProfileResponse(CamelResponse):
    id: str
    name: str
    rain_weight: float
    temperature_weight: float
    temperature_min: float | None
    temperature_max: float | None
    description: str
    rain_threshold_mm: float


class CandidateWindowResponse(CamelResponse):
    start_date: date
    end_date: date
    label: str
    resolution: Literal["month", "period"]


class CandidateResponse(CamelResponse):
    window: CandidateWindowResponse
    temperature_mean: float
    rainy_day_percentage: float
    precipitation_mean: float
    rain_score: float
    temperature_score: float | None
    rain_contribution: float
    temperature_contribution: float
    score: float
    sample_years: int
    sample_days: int
    explanation: str
    rank: int
    similar_to_best: bool


class AdviceResponse(CamelResponse):
    request: NormalizedRequestResponse
    baseline_start: date
    baseline_end: date
    activity: ActivityProfileResponse
    recommendations: list[CandidateResponse]
    candidates: list[CandidateResponse]
    summary: str
    low_suitability: bool
    notes: list[str]


class AdvisoryErrorResponse(CamelResponse):
    detail: str


class DestinationRequestBody(CamelResponse):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"month": "2026-12", "activityId": "beach"}],
        },
    )

    month: StrictStr | None = Field(
        default=None, description="Tháng YYYY-MM; bỏ trống để dùng tháng kế tiếp"
    )
    activity_id: StrictStr | None = Field(
        default=None, description="Bỏ trống để dùng nhu cầu chung"
    )

    def to_request(self) -> DestinationRequest:
        return DestinationRequest(month=self.month, activity_id=self.activity_id)


class DestinationLocationResponse(CamelResponse):
    slug: str
    name: str
    region_label: str


class DestinationResultResponse(CamelResponse):
    location: DestinationLocationResponse
    candidate: CandidateResponse

    @classmethod
    def from_result(cls, result: DestinationResult) -> Self:
        return cls(
            location=DestinationLocationResponse(
                slug=result.slug, name=result.name, region_label=result.region_label
            ),
            candidate=CandidateResponse.model_validate(result.candidate),
        )


class DestinationRankingResponse(CamelResponse):
    month: str
    activity: ActivityProfileResponse
    baseline_start: date
    baseline_end: date
    destinations: list[DestinationResultResponse]
    summary: str
    low_suitability: bool
    notes: list[str]

    @classmethod
    def from_ranking(cls, ranking: DestinationRanking) -> Self:
        return cls(
            month=ranking.month,
            activity=ActivityProfileResponse.model_validate(ranking.activity),
            baseline_start=ranking.baseline_start,
            baseline_end=ranking.baseline_end,
            destinations=[
                DestinationResultResponse.from_result(item)
                for item in ranking.destinations
            ],
            summary=ranking.summary,
            low_suitability=ranking.low_suitability,
            notes=ranking.notes,
        )
