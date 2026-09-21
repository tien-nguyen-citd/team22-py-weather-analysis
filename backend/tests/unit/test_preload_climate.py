from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tests.advisory_helpers import FakeArchiveClient
from weather_analysis import preload_climate
from weather_analysis.advisory import destinations
from weather_analysis.advisory.destinations import Destination
from weather_analysis.clients.open_meteo_client import OpenMeteoArchive
from weather_analysis.models import DailyWeather
from weather_analysis.services.location_service import get_location_by_slug


TODAY = date(2026, 9, 20)


class FlakyClient(FakeArchiveClient):
    """Chỉ thất bại từ lượt gọi thứ `fail_after` trở đi, để mô phỏng một điểm lỗi."""

    def __init__(self, fail_after: int) -> None:
        super().__init__()
        self._fail_after = fail_after

    def fetch_archive(
        self, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> OpenMeteoArchive:
        if len(self.calls) >= self._fail_after:
            self.fail = True
        return super().fetch_archive(latitude, longitude, start_date, end_date)


def test_one_failure_does_not_roll_back_points_already_loaded(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        destinations,
        "DESTINATIONS",
        (Destination("ha-noi", False), Destination("da-nang", True)),
    )
    client = FlakyClient(fail_after=1)

    failed_slugs = preload_climate.preload_all(client, TODAY)

    assert failed_slugs == ["da-nang"]
    ha_noi = get_location_by_slug(session, "ha-noi")
    stored_days = session.scalar(
        select(func.count())
        .select_from(DailyWeather)
        .where(
            DailyWeather.latitude == ha_noi.latitude,
            DailyWeather.longitude == ha_noi.longitude,
        )
    )
    assert stored_days is not None and stored_days > 0


def test_destination_missing_from_catalog_counts_as_failed(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        destinations,
        "DESTINATIONS",
        (Destination("khong-ton-tai", False),),
    )

    failed_slugs = preload_climate.preload_all(FakeArchiveClient(), TODAY)

    assert failed_slugs == ["khong-ton-tai"]
