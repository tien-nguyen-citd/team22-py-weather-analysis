from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from weather_analysis.api.dependencies import DbSession, WeatherClient
from weather_analysis.api.schemas import (
    LocationComparisonResponse,
    LocationHistoryResponse,
)
from weather_analysis.clients.open_meteo_client import WeatherProviderError
from weather_analysis.services.climate_service import ClimateDataError
from weather_analysis.services.compare_service import compare_locations
from weather_analysis.services.history_service import get_location_history
from weather_analysis.services.location_service import LocationNotFoundError


router = APIRouter(prefix="/api/locations", tags=["climate"])


@router.get("/compare", response_model=LocationComparisonResponse)
def get_location_comparison(
    a: str,
    b: str,
    month: Annotated[int, Query(ge=1, le=12)],
    session: DbSession,
    client: WeatherClient,
) -> LocationComparisonResponse:
    try:
        comparison = compare_locations(session, a, b, month, client)
    except LocationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy địa điểm",
        ) from error
    except (WeatherProviderError, ClimateDataError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    return LocationComparisonResponse.model_validate(comparison)


@router.get("/{slug}/history", response_model=LocationHistoryResponse)
def get_history(
    slug: str,
    session: DbSession,
    client: WeatherClient,
) -> LocationHistoryResponse:
    try:
        history = get_location_history(session, slug, client)
    except LocationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy địa điểm",
        ) from error
    except (WeatherProviderError, ClimateDataError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    return LocationHistoryResponse.model_validate(history)
