from datetime import date, timedelta

import pytest
from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from tests.advisory_helpers import FakeArchiveClient
from weather_analysis.advisory.models import AdvisoryRequest, MonthRange, WeatherDay
from weather_analysis.advisory.repository import AdvisoryWeatherRepository
from weather_analysis.advisory.service import get_advice
from weather_analysis.clients.open_meteo_client import WeatherProviderError
from weather_analysis.models import DailyWeather
from weather_analysis.services.climate_service import (
    ClimateDataError,
    calculate_climate_period,
)
from weather_analysis.services.location_service import LocationNotFoundError


TODAY = date(2026, 9, 20)
REQUEST = AdvisoryRequest("ha-noi", MonthRange("2027-01", "2027-03"), "travel")


def test_first_load_cached_read_and_baseline_excludes_recent_year(
    session: Session,
) -> None:
    client = FakeArchiveClient()
    period = calculate_climate_period(TODAY)
    first = get_advice(session, REQUEST, client, TODAY)
    # Mưa lớn trong năm gần nhất không thuộc baseline dùng để tư vấn.
    session.execute(
        update(DailyWeather)
        .where(DailyWeather.date > period.baseline_end)
        .values(precipitation_sum=100)
    )
    cached = get_advice(session, REQUEST, client, TODAY)
    assert len(client.calls) == 1
    assert client.calls[0][2:] == (period.start_date, period.end_date)
    assert first == cached
    assert first.baseline_start == date(2015, 9, 1)
    assert first.baseline_end == date(2025, 8, 31)
    assert all(item.score == 100 for item in first.candidates)
    assert all(item.sample_years == 10 for item in first.candidates)


def test_repository_filters_coordinates_and_date_bounds(session: Session) -> None:
    target_date = date(2020, 1, 2)
    session.add_all(
        [
            DailyWeather(
                latitude=10,
                longitude=20,
                date=target_date,
                temperature_mean=25,
                precipitation_sum=2,
            ),
            DailyWeather(
                latitude=11,
                longitude=20,
                date=target_date,
                temperature_mean=30,
                precipitation_sum=3,
            ),
            DailyWeather(
                latitude=10,
                longitude=21,
                date=target_date,
                temperature_mean=31,
                precipitation_sum=4,
            ),
            DailyWeather(
                latitude=10,
                longitude=20,
                date=target_date - timedelta(days=1),
                temperature_mean=32,
                precipitation_sum=5,
            ),
            DailyWeather(
                latitude=10,
                longitude=20,
                date=target_date + timedelta(days=1),
                temperature_mean=33,
                precipitation_sum=6,
            ),
        ]
    )
    session.flush()
    days = AdvisoryWeatherRepository(session).read_days(
        10, 20, target_date, target_date
    )
    assert days == [WeatherDay(target_date, 25, 2)]
    assert not session.new and not session.dirty and not session.deleted


@pytest.mark.parametrize("problem", ["missing", "negative_rain"])
def test_bad_cached_data_is_not_silently_used(session: Session, problem: str) -> None:
    client = FakeArchiveClient()
    get_advice(session, REQUEST, client, TODAY)
    if problem == "missing":
        session.execute(
            delete(DailyWeather).where(DailyWeather.date == date(2020, 5, 10))
        )
    else:
        session.execute(
            update(DailyWeather)
            .where(DailyWeather.date == date(2020, 5, 10))
            .values(precipitation_sum=-1)
        )
    with pytest.raises(ClimateDataError):
        get_advice(session, REQUEST, client, TODAY)
    assert len(client.calls) == 1


def test_provider_and_incomplete_archive_errors(session: Session) -> None:
    client = FakeArchiveClient()
    client.fail = True
    with pytest.raises(WeatherProviderError):
        get_advice(session, REQUEST, client, TODAY)
    client.fail = False
    client.omit_last_day = True
    with pytest.raises(ClimateDataError, match="chưa đủ ngày"):
        get_advice(session, REQUEST, client, TODAY)


def test_missing_location_does_not_fetch_history(session: Session) -> None:
    client = FakeArchiveClient()
    with pytest.raises(LocationNotFoundError):
        get_advice(session, AdvisoryRequest("khong-ton-tai"), client, TODAY)
    assert client.calls == []
