from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from weather_analysis.advisory.models import WeatherDay
from weather_analysis.models import DailyWeather


class AdvisoryWeatherRepository:
    """Đọc lịch sử theo ngày mà không thay đổi dữ liệu."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def read_days(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> list[WeatherDay]:
        statement = (
            select(DailyWeather)
            .where(
                DailyWeather.latitude == latitude,
                DailyWeather.longitude == longitude,
                DailyWeather.date.between(start_date, end_date),
            )
            .order_by(DailyWeather.date)
        )
        return [
            WeatherDay(row.date, row.temperature_mean, row.precipitation_sum)
            for row in self._session.scalars(statement)
        ]
