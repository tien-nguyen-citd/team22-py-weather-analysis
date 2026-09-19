from collections.abc import Iterator
from datetime import date
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from weather_analysis.clients.open_meteo_client import (
    OpenMeteoClient,
    OpenMeteoArchive,
    OpenMeteoForecast,
)
from weather_analysis.database import session_scope
from weather_analysis.memory_cache import MemoryCache
from weather_analysis.services.forecast_service import ForecastCacheKey


_open_meteo_http_client = httpx.Client(timeout=10)
_open_meteo_client = OpenMeteoClient(_open_meteo_http_client)
_forecast_cache: MemoryCache[ForecastCacheKey, OpenMeteoForecast] = MemoryCache()
ArchiveCacheKey = tuple[float, float, date, date]
_archive_cache: MemoryCache[ArchiveCacheKey, OpenMeteoArchive] = MemoryCache()
TemperatureCacheKey = tuple[tuple[str, float, float], ...]
_temperature_cache: MemoryCache[TemperatureCacheKey, dict[str, float]] = MemoryCache()


def get_session() -> Iterator[Session]:
    """Cấp một database session riêng cho mỗi request."""
    with session_scope() as session:
        yield session


def get_current_username(request: Request) -> str:
    """Đọc người dùng đã đăng nhập từ session."""
    username = request.session.get("username")
    if not isinstance(username, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bạn cần đăng nhập",
        )
    return username


def get_open_meteo_client() -> OpenMeteoClient:
    return _open_meteo_client


def get_forecast_cache() -> MemoryCache[ForecastCacheKey, OpenMeteoForecast]:
    return _forecast_cache


def get_archive_cache() -> MemoryCache[ArchiveCacheKey, OpenMeteoArchive]:
    return _archive_cache


def get_temperature_cache() -> MemoryCache[TemperatureCacheKey, dict[str, float]]:
    return _temperature_cache


DbSession = Annotated[Session, Depends(get_session)]
CurrentUsername = Annotated[str, Depends(get_current_username)]
WeatherClient = Annotated[OpenMeteoClient, Depends(get_open_meteo_client)]
ForecastCache = Annotated[
    MemoryCache[ForecastCacheKey, OpenMeteoForecast],
    Depends(get_forecast_cache),
]
ArchiveCache = Annotated[
    MemoryCache[ArchiveCacheKey, OpenMeteoArchive],
    Depends(get_archive_cache),
]
TemperatureCache = Annotated[
    MemoryCache[TemperatureCacheKey, dict[str, float]],
    Depends(get_temperature_cache),
]
