from datetime import date
from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Client

from weather_analysis.api.climate_routes import router
from weather_analysis.api.dependencies import (
    get_archive_cache,
    get_open_meteo_client,
    get_session,
)
from weather_analysis.clients.open_meteo_client import (
    OpenMeteoArchive,
    WeatherProviderError,
)
from weather_analysis.memory_cache import MemoryCache
from weather_analysis.models import Location


class FakeSession:
    def __init__(self, location: Location | None) -> None:
        self.location = location

    def scalar(self, _statement: object) -> Location | None:
        return self.location


class FakeArchiveClient:
    def __init__(self, error: bool = False) -> None:
        self.calls = 0
        self.error = error

    def fetch_archive(
        self, _latitude: float, _longitude: float, _start: date, _end: date
    ) -> OpenMeteoArchive:
        self.calls += 1
        if self.error:
            raise WeatherProviderError("Không lấy được dữ liệu lịch sử từ Open-Meteo")
        return OpenMeteoArchive.model_validate(
            {
                "daily": {
                    "time": ["2026-08-31"],
                    "precipitation_sum": [2],
                    "temperature_2m_mean": [26],
                }
            }
        )


def build_app(
    location: Location | None,
    archive_client: FakeArchiveClient,
    cache: MemoryCache[tuple[float, float, date, date], OpenMeteoArchive] | None = None,
) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_session] = lambda: FakeSession(location)
    app.dependency_overrides[get_open_meteo_client] = lambda: archive_client
    archive_cache = cache or MemoryCache[
        tuple[float, float, date, date], OpenMeteoArchive
    ]()
    app.dependency_overrides[get_archive_cache] = lambda: archive_cache
    return app


def test_climate_route_returns_archive_and_reuses_cache() -> None:
    location = Location(
        name="Hà Nội",
        slug="ha-noi",
        region_code="dbbb",
        region_label="Đồng bằng Bắc Bộ",
        temp_offset=0,
        latitude=21.0285,
        longitude=105.8542,
        pin_order=1,
    )
    provider = FakeArchiveClient()
    app = build_app(location, provider)

    with cast(Client, TestClient(app)) as client:
        url = "/api/locations/ha-noi/climate?start_date=2015-09-01&end_date=2026-08-31"
        first = client.get(url)
        second = client.get(url)

    assert first.status_code == 200
    assert first.json()["daily"]["precipitation_sum"] == [2.0]
    assert second.status_code == 200
    assert provider.calls == 1


def test_climate_route_handles_missing_location_and_provider_error() -> None:
    url = "/api/locations/ha-noi/climate?start_date=2015-09-01&end_date=2026-08-31"
    with cast(Client, TestClient(build_app(None, FakeArchiveClient()))) as client:
        missing = client.get(url)
    assert missing.status_code == 404

    location = Location(
        name="Hà Nội",
        slug="ha-noi",
        region_code="dbbb",
        region_label="Đồng bằng Bắc Bộ",
        temp_offset=0,
        latitude=21.0285,
        longitude=105.8542,
        pin_order=1,
    )
    with cast(Client, TestClient(build_app(location, FakeArchiveClient(error=True)))) as client:
        failed = client.get(url)
    assert failed.status_code == 502
    assert "Open-Meteo" in failed.json()["detail"]


def test_climate_route_rejects_unsupported_date_range() -> None:
    provider = FakeArchiveClient()
    with cast(Client, TestClient(build_app(None, provider))) as client:
        response = client.get(
            "/api/locations/ha-noi/climate?start_date=2026-08-01&end_date=2026-08-31"
        )

    assert response.status_code == 422
    assert provider.calls == 0
