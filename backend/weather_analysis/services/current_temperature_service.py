from datetime import timedelta
from typing import Protocol

from sqlalchemy.orm import Session

from weather_analysis.memory_cache import MemoryCache
from weather_analysis.repositories.location_repository import LocationRepository
from weather_analysis.services.system_settings_service import (
    FORECAST_CACHE_DURATION,
    get_setting_value,
)


TemperatureCacheKey = tuple[tuple[str, float, float], ...]


class CurrentTemperatureClient(Protocol):
    def fetch_current_temperatures(
        self, locations: list[tuple[str, float, float]]
    ) -> dict[str, float]: ...


def get_current_temperatures(
    session: Session,
    client: CurrentTemperatureClient,
    cache: MemoryCache[TemperatureCacheKey, dict[str, float]],
) -> dict[str, float]:
    locations = LocationRepository(session).list_all()
    key = tuple(
        (location.slug, location.latitude, location.longitude) for location in locations
    )
    if not key:
        return {}
    cache_duration = get_setting_value(session, FORECAST_CACHE_DURATION)
    return cache.get_or_create(
        key,
        lambda: client.fetch_current_temperatures(list(key)),
        timedelta(minutes=cache_duration),
    )
