from datetime import date
from typing import Literal

from pydantic import ConfigDict, Field, StrictInt, StrictStr

from weather_analysis.advisory.models import AdvisoryRequest, MonthRange
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
