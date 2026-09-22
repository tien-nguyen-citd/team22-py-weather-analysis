from dataclasses import replace
from datetime import date, timedelta
import math
from statistics import fmean

from weather_analysis.advisory.models import (
    ActivityProfile,
    Candidate,
    CandidateWindow,
    WeatherDay,
)
from weather_analysis.services.climate_service import ClimateDataError


TEMPERATURE_PENALTY_PER_DEGREE = 10.0
# Tỷ lệ ngày mưa lớn còn chấp nhận được (khoảng 3 ngày/tháng); vượt mức này thì trừ nhanh.
RAIN_TOLERANCE_PERCENT = 10.0
RAIN_PENALTY_PER_PERCENT = 2.5
SIMILAR_SCORE_GAP = 3.0
LOW_SUITABILITY_SCORE = 50.0
BASELINE_YEARS = 10


def temperature_score(temperature: float, minimum: float, maximum: float) -> float:
    distance = max(minimum - temperature, temperature - maximum, 0.0)
    return max(0.0, 100.0 - distance * TEMPERATURE_PENALTY_PER_DEGREE)


def rain_score(rainy_day_percentage: float) -> float:
    excess = max(rainy_day_percentage - RAIN_TOLERANCE_PERCENT, 0.0)
    return max(0.0, 100.0 - excess * RAIN_PENALTY_PER_PERCENT)


def group_history(
    days: list[WeatherDay],
    baseline_start: date,
    baseline_end: date,
) -> dict[tuple[int, int], list[WeatherDay]]:
    """Kiểm tra toàn bộ baseline, rồi gom theo năm/tháng và bỏ ngày 29/2."""
    expected_count = (baseline_end - baseline_start).days + 1
    dates = {day.date for day in days}
    if len(days) != len(dates):
        raise ClimateDataError("Dữ liệu lịch sử bị trùng ngày")
    if len(days) != expected_count or any(
        baseline_start + timedelta(days=offset) not in dates
        for offset in range(expected_count)
    ):
        raise ClimateDataError("Dữ liệu lịch sử chưa đủ ngày trong baseline")

    grouped: dict[tuple[int, int], list[WeatherDay]] = {}
    for day in days:
        if (
            not math.isfinite(day.temperature_mean)
            or not math.isfinite(day.precipitation_sum)
            or day.precipitation_sum < 0
        ):
            raise ClimateDataError("Dữ liệu lịch sử không hợp lệ")
        if day.date.month == 2 and day.date.day == 29:
            continue
        grouped.setdefault((day.date.year, day.date.month), []).append(day)
    return grouped


def score_candidates(
    windows: list[CandidateWindow],
    days: list[WeatherDay],
    baseline_start: date,
    baseline_end: date,
    activity: ActivityProfile,
) -> list[Candidate]:
    grouped = group_history(days, baseline_start, baseline_end)
    return [_score_candidate(window, grouped, activity) for window in windows]


def _score_candidate(
    window: CandidateWindow,
    grouped: dict[tuple[int, int], list[WeatherDay]],
    activity: ActivityProfile,
) -> Candidate:
    yearly_days = [
        [
            day
            for day in days
            if window.start_date.day <= day.date.day <= window.end_date.day
        ]
        for (_, month), days in sorted(grouped.items())
        if month == window.start_date.month
    ]
    if len(yearly_days) != BASELINE_YEARS or any(not days for days in yearly_days):
        raise ClimateDataError("Dữ liệu lịch sử chưa đủ 10 năm cho ứng viên")

    rainy_day_percentage = fmean(
        fmean(
            100.0 if day.precipitation_sum >= activity.rain_threshold_mm else 0.0
            for day in days
        )
        for days in yearly_days
    )
    dry_score = rain_score(rainy_day_percentage)
    minimum, maximum = activity.temperature_min, activity.temperature_max
    temp_score = (
        None
        if minimum is None or maximum is None
        else fmean(
            fmean(
                temperature_score(day.temperature_mean, minimum, maximum)
                for day in days
            )
            for days in yearly_days
        )
    )
    rain_contribution = activity.rain_weight * dry_score
    temperature_contribution = activity.temperature_weight * (temp_score or 0.0)
    candidate = Candidate(
        window=window,
        temperature_mean=fmean(
            fmean(day.temperature_mean for day in days) for days in yearly_days
        ),
        rainy_day_percentage=rainy_day_percentage,
        precipitation_mean=fmean(
            fmean(day.precipitation_sum for day in days) for days in yearly_days
        ),
        rain_score=dry_score,
        temperature_score=temp_score,
        rain_contribution=rain_contribution,
        temperature_contribution=temperature_contribution,
        score=rain_contribution + temperature_contribution,
        sample_years=len(yearly_days),
        sample_days=sum(len(days) for days in yearly_days),
        explanation="",
    )
    return replace(candidate, explanation=explain_candidate(candidate, activity))


def explain_candidate(candidate: Candidate, activity: ActivityProfile) -> str:
    description = (
        f"{candidate.window.label}: nhiệt độ trung bình ngày {candidate.temperature_mean:.1f}°C; "
        f"{candidate.rainy_day_percentage:.1f}% ngày có mưa từ {activity.rain_threshold_mm:g} mm; "
        f"lượng mưa trung bình {candidate.precipitation_mean:.1f} mm/ngày. "
        f"Tối đa {RAIN_TOLERANCE_PERCENT:g}% ngày mưa vẫn đạt trọn điểm ít mưa, "
        f"vượt thêm mỗi 1% trừ {RAIN_PENALTY_PER_PERCENT:g} điểm. "
        f"Điểm ít mưa {candidate.rain_score:.1f} × {activity.rain_weight:.0%} "
        f"= {candidate.rain_contribution:.1f} điểm"
    )
    if candidate.temperature_score is not None:
        description += (
            f"; điểm nhiệt độ {candidate.temperature_score:.1f} × {activity.temperature_weight:.0%} "
            f"= {candidate.temperature_contribution:.1f} điểm"
        )
    else:
        description += "; không chấm nhiệt độ cho hoạt động này"
    return (
        description
        + f". Tổng {candidate.score:.1f}/100 điểm từ {candidate.sample_years} năm lịch sử."
    )


def ranking_key(candidate: Candidate) -> tuple[float, float, date]:
    return (-candidate.score, candidate.rainy_day_percentage, candidate.window.start_date)


def rank_candidates(candidates: list[Candidate]) -> list[Candidate]:
    ranked = sorted(candidates, key=ranking_key)
    if not ranked:
        return []
    best_score = ranked[0].score
    return [
        replace(
            candidate,
            rank=index + 1,
            similar_to_best=index > 0
            and best_score - candidate.score < SIMILAR_SCORE_GAP,
        )
        for index, candidate in enumerate(ranked)
    ]
