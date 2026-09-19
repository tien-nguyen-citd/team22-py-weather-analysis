from dataclasses import dataclass
from datetime import date

from sqlalchemy import case, extract, func, select
from sqlalchemy.orm import Session

from weather_analysis.models import DailyWeather


@dataclass(frozen=True)
class MonthlyWeatherAggregate:
    year: int
    month: int
    temperature_mean: float
    precipitation_sum: float
    rainy_days: int
    day_count: int


class DailyWeatherRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_date_bounds(
        self, latitude: float, longitude: float
    ) -> tuple[date | None, date | None]:
        statement = select(
            func.min(DailyWeather.date),
            func.max(DailyWeather.date),
        ).where(
            DailyWeather.latitude == latitude,
            DailyWeather.longitude == longitude,
        )
        minimum, maximum = self._session.execute(statement).one()
        return minimum, maximum

    def add_many(self, rows: list[DailyWeather]) -> None:
        self._session.add_all(rows)
        self._session.flush()

    def count_days(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(DailyWeather)
            .where(
                DailyWeather.latitude == latitude,
                DailyWeather.longitude == longitude,
                DailyWeather.date.between(start_date, end_date),
            )
        )
        return self._session.scalar(statement) or 0

    def aggregate_months(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> list[MonthlyWeatherAggregate]:
        year = extract("year", DailyWeather.date)
        month = extract("month", DailyWeather.date)
        statement = (
            select(
                year,
                month,
                func.avg(DailyWeather.temperature_mean),
                func.sum(DailyWeather.precipitation_sum),
                func.sum(case((DailyWeather.precipitation_sum >= 1, 1), else_=0)),
                func.count(),
            )
            .where(
                DailyWeather.latitude == latitude,
                DailyWeather.longitude == longitude,
                DailyWeather.date.between(start_date, end_date),
            )
            .group_by(year, month)
            .order_by(year, month)
        )
        return [
            MonthlyWeatherAggregate(
                year=int(row[0]),
                month=int(row[1]),
                temperature_mean=float(row[2]),
                precipitation_sum=float(row[3]),
                rainy_days=int(row[4]),
                day_count=int(row[5]),
            )
            for row in self._session.execute(statement)
        ]
