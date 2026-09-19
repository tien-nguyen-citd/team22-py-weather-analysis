from weather_analysis.models import Location
from weather_analysis.services.climate_service import (
    LocationClimate,
    MonthClimate,
    RecentMonthClimate,
)
from weather_analysis.services.history_service import build_location_history


def make_location() -> Location:
    return Location(
        name="Hà Nội",
        slug="ha-noi",
        region_code="dbbb",
        region_label="Đồng bằng Bắc Bộ",
        temp_offset=0,
        latitude=21,
        longitude=105,
        pin_order=1,
    )


def make_climate(recent_rain: int, baseline_rain: int) -> LocationClimate:
    return LocationClimate(
        recent_period="01/2025–12/2025",
        baseline_period="01/2015–12/2024",
        months=[
            MonthClimate(month, 25, baseline_rain, 5, 80) for month in range(1, 13)
        ],
        recent_months=[
            RecentMonthClimate(2025, month, 20 + month, recent_rain, month)
            for month in range(1, 13)
        ],
    )


def test_history_builds_insights_and_higher_rain_text() -> None:
    result = build_location_history(make_location(), make_climate(20, 10))

    assert result.rain_diff_percent == 100
    assert result.rain_comparison == "cao hơn 100%"
    assert result.wettest_month.label == "01/2025"
    assert result.hottest_month.label == "12/2025"
    assert result.coolest_month.label == "01/2025"


def test_history_describes_lower_and_equal_rain() -> None:
    lower = build_location_history(make_location(), make_climate(5, 10))
    equal = build_location_history(make_location(), make_climate(10, 10))

    assert lower.rain_comparison == "thấp hơn 50%"
    assert equal.rain_comparison == "xấp xỉ mức trung bình"
