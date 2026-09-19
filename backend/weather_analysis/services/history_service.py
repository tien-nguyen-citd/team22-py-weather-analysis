from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from weather_analysis.clients.open_meteo_client import VIETNAM_TIMEZONE
from weather_analysis.services.climate_service import (
    ClimateClient,
    ClimateLocation,
    LocationClimate,
    get_location_climate,
    to_climate_location,
)
from weather_analysis.services.location_service import get_location_by_slug
from weather_analysis.services.scoring import js_round
from weather_analysis.models import Location


@dataclass(frozen=True)
class HistoryMonth:
    year: int
    month: int
    rain: int
    baseline_rain: int


@dataclass(frozen=True)
class RainMonthInsight:
    label: str
    rain: int
    rainy_days: int


@dataclass(frozen=True)
class TemperatureMonthInsight:
    label: str
    temperature: float


@dataclass(frozen=True)
class LocationHistory:
    location: ClimateLocation
    recent_period: str
    baseline_period: str
    months: list[HistoryMonth]
    total_rain: int
    baseline_total_rain: int
    rain_diff_percent: int
    rain_comparison: str
    wettest_month: RainMonthInsight
    hottest_month: TemperatureMonthInsight
    coolest_month: TemperatureMonthInsight


def get_location_history(
    session: Session,
    slug: str,
    client: ClimateClient,
    now_factory: Callable[[], datetime] | None = None,
) -> LocationHistory:
    location = get_location_by_slug(session, slug)
    now = now_factory() if now_factory is not None else datetime.now(VIETNAM_TIMEZONE)
    climate = get_location_climate(session, location, client, now.date())
    return build_location_history(location, climate)


def build_location_history(
    location: Location, climate: LocationClimate
) -> LocationHistory:
    baseline_by_month = {item.month: item for item in climate.months}
    months = [
        HistoryMonth(
            year=item.year,
            month=item.month,
            rain=item.rain,
            baseline_rain=baseline_by_month[item.month].rain,
        )
        for item in climate.recent_months
    ]
    total_rain = sum(item.rain for item in climate.recent_months)
    baseline_total_rain = sum(item.baseline_rain for item in months)
    rain_diff_percent = (
        js_round((total_rain / baseline_total_rain - 1) * 100)
        if baseline_total_rain > 0
        else 0
    )
    if rain_diff_percent > 0:
        rain_comparison = f"cao hơn {rain_diff_percent}%"
    elif rain_diff_percent < 0:
        rain_comparison = f"thấp hơn {abs(rain_diff_percent)}%"
    else:
        rain_comparison = "xấp xỉ mức trung bình"

    wettest = max(climate.recent_months, key=lambda item: item.rain)
    hottest = max(climate.recent_months, key=lambda item: item.temperature)
    coolest = min(climate.recent_months, key=lambda item: item.temperature)
    return LocationHistory(
        location=to_climate_location(location),
        recent_period=climate.recent_period,
        baseline_period=climate.baseline_period,
        months=months,
        total_rain=total_rain,
        baseline_total_rain=baseline_total_rain,
        rain_diff_percent=rain_diff_percent,
        rain_comparison=rain_comparison,
        wettest_month=RainMonthInsight(
            label=_month_label(wettest.year, wettest.month),
            rain=wettest.rain,
            rainy_days=wettest.rainy_days,
        ),
        hottest_month=TemperatureMonthInsight(
            label=_month_label(hottest.year, hottest.month),
            temperature=hottest.temperature,
        ),
        coolest_month=TemperatureMonthInsight(
            label=_month_label(coolest.year, coolest.month),
            temperature=coolest.temperature,
        ),
    )


def _month_label(year: int, month: int) -> str:
    return f"{month:02d}/{year}"
