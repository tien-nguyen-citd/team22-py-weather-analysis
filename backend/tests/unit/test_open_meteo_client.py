from datetime import date
from typing import Any

import httpx
import pytest

from weather_analysis.clients.open_meteo_client import (
    OpenMeteoClient,
    WeatherProviderError,
)


def test_fetch_forecast_sends_expected_queries_and_parses_response(
    open_meteo_payload: dict[str, Any],
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        key = "air_quality" if "air-quality" in request.url.host else "forecast"
        return httpx.Response(200, json=open_meteo_payload[key])

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        result = OpenMeteoClient(http_client).fetch_forecast(21.0285, 105.8542)

    assert len(requests) == 2
    assert requests[0].url.params["latitude"] == "21.0285"
    assert requests[0].url.params["longitude"] == "105.8542"
    assert requests[0].url.params["forecast_days"] == "7"
    assert requests[0].url.params["timezone"] == "Asia/Ho_Chi_Minh"
    assert "temperature_2m" in requests[0].url.params["hourly"]
    assert requests[1].url.params["hourly"] == "us_aqi"
    assert result.hourly_temperature[14] == 30.4
    assert result.daily_time[0].isoformat() == "2026-09-19"
    assert result.us_aqi is not None
    assert result.us_aqi[14] == 58


def test_fetch_archive_sends_era5_query_and_returns_daily_data() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "daily": {
                    "time": ["2026-08-30", "2026-08-31"],
                    "precipitation_sum": [1.0, 2.0],
                    "temperature_2m_mean": [25.0, 26.0],
                }
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        archive = OpenMeteoClient(http_client).fetch_archive(
            21.0285, 105.8542, date(2015, 9, 1), date(2026, 8, 31)
        )

    assert len(requests) == 1
    assert requests[0].url.host == "archive-api.open-meteo.com"
    assert requests[0].url.params["start_date"] == "2015-09-01"
    assert requests[0].url.params["end_date"] == "2026-08-31"
    assert requests[0].url.params["daily"] == "precipitation_sum,temperature_2m_mean"
    assert requests[0].url.params["models"] == "era5"
    assert archive.daily.precipitation_sum == [1.0, 2.0]


def test_fetch_archive_wraps_invalid_provider_response() -> None:
    with httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json={}))
    ) as http_client:
        with pytest.raises(WeatherProviderError, match="dữ liệu lịch sử"):
            OpenMeteoClient(http_client).fetch_archive(
                21, 105, date(2015, 9, 1), date(2026, 8, 31)
            )


def test_fetch_current_temperatures_batches_locations() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        latitudes = request.url.params["latitude"].split(",")
        assert len(latitudes) <= 25
        assert request.url.params["current"] == "temperature_2m"
        items = [
            {"current": {"temperature_2m": float(latitude)}}
            for latitude in latitudes
        ]
        return httpx.Response(200, json=items if len(items) > 1 else items[0])

    locations = [(f"place-{index}", float(index), 105.0) for index in range(51)]
    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        temperatures = OpenMeteoClient(http_client).fetch_current_temperatures(
            locations
        )

    assert len(requests) == 3
    assert temperatures == {
        f"place-{index}": float(index) for index in range(51)
    }


def test_fetch_forecast_wraps_http_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(WeatherProviderError, match="Open-Meteo"):
            OpenMeteoClient(http_client).fetch_forecast(21, 105)


def test_fetch_forecast_wraps_invalid_response() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"hourly": {}, "daily": {}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        with pytest.raises(WeatherProviderError, match="Open-Meteo"):
            OpenMeteoClient(http_client).fetch_forecast(21, 105)


def test_air_quality_error_returns_forecast_without_aqi(
    open_meteo_payload: dict[str, Any],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "air-quality" in request.url.host:
            return httpx.Response(503)
        return httpx.Response(200, json=open_meteo_payload["forecast"])

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        result = OpenMeteoClient(http_client).fetch_forecast(21, 105)

    assert result.us_aqi is None
