from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from weather_analysis.clients.open_meteo_client import OpenMeteoArchive
from weather_analysis.models import Location
from weather_analysis.repositories.location_repository import LocationRepository
from weather_analysis.services.climate_service import (
    ClimateDataError,
    calculate_climate_period,
    get_location_climate,
)


class FakeArchiveClient:
    def __init__(self, omit_last_day: bool = False) -> None:
        self.calls: list[tuple[date, date]] = []
        self.omit_last_day = omit_last_day

    def fetch_archive(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> OpenMeteoArchive:
        del latitude, longitude
        self.calls.append((start_date, end_date))
        actual_end = end_date - timedelta(days=1) if self.omit_last_day else end_date
        dates = [
            start_date + timedelta(days=offset)
            for offset in range((actual_end - start_date).days + 1)
        ]
        return OpenMeteoArchive.model_validate(
            {
                "daily": {
                    "time": dates,
                    "precipitation_sum": [1.0] * len(dates),
                    "temperature_2m_mean": [25.0] * len(dates),
                }
            }
        )


def get_location(session: Session) -> Location:
    location = LocationRepository(session).find_by_slug("ha-noi")
    assert location is not None
    return location


def test_calculate_period_accounts_for_era5_delay() -> None:
    regular = calculate_climate_period(date(2026, 9, 19))
    early_month = calculate_climate_period(date(2026, 9, 3))

    assert regular.recent_period == "09/2025–08/2026"
    assert regular.baseline_period == "09/2015–08/2025"
    assert early_month.recent_period == "08/2025–07/2026"


def test_archive_is_loaded_once_then_only_new_month_is_added(
    session: Session,
) -> None:
    client = FakeArchiveClient()
    location = get_location(session)

    first = get_location_climate(session, location, client, date(2026, 9, 19))
    second = get_location_climate(session, location, client, date(2026, 9, 19))
    advanced = get_location_climate(session, location, client, date(2026, 10, 10))

    assert client.calls == [
        (date(2015, 9, 1), date(2026, 8, 31)),
        (date(2026, 9, 1), date(2026, 9, 30)),
    ]
    assert first.recent_period == second.recent_period
    assert advanced.recent_period == "10/2025–09/2026"
    assert first.months[0].rainy_days == 31


def test_incomplete_archive_raises_error(session: Session) -> None:
    with pytest.raises(ClimateDataError, match="chưa đủ ngày"):
        get_location_climate(
            session,
            get_location(session),
            FakeArchiveClient(omit_last_day=True),
            date(2026, 9, 19),
        )
