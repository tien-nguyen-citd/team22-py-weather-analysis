from datetime import timedelta

from fastapi import APIRouter, HTTPException, status

from weather_analysis.api.dependencies import DbSession, TemperatureCache, WeatherClient
from weather_analysis.api.schemas import LocationResponse
from weather_analysis.clients.open_meteo_client import WeatherProviderError
from weather_analysis.repositories.location_repository import LocationRepository
from weather_analysis.services.location_service import (
    get_pinned_locations,
    search_locations,
)


router = APIRouter(prefix="/api/locations", tags=["locations"])


@router.get("")
def list_locations(session: DbSession, q: str = "") -> list[LocationResponse]:
    return [
        LocationResponse.from_model(location)
        for location in search_locations(session, q)
    ]


@router.get("/pinned")
def list_pinned_locations(session: DbSession) -> list[LocationResponse]:
    return [
        LocationResponse.from_model(location)
        for location in get_pinned_locations(session)
    ]


@router.get("/temperatures")
def list_current_temperatures(
    session: DbSession, client: WeatherClient, cache: TemperatureCache
) -> dict[str, float]:
    locations = LocationRepository(session).list_all()
    key = tuple(
        (location.slug, location.latitude, location.longitude)
        for location in locations
    )
    if not key:
        return {}
    try:
        return cache.get_or_create(
            key,
            lambda: client.fetch_current_temperatures(list(key)),
            timedelta(minutes=30),
        )
    except WeatherProviderError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
