from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Protocol

from sqlalchemy.orm import Session

from weather_analysis.clients.open_meteo_client import (
    VIETNAM_TIMEZONE,
    OpenMeteoForecast,
)
from weather_analysis.memory_cache import MemoryCache
from weather_analysis.models import Location
from weather_analysis.services.location_service import get_location_by_slug
from weather_analysis.services.scoring import (
    ActivityWindow,
    BestWindow,
    Factor,
    HourData,
    calculate_activity_windows,
    calculate_day_score,
    calculate_factors,
    calculate_hourly_score,
    get_aqi_label,
    get_best_windows,
    get_day_verdict,
    get_day_why,
    get_rain_window,
    get_weather_condition,
    js_round,
)
from weather_analysis.services.system_settings_service import (
    FORECAST_CACHE_DURATION,
    get_setting_value,
)


VIETNAMESE_DAYS = (
    "Thứ Hai",
    "Thứ Ba",
    "Thứ Tư",
    "Thứ Năm",
    "Thứ Sáu",
    "Thứ Bảy",
    "Chủ Nhật",
)
ForecastCacheKey = tuple[float, float, date]


class ForecastClient(Protocol):
    def fetch_forecast(
        self,
        latitude: float,
        longitude: float,
    ) -> OpenMeteoForecast: ...


@dataclass(frozen=True)
class ForecastLocation:
    name: str
    slug: str
    region: str
    region_label: str
    temp_offset: float
    lat: float
    lon: float


@dataclass(frozen=True)
class WeatherDetails:
    sunrise: str
    sunset: str
    sunshine_hours: float
    aqi: int | None
    aqi_label: str | None
    rain_sum: float
    rain_window: str
    dew_point: int


@dataclass(frozen=True)
class DayForecast:
    date: date
    day_label: str
    temp_max: int
    temp_min: int
    rain_prob: int
    rain_sum: float


@dataclass(frozen=True)
class LocationForecast:
    location: ForecastLocation
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
    best_windows: list[BestWindow]
    hourly: list[HourData]
    factors: list[Factor]
    details: WeatherDetails
    daily7: list[DayForecast]
    activities: list[ActivityWindow]


def get_location_forecast(
    session: Session,
    slug: str,
    client: ForecastClient,
    cache: MemoryCache[ForecastCacheKey, OpenMeteoForecast],
    now_factory: Callable[[], datetime] | None = None,
) -> LocationForecast:
    location = get_location_by_slug(session, slug)

    now = (
        now_factory() if now_factory is not None else datetime.now(VIETNAM_TIMEZONE)
    )
    cache_key = (location.latitude, location.longitude, now.date())
    cache_duration = get_setting_value(session, FORECAST_CACHE_DURATION)
    raw = cache.get_or_create(
        cache_key,
        lambda: client.fetch_forecast(location.latitude, location.longitude),
        timedelta(minutes=cache_duration),
    )
    return build_forecast(location, raw, now)


def build_forecast(
    location: Location,
    raw: OpenMeteoForecast,
    now: datetime,
) -> LocationForecast:
    current_hour = now.astimezone(VIETNAM_TIMEZONE).hour
    hourly = [_build_hour(raw, hour) for hour in range(24)]
    day_score = calculate_day_score(hourly)
    now_data = hourly[current_hour] if current_hour < len(hourly) else hourly[12]
    daily7 = [_build_day(raw, index) for index in range(7)]
    rain_sum = _round_one(_value_or(raw.daily_rain_sum[0], 0))
    aqi = _get_current_aqi(raw, current_hour)
    details = WeatherDetails(
        sunrise=_time_part(raw.daily_sunrise[0], "06:00"),
        sunset=_time_part(raw.daily_sunset[0], "18:00"),
        sunshine_hours=_round_one(
            (raw.daily_sunshine_duration[0] or 28800) / 3600
        ),
        aqi=aqi,
        aqi_label=get_aqi_label(aqi) if aqi is not None else None,
        rain_sum=rain_sum,
        rain_window=get_rain_window(hourly),
        dew_point=js_round(
            _value_or(raw.hourly_dew_point[current_hour], 22)
        ),
    )
    condition = get_weather_condition(
        now_data.rain_prob,
        now_data.uv,
        rain_sum,
    )
    peak_rain = max(hour.rain_prob for hour in hourly)
    return LocationForecast(
        location=_location_data(location),
        updated_at=raw.fetched_at,
        temp_now=js_round(now_data.temp),
        apparent_temp_now=js_round(
            _value_or(
                raw.hourly_apparent_temperature[current_hour],
                now_data.temp,
            )
        ),
        temp_max=daily7[0].temp_max,
        temp_min=daily7[0].temp_min,
        condition_desc=condition,
        humidity_now=now_data.humidity,
        wind_now=now_data.wind,
        rain_prob_now=now_data.rain_prob,
        uv_now=now_data.uv,
        day_score=day_score,
        verdict=get_day_verdict(day_score),
        why=get_day_why(
            condition,
            now_data.humidity,
            now_data.wind,
            hourly,
            now_data.uv,
        ),
        best_windows=get_best_windows(hourly),
        hourly=hourly,
        factors=calculate_factors(
            now_data.temp,
            now_data.uv,
            peak_rain,
            now_data.humidity,
            now_data.wind,
        ),
        details=details,
        daily7=daily7,
        activities=calculate_activity_windows(hourly),
    )


def _build_hour(raw: OpenMeteoForecast, hour: int) -> HourData:
    temp = _round_one(_value_or(raw.hourly_temperature[hour], 25))
    rain_prob = js_round(_value_or(raw.hourly_rain_probability[hour], 0))
    uv = _round_one(_value_or(raw.hourly_uv[hour], 0))
    humidity = js_round(_value_or(raw.hourly_humidity[hour], 60))
    wind = js_round(_value_or(raw.hourly_wind[hour], 10))
    return HourData(
        hour=hour,
        temp=temp,
        rain_prob=rain_prob,
        uv=uv,
        humidity=humidity,
        wind=wind,
        score=calculate_hourly_score(temp, rain_prob, uv, hour),
    )


def _build_day(raw: OpenMeteoForecast, index: int) -> DayForecast:
    forecast_date = raw.daily_time[index]
    day_label = "Hôm nay" if index == 0 else VIETNAMESE_DAYS[
        forecast_date.weekday()
    ]
    return DayForecast(
        date=forecast_date,
        day_label=day_label,
        temp_max=js_round(_value_or(raw.daily_temp_max[index], 30)),
        temp_min=js_round(_value_or(raw.daily_temp_min[index], 22)),
        rain_prob=js_round(_value_or(raw.daily_rain_probability[index], 20)),
        rain_sum=_round_one(_value_or(raw.daily_rain_sum[index], 0)),
    )


def _location_data(location: Location) -> ForecastLocation:
    return ForecastLocation(
        name=location.name,
        slug=location.slug,
        region=location.region_code,
        region_label=location.region_label,
        temp_offset=location.temp_offset,
        lat=location.latitude,
        lon=location.longitude,
    )


def _get_current_aqi(raw: OpenMeteoForecast, current_hour: int) -> int | None:
    if raw.us_aqi is None or current_hour >= len(raw.us_aqi):
        return None
    value = raw.us_aqi[current_hour]
    return js_round(value) if value is not None else None


def _time_part(value: str | None, default: str) -> str:
    actual = value or default
    if "T" in actual:
        return actual.split("T", maxsplit=1)[1][:5]
    return actual


def _round_one(value: float) -> float:
    return js_round(value * 10) / 10


def _value_or(value: float | None, default: float) -> float:
    return default if value is None else value
