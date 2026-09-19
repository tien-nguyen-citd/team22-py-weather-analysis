from datetime import date

from sqlalchemy.orm import Session

from weather_analysis.models import DailyWeather
from weather_analysis.repositories.daily_weather_repository import (
    DailyWeatherRepository,
)


def test_aggregate_months_counts_rainy_days_from_one_millimeter(
    session: Session,
) -> None:
    repository = DailyWeatherRepository(session)
    repository.add_many(
        [
            DailyWeather(
                latitude=10,
                longitude=106,
                date=date(2026, 1, day),
                temperature_mean=20 + day,
                precipitation_sum=rain,
            )
            for day, rain in [(1, 0), (2, 0.9), (3, 1), (4, 2)]
        ]
    )

    result = repository.aggregate_months(10, 106, date(2026, 1, 1), date(2026, 1, 31))

    assert repository.count_days(10, 106, date(2026, 1, 1), date(2026, 1, 31)) == 4
    assert len(result) == 1
    assert result[0].temperature_mean == 22.5
    assert result[0].precipitation_sum == 3.9
    assert result[0].rainy_days == 2
    assert result[0].day_count == 4
