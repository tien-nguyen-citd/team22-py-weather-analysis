from datetime import date, timedelta

from httpx import Client

from weather_analysis.api.app import app
from weather_analysis.api.dependencies import get_open_meteo_client
from weather_analysis.clients.open_meteo_client import (
    OpenMeteoArchive,
    WeatherProviderError,
)


class FakeArchiveClient:
    def __init__(self, error: bool = False) -> None:
        self.error = error

    def fetch_archive(
        self,
        _latitude: float,
        _longitude: float,
        start_date: date,
        end_date: date,
    ) -> OpenMeteoArchive:
        if self.error:
            raise WeatherProviderError("Không lấy được dữ liệu lịch sử từ Open-Meteo")
        dates = [
            start_date + timedelta(days=offset)
            for offset in range((end_date - start_date).days + 1)
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


def override_client(client: FakeArchiveClient) -> None:
    app.dependency_overrides[get_open_meteo_client] = lambda: client


def test_history_returns_camel_case_response(client: Client) -> None:
    override_client(FakeArchiveClient())
    try:
        response = client.get("/api/locations/ha-noi/history")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["location"]["slug"] == "ha-noi"
    assert "–" in body["recentPeriod"]
    assert len(body["months"]) == 12
    assert "baselineRain" in body["months"][0]
    assert body["wettestMonth"]["rainyDays"] > 0


def test_compare_returns_camel_case_response(client: Client) -> None:
    override_client(FakeArchiveClient())
    try:
        response = client.get("/api/locations/compare?a=ha-noi&b=da-lat&month=12")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["month"] == 12
    assert body["a"]["location"]["slug"] == "ha-noi"
    assert body["b"]["location"]["slug"] == "da-lat"
    assert len(body["a"]["months"]) == 12
    assert "tourismScore" in body["a"]["months"][0]
    assert "yearRecommendation" in body


def test_climate_routes_validate_locations_month_and_provider_errors(
    client: Client,
) -> None:
    override_client(FakeArchiveClient())
    try:
        missing = client.get("/api/locations/khong-ton-tai/history")
        invalid_month = client.get("/api/locations/compare?a=ha-noi&b=da-lat&month=13")
    finally:
        app.dependency_overrides.clear()

    override_client(FakeArchiveClient(error=True))
    try:
        failed = client.get("/api/locations/ha-noi/history")
    finally:
        app.dependency_overrides.clear()

    assert missing.status_code == 404
    assert invalid_month.status_code == 422
    assert failed.status_code == 502
    assert "Open-Meteo" in failed.json()["detail"]
