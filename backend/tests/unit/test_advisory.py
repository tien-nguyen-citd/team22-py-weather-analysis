from dataclasses import replace
from datetime import date, timedelta

import pytest

from tests.advisory_helpers import make_history
from weather_analysis.advisory.activities import ACTIVITY_PROFILES, get_activity
from weather_analysis.advisory.candidates import generate_candidates, normalize_request
from weather_analysis.advisory.models import (
    AdvisoryInputError,
    AdvisoryRequest,
    MonthRange,
)
from weather_analysis.advisory.scoring import (
    rain_score,
    rank_candidates,
    score_candidates,
    temperature_score,
)
from weather_analysis.advisory.service import build_advice
from weather_analysis.services.climate_service import (
    ClimateDataError,
    calculate_climate_period,
)


TODAY = date(2026, 9, 20)
PERIOD = calculate_climate_period(TODAY)


def test_default_request_and_activity_profiles() -> None:
    result = normalize_request(AdvisoryRequest(" ha-noi "), TODAY)
    assert result.location_slug == "ha-noi"
    assert result.time == MonthRange("2026-10", "2027-09")
    assert result.activity_id == "general"
    assert result.top_k == 3
    december = normalize_request(AdvisoryRequest("ha-noi"), date(2026, 12, 31))
    assert december.time == MonthRange("2027-01", "2027-12")
    assert len(ACTIVITY_PROFILES) == 9
    assert len({profile.id for profile in ACTIVITY_PROFILES}) == 9
    assert all(
        profile.rain_weight + profile.temperature_weight == 1
        for profile in ACTIVITY_PROFILES
    )


@pytest.mark.parametrize(
    "advisory_request",
    [
        AdvisoryRequest(" "),
        AdvisoryRequest("ha-noi", activity_id="unknown"),
        AdvisoryRequest("ha-noi", activity_id=""),
        AdvisoryRequest("ha-noi", top_k=0),
        AdvisoryRequest("ha-noi", top_k=4),
        AdvisoryRequest("ha-noi", top_k=True),
        AdvisoryRequest("ha-noi", MonthRange("2026-9", "2026-10")),
        AdvisoryRequest("ha-noi", MonthRange("2026-00", "2026-10")),
        AdvisoryRequest("ha-noi", MonthRange("0000-01", "0000-02")),
        AdvisoryRequest("ha-noi", MonthRange("2026-12", "2026-11")),
        AdvisoryRequest("ha-noi", MonthRange("2026-01", "2027-01")),
    ],
)
def test_invalid_request(advisory_request: AdvisoryRequest) -> None:
    with pytest.raises(AdvisoryInputError):
        normalize_request(advisory_request, TODAY)


def test_candidate_resolution_boundaries_and_cross_year() -> None:
    monthly = generate_candidates(MonthRange("2026-12", "2027-02"))
    assert len(monthly) == 3
    assert all(window.resolution == "month" for window in monthly)
    assert monthly[-1].end_date == date(2027, 2, 28)
    periods = generate_candidates(MonthRange("2027-12", "2028-01"))
    assert len(periods) == 6
    assert all(window.resolution == "period" for window in periods)
    assert all(
        left.end_date + timedelta(days=1) == right.start_date
        for left, right in zip(periods, periods[1:])
    )
    assert generate_candidates(MonthRange("2028-02", "2028-02"))[-1].end_date == date(
        2028, 2, 29
    )
    assert len(generate_candidates(MonthRange("2027-01", "2027-12"))) == 12


@pytest.mark.parametrize(
    ("temperature", "expected"),
    [(10, 0), (15, 50), (20, 100), (24, 100), (28, 100), (33, 50), (38, 0), (45, 0)],
)
def test_temperature_score(temperature: float, expected: float) -> None:
    assert temperature_score(temperature, 20, 28) == expected


@pytest.mark.parametrize(
    ("rainy_day_percentage", "expected"),
    [(0, 100), (5, 100), (10, 100), (20, 75), (30, 50), (50, 0), (80, 0)],
)
def test_rain_score(rainy_day_percentage: float, expected: float) -> None:
    assert rain_score(rainy_day_percentage) == expected


def test_hand_calculation_and_rain_threshold() -> None:
    # Mỗi giai đoạn 10 ngày: 7 ngày dưới 10 mm và 3 ngày đúng 10 mm.
    days = make_history(PERIOD, lambda day: (26.0, 9.8 if day.day <= 7 else 10.0))
    request = normalize_request(
        AdvisoryRequest("ha-noi", MonthRange("2027-01", "2027-01"), "wedding"), TODAY
    )
    result = build_advice(request, days, PERIOD)
    candidate = result.candidates[0]
    assert candidate.rain_score == 50
    assert candidate.rainy_day_percentage == pytest.approx(30)
    assert candidate.temperature_score == 100
    assert candidate.rain_contribution == 40
    assert candidate.temperature_contribution == 20
    assert candidate.score == 60
    assert candidate.precipitation_mean == pytest.approx(9.86)
    assert candidate.sample_years == 10
    assert candidate.sample_days == 100
    assert "50.0 × 80% = 40.0" in candidate.explanation
    assert "100.0 × 20% = 20.0" in candidate.explanation
    assert "Tổng 60.0/100" in candidate.explanation


def test_activity_changes_winner_and_candidate_set_does_not_change_score() -> None:
    def weather(day: date) -> tuple[float, float]:
        if day.month == 1:
            return 22.0, 0.0 if day.day <= 24 else 20.0
        if day.month == 2:
            return 38.0, 0.0
        return 40.0, 20.0

    days = make_history(PERIOD, weather)
    request = normalize_request(
        AdvisoryRequest("ha-noi", MonthRange("2027-01", "2027-03"), "wedding"), TODAY
    )
    wedding = build_advice(request, days, PERIOD)
    general = build_advice(replace(request, activity_id="general"), days, PERIOD)
    assert wedding.recommendations[0].window.start_date.month == 2
    assert general.recommendations[0].window.start_date.month == 1
    extended = build_advice(
        replace(request, time=MonthRange("2027-01", "2027-04")), days, PERIOD
    )
    assert [item.score for item in wedding.candidates] == [
        item.score for item in extended.candidates[:3]
    ]


def test_leap_day_is_excluded_and_years_are_equally_weighted() -> None:
    def weather(day: date) -> tuple[float, float]:
        if (day.month, day.day) == (2, 29):
            return -50.0, 1000.0
        return (20.0, 0.0) if day.year % 2 == 0 else (30.0, 20.0)

    request = normalize_request(
        AdvisoryRequest("ha-noi", MonthRange("2028-02", "2028-02")), TODAY
    )
    result = build_advice(request, make_history(PERIOD, weather), PERIOD)
    last = result.candidates[-1]
    assert last.sample_days == 80
    assert last.temperature_mean == 25
    assert last.precipitation_mean == 10
    assert last.rain_score == 0
    assert last.temperature_score == 90
    assert last.score == 36


def test_ranking_ties_near_scores_and_unrounded_scores() -> None:
    windows = generate_candidates(MonthRange("2027-01", "2027-03"))
    candidates = score_candidates(
        windows,
        make_history(PERIOD),
        PERIOD.start_date,
        PERIOD.baseline_end,
        get_activity("travel"),
    )
    first, second, third = candidates
    ranked = rank_candidates([third, second, first])
    assert [item.window for item in ranked] == windows
    assert ranked[0].similar_to_best is False
    assert ranked[1].similar_to_best is True
    ranked = rank_candidates(
        [
            replace(first, score=80, rainy_day_percentage=10),
            replace(second, score=80, rainy_day_percentage=5),
            replace(third, score=77),
        ]
    )
    assert ranked[0].window == second.window
    assert ranked[-1].similar_to_best is False
    ranked = rank_candidates(
        [replace(first, score=80.001), replace(second, score=80.002)]
    )
    assert ranked[0].window == second.window
    assert ranked[1].similar_to_best is True
    assert rank_candidates([]) == []


def test_low_suitability_and_top_k() -> None:
    request = normalize_request(
        AdvisoryRequest("ha-noi", MonthRange("2027-01", "2027-03"), "wedding", 1), TODAY
    )
    days = make_history(PERIOD, lambda _: (45.0, 10.0))
    result = build_advice(request, days, PERIOD)
    assert result.low_suitability is True
    assert len(result.recommendations) == 1
    assert len(result.candidates) == 3
    assert "ít phù hợp" in result.summary
    multiple = build_advice(replace(request, top_k=3), days, PERIOD)
    assert len(multiple.recommendations) == 3
    assert "gần tương đương" in multiple.summary
    assert any("không phải dự báo" in note for note in result.notes)


@pytest.mark.parametrize(
    "problem",
    ["missing", "duplicate", "wrong_date", "negative_rain", "nan", "infinity"],
)
def test_invalid_history_is_rejected(problem: str) -> None:
    days = make_history(PERIOD)
    if problem == "missing":
        days.pop(100)
    elif problem == "duplicate":
        days[100] = days[101]
    elif problem == "wrong_date":
        days[100] = replace(days[100], date=PERIOD.start_date - timedelta(days=1))
    elif problem == "negative_rain":
        days[100] = replace(days[100], precipitation_sum=-1)
    elif problem == "nan":
        days[100] = replace(days[100], temperature_mean=float("nan"))
    else:
        days[100] = replace(days[100], precipitation_sum=float("inf"))
    with pytest.raises(ClimateDataError):
        score_candidates(
            generate_candidates(MonthRange("2027-01", "2027-03")),
            days,
            PERIOD.start_date,
            PERIOD.baseline_end,
            get_activity("travel"),
        )


def test_cannot_reduce_baseline_to_nine_years() -> None:
    start = date(2016, 9, 1)
    days = [day for day in make_history(PERIOD) if day.date >= start]
    with pytest.raises(ClimateDataError, match="10 năm"):
        score_candidates(
            generate_candidates(MonthRange("2027-01", "2027-03")),
            days,
            start,
            PERIOD.baseline_end,
            get_activity("travel"),
        )
