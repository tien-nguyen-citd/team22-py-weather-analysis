from httpx import Client

from weather_analysis.api.app import app
from weather_analysis.api.dependencies import (
    get_open_meteo_client,
    get_temperature_cache,
)
from weather_analysis.clients.open_meteo_client import WeatherProviderError
from weather_analysis.memory_cache import MemoryCache
from weather_analysis.services.current_temperature_service import (
    TemperatureCacheKey,
)


class FakeTemperatureClient:
    def __init__(self, error: bool = False) -> None:
        self.error = error

    def fetch_current_temperatures(
        self, locations: list[tuple[str, float, float]]
    ) -> dict[str, float]:
        if self.error:
            raise WeatherProviderError(
                "Không lấy được nhiệt độ hiện tại từ Open-Meteo"
            )
        return {slug: 28.4 for slug, _, _ in locations}


def test_list_locations_returns_camel_case_fields(client: Client) -> None:
    response = client.get("/api/locations?q=da%20nang")

    assert response.status_code == 200
    assert response.json() == [
        {
            "name": "Đà Nẵng",
            "slug": "da-nang",
            "region": "trungtrung",
            "regionLabel": "Trung Trung Bộ",
            "tempOffset": 0.0,
            "lat": 16.0544,
            "lon": 108.2022,
        }
    ]


def test_list_locations_returns_all_for_blank_query(client: Client) -> None:
    response = client.get("/api/locations?q=")

    assert response.status_code == 200
    assert len(response.json()) == 91


def test_list_pinned_locations_returns_configured_order(client: Client) -> None:
    response = client.get("/api/locations/pinned")

    assert response.status_code == 200
    assert [location["name"] for location in response.json()] == [
        "Hồ Chí Minh",
        "Hà Nội",
        "Đà Nẵng",
        "Đà Lạt",
        "Nha Trang",
        "Huế",
    ]


def test_current_temperatures_returns_data_and_provider_error(
    client: Client,
) -> None:
    success_cache: MemoryCache[TemperatureCacheKey, dict[str, float]] = (
        MemoryCache()
    )
    app.dependency_overrides[get_open_meteo_client] = lambda: FakeTemperatureClient()
    app.dependency_overrides[get_temperature_cache] = lambda: success_cache
    try:
        response = client.get("/api/locations/temperatures")
    finally:
        app.dependency_overrides.clear()

    app.dependency_overrides[get_open_meteo_client] = lambda: FakeTemperatureClient(
        error=True
    )
    error_cache: MemoryCache[TemperatureCacheKey, dict[str, float]] = MemoryCache()
    app.dependency_overrides[get_temperature_cache] = lambda: error_cache
    try:
        failed = client.get("/api/locations/temperatures")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["ha-noi"] == 28.4
    assert failed.status_code == 502
