from typing import Self

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from weather_analysis.models import Location
from weather_analysis.services.system_settings_service import SettingState


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    username: str


class LocationResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        from_attributes=True,
    )

    name: str
    slug: str
    region: str
    region_label: str
    temp_offset: float
    lat: float
    lon: float

    @classmethod
    def from_model(cls, location: Location) -> Self:
        return cls(
            name=location.name,
            slug=location.slug,
            region=location.region_code,
            region_label=location.region_label,
            temp_offset=location.temp_offset,
            lat=location.latitude,
            lon=location.longitude,
        )


class LocationImportResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    imported_count: int


class SystemSettingUpdateRequest(BaseModel):
    value: object


class SystemSettingResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    key: str
    category: str
    title: str
    description: str
    type: str
    value: int
    default_value: int
    minimum: int
    maximum: int
    is_modified: bool

    @classmethod
    def from_state(cls, state: SettingState) -> Self:
        definition = state.definition
        return cls(
            key=definition.key,
            category=definition.category,
            title=definition.title,
            description=definition.description,
            type=definition.type,
            value=state.value,
            default_value=definition.default,
            minimum=definition.minimum,
            maximum=definition.maximum,
            is_modified=state.is_modified,
        )


class CamelResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        from_attributes=True,
    )


class BestWindowResponse(CamelResponse):
    range: str
    score: int
    start: int
    len: int
    tag: str
    note: str


class HourForecastResponse(CamelResponse):
    hour: int
    temp: float
    rain_prob: int
    uv: float
    humidity: int
    wind: int
    score: int


class FactorResponse(CamelResponse):
    label: str
    value: int
    note: str


class WeatherDetailsResponse(CamelResponse):
    sunrise: str
    sunset: str
    sunshine_hours: float
    aqi: int | None
    aqi_label: str | None
    rain_sum: float
    rain_window: str
    dew_point: int


class DayForecastResponse(CamelResponse):
    date: date
    day_label: str
    temp_max: int
    temp_min: int
    rain_prob: int
    rain_sum: float


class ActivityWindowResponse(CamelResponse):
    id: str
    name: str
    score: int
    range: str
    note: str
    has_window: bool


class LocationForecastResponse(CamelResponse):
    location: LocationResponse
    updated_at: datetime
    temp_now: int
    apparent_temp_now: int
    temp_max: int
    temp_min: int
    condition_desc: str
    humidity_now: int
    wind_now: int
    rain_prob_now: int
    uv_now: float
    day_score: int
    verdict: str
    why: str
    best_windows: list[BestWindowResponse]
    hourly: list[HourForecastResponse]
    factors: list[FactorResponse]
    details: WeatherDetailsResponse
    daily7: list[DayForecastResponse]
    activities: list[ActivityWindowResponse]


class HistoryMonthResponse(CamelResponse):
    year: int
    month: int
    rain: int
    baseline_rain: int


class RainMonthInsightResponse(CamelResponse):
    label: str
    rain: int
    rainy_days: int


class TemperatureMonthInsightResponse(CamelResponse):
    label: str
    temperature: float


class LocationHistoryResponse(CamelResponse):
    location: LocationResponse
    recent_period: str
    baseline_period: str
    months: list[HistoryMonthResponse]
    total_rain: int
    baseline_total_rain: int
    rain_diff_percent: int
    rain_comparison: str
    wettest_month: RainMonthInsightResponse
    hottest_month: TemperatureMonthInsightResponse
    coolest_month: TemperatureMonthInsightResponse


class MonthClimateResponse(CamelResponse):
    month: int
    temperature: float
    rain: int
    rainy_days: int
    tourism_score: int


class ComparedLocationResponse(CamelResponse):
    location: LocationResponse
    months: list[MonthClimateResponse]
    summary: str


class LocationComparisonResponse(CamelResponse):
    month: int
    baseline_period: str
    a: ComparedLocationResponse
    b: ComparedLocationResponse
    conclusion: str
    year_recommendation: str
