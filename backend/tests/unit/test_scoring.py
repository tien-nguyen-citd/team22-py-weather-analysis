from weather_analysis.services.scoring import (
    HourData,
    best_runs,
    calculate_activity_windows,
    calculate_day_score,
    calculate_factors,
    calculate_hourly_score,
    calculate_tourism_score,
    get_best_windows,
    get_day_verdict,
    get_day_why,
    get_rain_window,
    js_round,
    score_running,
)


def make_hour(
    hour: int,
    *,
    temp: float = 25,
    rain_prob: int = 0,
    uv: float = 2,
    score: int | None = None,
) -> HourData:
    return HourData(
        hour=hour,
        temp=temp,
        rain_prob=rain_prob,
        uv=uv,
        score=score,
    )


def test_calculate_hourly_score_for_daytime_and_nighttime() -> None:
    assert calculate_hourly_score(25, 0, 2, 10) == 99
    assert calculate_hourly_score(30, 10, 7, 14) == 68
    assert calculate_hourly_score(25, 0, 0, 22) == 16
    assert calculate_hourly_score(25, 0, 0, 18) == 28


def test_calculate_day_score_only_uses_hours_from_6_to_17() -> None:
    hours = [
        make_hour(hour, score=80 if 6 <= hour <= 17 else 10)
        for hour in range(24)
    ]

    assert calculate_day_score(hours) == 80


def test_best_runs_finds_two_non_overlapping_windows() -> None:
    hours: list[HourData] = []
    for hour in range(24):
        score = 50
        if 7 <= hour <= 9:
            score = 85
        if 15 <= hour <= 17:
            score = 90
        hours.append(make_hour(hour, score=score))

    runs = best_runs(hours, lambda hour: hour.score or 0, 55)

    assert [run.range for run in runs] == [
        "07:00 – 10:00",
        "15:00 – 18:00",
    ]


def test_best_windows_ignore_hours_before_requested_hour() -> None:
    hours = [make_hour(hour, score=90) for hour in range(24)]

    windows = get_best_windows(hours, 14)

    assert windows
    assert all(window.start >= 14 for window in windows)


def test_best_windows_are_empty_when_no_window_reaches_threshold() -> None:
    hours = [make_hour(hour, score=30) for hour in range(24)]

    assert get_best_windows(hours, 6) == []


def test_calculate_factors_matches_existing_labels_and_notes() -> None:
    factors = calculate_factors(28, 6.4, 70, 74, 15)

    assert len(factors) == 4
    assert [(factor.label, factor.note) for factor in factors] == [
        ("Nhiệt độ", "28°C lúc này"),
        ("Mưa", "cao nhất 70%"),
        ("Tia UV", "UV 6.4"),
        ("Gió & ẩm", "74% ẩm"),
    ]


def test_activity_scorers_match_existing_expectations() -> None:
    assert score_running(make_hour(7, temp=24, uv=1)) > 80


def test_activity_uses_highest_scoring_window_not_earliest_window() -> None:
    hours = [make_hour(hour, rain_prob=100) for hour in range(24)]
    for hour in range(7, 10):
        hours[hour] = make_hour(hour, temp=27, uv=2)
    for hour in range(15, 18):
        hours[hour] = make_hour(hour, temp=23, uv=2)

    running = next(
        activity
        for activity in calculate_activity_windows(hours)
        if activity.id == "running"
    )

    assert running.range == "15:00 – 18:00"
    assert running.score == 99


def test_activity_has_no_window_when_no_time_remains() -> None:
    hours = [make_hour(hour) for hour in range(24)]

    activities = calculate_activity_windows(hours, 18)

    assert all(not activity.has_window for activity in activities)
    assert all(
        activity.range == "Hôm nay không còn khung giờ phù hợp"
        for activity in activities
    )


def test_dynamic_weather_text_matches_existing_behavior() -> None:
    hours = [
        make_hour(14, temp=28, rain_prob=60, uv=9),
        make_hour(15, temp=27, rain_prob=70, uv=8),
        make_hour(16, temp=26, rain_prob=50, uv=6),
    ]

    assert get_day_verdict(80) == (
        "Một ngày dễ chịu, gần như giờ nào ra ngoài cũng được."
    )
    assert get_day_verdict(30) == (
        "Hôm nay khó chịu, chỉ nên ra ngoài trong khung giờ hẹp."
    )
    assert get_rain_window(hours) == "14:00 – 17:00"
    why = get_day_why("Nhiều mây", 75, 12, hours, 5)
    assert "Nhiều mây. Độ ẩm 75%, gió 12 km/h." in why
    assert "Khả năng mưa cao nhất khoảng 15:00 (70%)" in why
    assert "Tia UV ở mức có hại" in why


def test_rain_window_separates_non_consecutive_periods() -> None:
    hours = [
        make_hour(5, rain_prob=60),
        make_hour(6, rain_prob=50),
        make_hour(7, rain_prob=10),
        make_hour(14, rain_prob=45),
        make_hour(15, rain_prob=70),
        make_hour(16, rain_prob=50),
    ]

    assert get_rain_window(hours) == "05:00 – 07:00, 14:00 – 17:00"


def test_js_round_rounds_half_toward_positive_infinity() -> None:
    assert js_round(2.5) == 3
    assert js_round(-1.5) == -1


def test_calculate_tourism_score_matches_existing_rules() -> None:
    assert calculate_tourism_score(25, 5) == 89
    assert calculate_tourism_score(17, 6) == 79
