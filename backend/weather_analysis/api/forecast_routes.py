from fastapi import APIRouter, HTTPException, status

from weather_analysis.api.dependencies import (
    DbSession,
    ForecastCache,
    WeatherClient,
)
from weather_analysis.api.schemas import LocationForecastResponse
from weather_analysis.clients.open_meteo_client import WeatherProviderError
from weather_analysis.services.forecast_service import get_location_forecast
from weather_analysis.services.location_service import LocationNotFoundError


router = APIRouter(prefix="/api/locations", tags=["forecast"])


@router.get("/{slug}/forecast", response_model=LocationForecastResponse)
def get_forecast(
    slug: str,
    session: DbSession,
    client: WeatherClient,
    cache: ForecastCache,
) -> LocationForecastResponse:
    try:
        forecast = get_location_forecast(session, slug, client, cache)
    except LocationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy địa điểm",
        ) from error
    except WeatherProviderError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    return LocationForecastResponse.model_validate(forecast)
