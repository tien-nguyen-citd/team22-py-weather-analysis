from sqlalchemy.orm import Session

from weather_analysis.memory_cache import MemoryCache
from weather_analysis.services.current_temperature_service import (
    TemperatureCacheKey,
    get_current_temperatures,
)
from weather_analysis.services.system_settings_service import (
    FORECAST_CACHE_DURATION,
    update_setting,
)


class FakeTemperatureClient:
    def __init__(self) -> None:
        self.calls = 0

    def fetch_current_temperatures(
        self, locations: list[tuple[str, float, float]]
    ) -> dict[str, float]:
        self.calls += 1
        return {slug: 25.0 for slug, _, _ in locations}


def test_current_temperatures_are_cached(session: Session) -> None:
    client = FakeTemperatureClient()
    cache: MemoryCache[TemperatureCacheKey, dict[str, float]] = MemoryCache()

    first = get_current_temperatures(session, client, cache)
    second = get_current_temperatures(session, client, cache)

    assert first == second
    assert client.calls == 1


def test_current_temperature_cache_uses_configured_duration(
    session: Session,
) -> None:
    now = 100.0
    client = FakeTemperatureClient()
    cache: MemoryCache[TemperatureCacheKey, dict[str, float]] = MemoryCache(lambda: now)
    update_setting(session, FORECAST_CACHE_DURATION.key, 5)

    get_current_temperatures(session, client, cache)
    now += 6 * 60
    get_current_temperatures(session, client, cache)

    assert client.calls == 2
