from datetime import date, datetime

import httpx

from weather_analysis.advisory import destinations
from weather_analysis.clients.open_meteo_client import (
    VIETNAM_TIMEZONE,
    OpenMeteoClient,
    WeatherProviderError,
)
from weather_analysis.database import ensure_database_exists, session_scope
from weather_analysis.repositories.location_repository import LocationRepository
from weather_analysis.services.climate_service import ClimateClient, ClimateDataError, get_location_climate


def preload_all(client: ClimateClient, today: date) -> list[str]:
    """Nạp lịch sử khí hậu cho từng điểm trong danh mục, mỗi điểm một giao dịch riêng."""
    failed_slugs: list[str] = []
    total = len(destinations.DESTINATIONS)
    for index, destination in enumerate(destinations.DESTINATIONS, start=1):
        label = destination.slug
        try:
            with session_scope() as session:
                location = LocationRepository(session).find_by_slug(destination.slug)
                if location is None:
                    print(f"[{index}/{total}] {label}: bỏ qua, không có trong danh mục địa điểm")
                    failed_slugs.append(destination.slug)
                    continue
                label = location.name
                get_location_climate(session, location, client, today)
        except (WeatherProviderError, ClimateDataError) as error:
            print(f"[{index}/{total}] {label}: lỗi – {error}")
            failed_slugs.append(destination.slug)
            continue
        print(f"[{index}/{total}] {label}: xong")
    return failed_slugs


def main() -> None:
    ensure_database_exists()
    today = datetime.now(VIETNAM_TIMEZONE).date()
    with httpx.Client(timeout=10) as http_client:
        client = OpenMeteoClient(http_client)
        failed_slugs = preload_all(client, today)

    total = len(destinations.DESTINATIONS)
    print(f"Hoàn tất {total - len(failed_slugs)}/{total} điểm.")
    if failed_slugs:
        print("Còn điểm lỗi, chạy lại lệnh để nạp tiếp.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
