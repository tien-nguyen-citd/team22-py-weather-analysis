from dataclasses import dataclass
from datetime import date, timedelta
import math
from typing import Protocol

from sqlalchemy.orm import Session

from weather_analysis.clients.open_meteo_client import OpenMeteoArchive
from weather_analysis.models import DailyWeather, Location
from weather_analysis.repositories.daily_weather_repository import (
    DailyWeatherRepository,
    MonthlyWeatherAggregate,
)
from weather_analysis.services.scoring import calculate_tourism_score, js_round


ERA5_DELAY_DAYS = 5


class ClimateDataError(Exception):
    """Dữ liệu lịch sử không đầy đủ hoặc không hợp lệ."""


class ClimateClient(Protocol):
    def fetch_archive(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> OpenMeteoArchive: ...


@dataclass(frozen=True)
class ClimatePeriod:
    start_date: date
    end_date: date
    recent_start: date
    baseline_end: date
    recent_period: str
    baseline_period: str


@dataclass(frozen=True)
class MonthClimate:
    month: int
    temperature: float
    rain: int
    rainy_days: int
    tourism_score: int


@dataclass(frozen=True)
class RecentMonthClimate:
    year: int
    month: int
    temperature: float
    rain: int
    rainy_days: int


@dataclass(frozen=True)
class LocationClimate:
    recent_period: str
    baseline_period: str
    months: list[MonthClimate]
    recent_months: list[RecentMonthClimate]


@dataclass(frozen=True)
class ClimateLocation:
    name: str
    slug: str
    region: str
    region_label: str
    temp_offset: float
    lat: float
    lon: float


def to_climate_location(location: Location) -> ClimateLocation:
    return ClimateLocation(
        name=location.name,
        slug=location.slug,
        region=location.region_code,
        region_label=location.region_label,
        temp_offset=location.temp_offset,
        lat=location.latitude,
        lon=location.longitude,
    )


def calculate_climate_period(today: date) -> ClimatePeriod:
    available_date = today - timedelta(days=ERA5_DELAY_DAYS)
    current_month_start = available_date.replace(day=1)
    end_date = current_month_start - timedelta(days=1)
    recent_start = _add_months(current_month_start, -12)
    baseline_end = recent_start - timedelta(days=1)
    start_date = _add_months(recent_start, -120)
    return ClimatePeriod(
        start_date=start_date,
        end_date=end_date,
        recent_start=recent_start,
        baseline_end=baseline_end,
        recent_period=(f"{_format_month(recent_start)}–{_format_month(end_date)}"),
        baseline_period=(f"{_format_month(start_date)}–{_format_month(baseline_end)}"),
    )


def get_location_climate(
    session: Session,
    location: Location,
    client: ClimateClient,
    today: date,
) -> LocationClimate:
    period = calculate_climate_period(today)
    repository = DailyWeatherRepository(session)
    minimum, maximum = repository.get_date_bounds(location.latitude, location.longitude)

    if minimum is None or maximum is None:
        _fetch_and_store(
            repository, location, client, period.start_date, period.end_date
        )
    else:
        if minimum > period.start_date:
            missing_end = min(minimum - timedelta(days=1), period.end_date)
            _fetch_and_store(
                repository, location, client, period.start_date, missing_end
            )
        if maximum < period.end_date:
            missing_start = max(maximum + timedelta(days=1), period.start_date)
            _fetch_and_store(
                repository, location, client, missing_start, period.end_date
            )

    expected_days = (period.end_date - period.start_date).days + 1
    actual_days = repository.count_days(
        location.latitude,
        location.longitude,
        period.start_date,
        period.end_date,
    )
    if actual_days != expected_days:
        raise ClimateDataError("Dữ liệu lịch sử chưa đủ ngày")

    aggregates = repository.aggregate_months(
        location.latitude,
        location.longitude,
        period.start_date,
        period.end_date,
    )
    return _build_location_climate(period, aggregates)


def _fetch_and_store(
    repository: DailyWeatherRepository,
    location: Location,
    client: ClimateClient,
    start_date: date,
    end_date: date,
) -> None:
    if start_date > end_date:
        return
    archive = client.fetch_archive(
        location.latitude, location.longitude, start_date, end_date
    )
    daily = archive.daily
    if not (
        len(daily.time)
        == len(daily.precipitation_sum)
        == len(daily.temperature_2m_mean)
    ):
        raise ClimateDataError("Dữ liệu lịch sử không hợp lệ")
    expected_days = (end_date - start_date).days + 1
    if len(daily.time) != expected_days:
        raise ClimateDataError("Dữ liệu lịch sử chưa đủ ngày")

    rows: list[DailyWeather] = []
    for index, (weather_date, rain, temperature) in enumerate(
        zip(
            daily.time,
            daily.precipitation_sum,
            daily.temperature_2m_mean,
            strict=True,
        )
    ):
        if weather_date != start_date + timedelta(days=index):
            raise ClimateDataError("Dữ liệu lịch sử không hợp lệ")
        if rain is None or temperature is None:
            continue
        if rain < 0 or not math.isfinite(rain) or not math.isfinite(temperature):
            raise ClimateDataError("Dữ liệu lịch sử không hợp lệ")
        rows.append(
            DailyWeather(
                latitude=location.latitude,
                longitude=location.longitude,
                date=weather_date,
                temperature_mean=temperature,
                precipitation_sum=rain,
            )
        )
    repository.add_many(rows)


def _build_location_climate(
    period: ClimatePeriod,
    aggregates: list[MonthlyWeatherAggregate],
) -> LocationClimate:
    by_year_month = {
        (aggregate.year, aggregate.month): aggregate for aggregate in aggregates
    }
    recent_months: list[RecentMonthClimate] = []
    for offset in range(12):
        month_date = _add_months(period.recent_start, offset)
        aggregate = by_year_month.get((month_date.year, month_date.month))
        if aggregate is None:
            raise ClimateDataError("Dữ liệu lịch sử chưa đủ tháng")
        recent_months.append(
            RecentMonthClimate(
                year=aggregate.year,
                month=aggregate.month,
                temperature=_round_one(aggregate.temperature_mean),
                rain=js_round(aggregate.precipitation_sum),
                rainy_days=aggregate.rainy_days,
            )
        )

    months: list[MonthClimate] = []
    baseline_aggregates = [
        aggregate
        for aggregate in aggregates
        if date(aggregate.year, aggregate.month, 1) < period.recent_start
    ]
    for month in range(1, 13):
        matching = [
            aggregate for aggregate in baseline_aggregates if aggregate.month == month
        ]
        if len(matching) != 10:
            raise ClimateDataError("Dữ liệu lịch sử chưa đủ 10 năm")
        temperature = _round_one(
            sum(item.temperature_mean for item in matching) / len(matching)
        )
        rain = js_round(
            sum(item.precipitation_sum for item in matching) / len(matching)
        )
        rainy_days = js_round(sum(item.rainy_days for item in matching) / len(matching))
        months.append(
            MonthClimate(
                month=month,
                temperature=temperature,
                rain=rain,
                rainy_days=rainy_days,
                tourism_score=calculate_tourism_score(temperature, rainy_days),
            )
        )

    return LocationClimate(
        recent_period=period.recent_period,
        baseline_period=period.baseline_period,
        months=months,
        recent_months=recent_months,
    )


def _add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    return date(month_index // 12, month_index % 12 + 1, 1)


def _format_month(value: date) -> str:
    return f"{value.month:02d}/{value.year}"


def _round_one(value: float) -> float:
    return js_round(value * 10) / 10
