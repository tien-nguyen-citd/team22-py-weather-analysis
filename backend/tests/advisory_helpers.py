from collections.abc import Callable
from datetime import date, timedelta

from weather_analysis.advisory.models import WeatherDay
from weather_analysis.clients.open_meteo_client import (
    OpenMeteoArchive,
    WeatherProviderError,
)
from weather_analysis.services.climate_service import ClimatePeriod


def constant_weather(_day: date) -> tuple[float, float]:
    return 25.0, 0.0


def make_history(
    period: ClimatePeriod,
    weather: Callable[[date], tuple[float, float]] = constant_weather,
) -> list[WeatherDay]:
    dates = [
        period.start_date + timedelta(days=offset)
        for offset in range((period.baseline_end - period.start_date).days + 1)
    ]
    return [WeatherDay(day, *weather(day)) for day in dates]


class FakeArchiveClient:
    def __init__(self) -> None:
        self.calls: list[tuple[float, float, date, date]] = []
        self.fail = False
        self.omit_last_day = False
        self.missing_value = False

    def fetch_archive(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> OpenMeteoArchive:
        self.calls.append((latitude, longitude, start_date, end_date))
        if self.fail:
            raise WeatherProviderError("Không lấy được dữ liệu lịch sử từ Open-Meteo")
        dates = [
            start_date + timedelta(days=offset)
            for offset in range(
                (end_date - start_date).days + 1 - int(self.omit_last_day)
            )
        ]
        rain: list[float | None] = [0.0] * len(dates)
        if self.missing_value:
            rain[len(rain) // 2] = None
        return OpenMeteoArchive.model_validate(
            {
                "daily": {
                    "time": dates,
                    "precipitation_sum": rain,
                    "temperature_2m_mean": [25.0] * len(dates),
                },
            }
        )
