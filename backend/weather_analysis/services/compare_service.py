from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from weather_analysis.clients.open_meteo_client import VIETNAM_TIMEZONE
from weather_analysis.services.climate_service import (
    ClimateClient,
    ClimateLocation,
    LocationClimate,
    MonthClimate,
    get_location_climate,
    to_climate_location,
)
from weather_analysis.services.location_service import get_location_by_slug
from weather_analysis.services.scoring import js_round


@dataclass(frozen=True)
class ComparedLocation:
    location: ClimateLocation
    months: list[MonthClimate]
    summary: str


@dataclass(frozen=True)
class LocationComparison:
    month: int
    baseline_period: str
    a: ComparedLocation
    b: ComparedLocation
    conclusion: str
    year_recommendation: str


def compare_locations(
    session: Session,
    slug_a: str,
    slug_b: str,
    month: int,
    client: ClimateClient,
    now_factory: Callable[[], datetime] | None = None,
) -> LocationComparison:
    location_a = get_location_by_slug(session, slug_a)
    location_b = get_location_by_slug(session, slug_b)
    now = now_factory() if now_factory is not None else datetime.now(VIETNAM_TIMEZONE)
    climate_a = get_location_climate(session, location_a, client, now.date())
    climate_b = get_location_climate(session, location_b, client, now.date())
    current_a = climate_a.months[month - 1]
    current_b = climate_b.months[month - 1]
    return LocationComparison(
        month=month,
        baseline_period=climate_a.baseline_period,
        a=ComparedLocation(
            location=to_climate_location(location_a),
            months=climate_a.months,
            summary=get_compare_summary(location_a.name, month, current_a),
        ),
        b=ComparedLocation(
            location=to_climate_location(location_b),
            months=climate_b.months,
            summary=get_compare_summary(location_b.name, month, current_b),
        ),
        conclusion=get_compare_conclusion(
            month, location_a.name, current_a, location_b.name, current_b
        ),
        year_recommendation=get_year_recommendation(
            location_a.name, climate_a, location_b.name, climate_b
        ),
    )


def get_compare_summary(location_name: str, month: int, climate: MonthClimate) -> str:
    ending = "Không phải thời điểm đẹp nhất."
    if climate.tourism_score >= 80:
        ending = "Rất thích hợp cho chuyến đi."
    elif climate.tourism_score >= 60:
        ending = "Đi được, nên chuẩn bị áo mưa mỏng."
    return (
        f"{location_name} tháng {month}: trung bình {climate.temperature:g}°C, "
        f"{climate.rainy_days} ngày có mưa, tổng {climate.rain} mm. {ending}"
    )


def get_compare_conclusion(
    month: int,
    name_a: str,
    climate_a: MonthClimate,
    name_b: str,
    climate_b: MonthClimate,
) -> str:
    if climate_a.rainy_days < climate_b.rainy_days:
        drier = (
            f"{name_a} khô hơn với {climate_a.rainy_days} ngày mưa so với "
            f"{climate_b.rainy_days} ngày."
        )
    elif climate_b.rainy_days < climate_a.rainy_days:
        drier = (
            f"{name_b} khô hơn với {climate_b.rainy_days} ngày mưa so với "
            f"{climate_a.rainy_days} ngày."
        )
    else:
        drier = f"Cả hai nơi cùng có {climate_a.rainy_days} ngày mưa."

    temperature_difference = abs(
        js_round((climate_a.temperature - climate_b.temperature) * 10) / 10
    )
    if climate_a.temperature < climate_b.temperature:
        cooler = f"{name_a} mát hơn khoảng {temperature_difference:g}°C."
    elif climate_b.temperature < climate_a.temperature:
        cooler = f"{name_b} mát hơn khoảng {temperature_difference:g}°C."
    else:
        cooler = "Nhiệt độ hai nơi tương đương nhau."

    score_difference = abs(climate_a.tourism_score - climate_b.tourism_score)
    if climate_a.tourism_score > climate_b.tourism_score:
        score = f"{name_a} nhích hơn {score_difference} điểm."
    elif climate_b.tourism_score > climate_a.tourism_score:
        score = f"{name_b} nhích hơn {score_difference} điểm."
    else:
        score = "Hai nơi ngang điểm nhau."
    return f"Tháng {month}, {drier} {cooler} {score}"


def get_year_recommendation(
    name_a: str,
    climate_a: LocationClimate,
    name_b: str,
    climate_b: LocationClimate,
) -> str:
    best_a = max(climate_a.months, key=lambda item: item.tourism_score)
    best_b = max(climate_b.months, key=lambda item: item.tourism_score)
    return (
        f"Nếu chưa chốt thời điểm: {name_a} đẹp nhất vào tháng {best_a.month} "
        f"({best_a.tourism_score} điểm), {name_b} đẹp nhất vào tháng "
        f"{best_b.month} ({best_b.tourism_score} điểm)."
    )
