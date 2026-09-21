from dataclasses import dataclass
from datetime import date
from typing import Literal


class AdvisoryInputError(ValueError):
    """Yêu cầu tư vấn không hợp lệ."""


@dataclass(frozen=True)
class MonthRange:
    start_month: str
    end_month: str


@dataclass(frozen=True)
class AdvisoryRequest:
    location_slug: str
    time: MonthRange | None = None
    activity_id: str | None = None
    top_k: int = 3


@dataclass(frozen=True)
class NormalizedRequest:
    location_slug: str
    time: MonthRange
    activity_id: str
    top_k: int


@dataclass(frozen=True)
class ActivityProfile:
    id: str
    name: str
    rain_weight: float
    temperature_weight: float
    temperature_min: float | None
    temperature_max: float | None
    description: str
    rain_threshold_mm: float = 1.0


@dataclass(frozen=True)
class CandidateWindow:
    start_date: date
    end_date: date
    label: str
    resolution: Literal["month", "period"]


@dataclass(frozen=True)
class WeatherDay:
    date: date
    temperature_mean: float
    precipitation_sum: float


@dataclass(frozen=True)
class Candidate:
    window: CandidateWindow
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
    rank: int = 0
    similar_to_best: bool = False


@dataclass(frozen=True)
class Advice:
    request: NormalizedRequest
    baseline_start: date
    baseline_end: date
    activity: ActivityProfile
    recommendations: list[Candidate]
    candidates: list[Candidate]
    summary: str
    low_suitability: bool
    notes: list[str]


@dataclass(frozen=True)
class DestinationRequest:
    month: str | None = None
    activity_id: str | None = None


@dataclass(frozen=True)
class DestinationResult:
    slug: str
    name: str
    region_label: str
    candidate: Candidate


@dataclass(frozen=True)
class DestinationRanking:
    month: str
    activity: ActivityProfile
    baseline_start: date
    baseline_end: date
    destinations: list[DestinationResult]
    summary: str
    low_suitability: bool
    notes: list[str]
