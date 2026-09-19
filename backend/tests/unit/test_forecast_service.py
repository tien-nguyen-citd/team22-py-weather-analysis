from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from weather_analysis.clients.open_meteo_client import (
    VIETNAM_TIMEZONE,
    OpenMeteoForecast,
)
from weather_analysis.memory_cache import MemoryCache
from weather_analysis.models import Location
from weather_analysis.services.forecast_service import (
    ForecastCacheKey,
    build_forecast,
    get_location_forecast,
)
from weather_analysis.services.location_service import LocationNotFoundError
from weather_analysis.services.system_settings_service import (
    FORECAST_CACHE_DURATION,
    update_setting,
)


class FakeForecastClient:
    def __init__(self, result: OpenMeteoForecast) -> None:
        self.result = result
        self.calls = 0

    def fetch_forecast(
        self,
        latitude: float,
        longitude: float,
    ) -> OpenMeteoForecast:
        del latitude, longitude
        self.calls += 1
        return self.result


def fixed_now() -> datetime:
    return datetime(2026, 9, 19, 14, 5, 12, tzinfo=VIETNAM_TIMEZONE)


def make_location() -> Location:
    return Location(
        name="Hà Nội",
        slug="ha-noi",
        region_code="dbbb",
        region_label="Đồng bằng Bắc Bộ",
        temp_offset=0,
        latitude=21.0285,
        longitude=105.8542,
        pin_order=2,
    )


def test_build_forecast_uses_fixed_time_and_vietnamese_day_labels(
    raw_forecast: OpenMeteoForecast,
) -> None:
    result = build_forecast(make_location(), raw_forecast, fixed_now())

    assert result.updated_at == raw_forecast.fetched_at
    assert result.temp_now == 30
    assert result.apparent_temp_now == 36
    assert result.rain_prob_now == 60
    assert result.details.aqi == 58
    assert result.details.sunshine_hours == 7.2
    assert result.details.rain_window == "14:00 – 17:00"
    assert all(window.start >= 14 for window in result.best_windows)
    assert [day.day_label for day in result.daily7[:3]] == [
        "Hôm nay",
        "Chủ Nhật",
        "Thứ Hai",
    ]
    assert len(result.hourly) == 24


def test_build_forecast_keeps_aqi_null_when_provider_has_no_air_quality(
    raw_forecast: OpenMeteoForecast,
) -> None:
    forecast_without_aqi = raw_forecast.model_copy(update={"us_aqi": None})

    result = build_forecast(make_location(), forecast_without_aqi, fixed_now())

    assert result.details.aqi is None
    assert result.details.aqi_label is None


def test_build_forecast_keeps_zero_sunshine_duration(
    raw_forecast: OpenMeteoForecast,
) -> None:
    forecast_without_sunshine = raw_forecast.model_copy(
        update={"daily_sunshine_duration": [0.0] * 7}
    )

    result = build_forecast(
        make_location(), forecast_without_sunshine, fixed_now()
    )

    assert result.details.sunshine_hours == 0


def test_build_forecast_keeps_sunshine_null_when_provider_has_no_data(
    raw_forecast: OpenMeteoForecast,
) -> None:
    forecast_without_sunshine = raw_forecast.model_copy(
        update={"daily_sunshine_duration": [None] * 7}
    )

    result = build_forecast(
        make_location(), forecast_without_sunshine, fixed_now()
    )

    assert result.details.sunshine_hours is None


def test_two_calls_for_same_location_only_fetch_once(
    session: Session,
    raw_forecast: OpenMeteoForecast,
) -> None:
    client = FakeForecastClient(raw_forecast)
    cache: MemoryCache[ForecastCacheKey, OpenMeteoForecast] = MemoryCache()

    first = get_location_forecast(session, "ha-noi", client, cache, fixed_now)
    second = get_location_forecast(session, "ha-noi", client, cache, fixed_now)

    assert client.calls == 1
    assert first.updated_at == second.updated_at


def test_locations_with_same_coordinates_share_cache(
    session: Session,
    raw_forecast: OpenMeteoForecast,
) -> None:
    client = FakeForecastClient(raw_forecast)
    cache: MemoryCache[ForecastCacheKey, OpenMeteoForecast] = MemoryCache()

    nghe_an = get_location_forecast(session, "nghe-an", client, cache, fixed_now)
    vinh = get_location_forecast(session, "vinh", client, cache, fixed_now)

    assert client.calls == 1
    assert nghe_an.location.slug == "nghe-an"
    assert vinh.location.slug == "vinh"


def test_forecast_uses_configured_cache_duration(
    session: Session,
    raw_forecast: OpenMeteoForecast,
) -> None:
    now = 100.0
    client = FakeForecastClient(raw_forecast)
    cache: MemoryCache[ForecastCacheKey, OpenMeteoForecast] = MemoryCache(
        lambda: now
    )
    update_setting(session, FORECAST_CACHE_DURATION.key, 5)

    get_location_forecast(session, "ha-noi", client, cache, fixed_now)
    now += 6 * 60
    get_location_forecast(session, "ha-noi", client, cache, fixed_now)

    assert client.calls == 2


def test_unknown_slug_raises_location_not_found(
    session: Session,
    raw_forecast: OpenMeteoForecast,
) -> None:
    client = FakeForecastClient(raw_forecast)
    cache: MemoryCache[ForecastCacheKey, OpenMeteoForecast] = MemoryCache()

    with pytest.raises(LocationNotFoundError):
        get_location_forecast(session, "khong-ton-tai", client, cache, fixed_now)

    assert client.calls == 0
