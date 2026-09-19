from datetime import date, datetime, timedelta

from fastapi import APIRouter, HTTPException, status

from weather_analysis.api.dependencies import ArchiveCache, DbSession, WeatherClient
from weather_analysis.clients.open_meteo_client import (
    OpenMeteoArchive,
    VIETNAM_TIMEZONE,
    WeatherProviderError,
)
from weather_analysis.repositories.location_repository import LocationRepository


router = APIRouter(prefix="/api/locations", tags=["climate"])
ARCHIVE_CACHE_DURATION = timedelta(hours=24)


@router.get("/{slug}/climate", response_model=OpenMeteoArchive)
def get_climate_archive(
    slug: str,
    start_date: date,
    end_date: date,
    session: DbSession,
    client: WeatherClient,
    cache: ArchiveCache,
) -> OpenMeteoArchive:
    current_month_start = datetime.now(VIETNAM_TIMEZONE).date().replace(day=1)
    if end_date < start_date or end_date >= current_month_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Khoảng thời gian lịch sử không hợp lệ",
        )
    next_month = end_date + timedelta(days=1)
    if (
        next_month.day != 1
        or next_month.year <= 11
        or start_date != date(next_month.year - 11, next_month.month, 1)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Khoảng thời gian lịch sử không hợp lệ",
        )

    location = LocationRepository(session).find_by_slug(slug)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy địa điểm",
        )

    key = (location.latitude, location.longitude, start_date, end_date)
    try:
        return cache.get_or_create(
            key,
            lambda: client.fetch_archive(
                location.latitude, location.longitude, start_date, end_date
            ),
            ARCHIVE_CACHE_DURATION,
        )
    except WeatherProviderError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
