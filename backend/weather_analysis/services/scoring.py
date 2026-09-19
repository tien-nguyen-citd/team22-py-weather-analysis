import math
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class HourData:
    hour: int
    temp: float
    rain_prob: int
    uv: float
    humidity: int = 60
    wind: int = 10
    score: int | None = None


@dataclass(frozen=True)
class Run:
    range: str
    score: int
    start: int
    len: int


@dataclass(frozen=True)
class BestWindow:
    range: str
    score: int
    start: int
    len: int
    tag: str
    note: str


@dataclass(frozen=True)
class Factor:
    label: str
    value: int
    note: str


@dataclass(frozen=True)
class ActivityWindow:
    id: str
    name: str
    score: int
    range: str
    note: str
    has_window: bool


@dataclass(frozen=True)
class _Candidate:
    start: int
    len: int
    average: float


def js_round(value: float) -> int:
    """Làm tròn giống Math.round của JavaScript."""
    return math.floor(value + 0.5)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def calculate_tourism_score(temperature: float, rainy_days: int) -> int:
    """Tính mức phù hợp để du lịch theo khí hậu trung bình tháng."""
    if temperature < 20:
        temperature_penalty = (20 - temperature) * 2.5
    elif temperature > 28:
        temperature_penalty = (temperature - 28) * 3.6
    else:
        temperature_penalty = 0
    score = 100 - temperature_penalty - rainy_days * 2.2
    return js_round(clamp(score, 8, 98))


def pad(hour: int) -> str:
    return f"{hour:02d}:00"


def calculate_hourly_score(temp: float, rain: int, uv: float, hour: int) -> int:
    night = hour < 6 or hour >= 18
    score = (
        100
        - abs(temp - 25) * 3.2
        - rain * 0.72
        - max(0, uv - 5) * 4.5
    )
    if night:
        score = min(score, 34) - (18 if hour < 5 or hour >= 20 else 6)
    return js_round(clamp(score, 3, 99))


def calculate_day_score(hours: list[HourData]) -> int:
    day_hours = [hour for hour in hours if 6 <= hour.hour <= 17]
    if not day_hours:
        return 50
    return js_round(
        sum(hour.score or 0 for hour in day_hours) / len(day_hours)
    )


def best_runs(
    hours: list[HourData],
    score_of: Callable[[HourData], int],
    minimum: int,
) -> list[Run]:
    scores = [score_of(hour) for hour in hours]
    candidates: list[_Candidate] = []
    for length in range(3, 1, -1):
        for start in range(6, 20 - length):
            segment = scores[start : start + length]
            if any(score < minimum for score in segment):
                continue
            candidates.append(
                _Candidate(start, length, sum(segment) / length)
            )

    candidates.sort(key=lambda candidate: candidate.average, reverse=True)
    picked: list[_Candidate] = []
    for candidate in candidates:
        overlaps = any(
            candidate.start < existing.start + existing.len
            and existing.start < candidate.start + candidate.len
            for existing in picked
        )
        if overlaps:
            continue
        picked.append(candidate)
        if len(picked) == 2:
            break

    return [
        Run(
            range=f"{pad(candidate.start)} – {pad(candidate.start + candidate.len)}",
            score=js_round(candidate.average),
            start=candidate.start,
            len=candidate.len,
        )
        for candidate in sorted(picked, key=lambda candidate: candidate.start)
    ]


def get_tag_for_start_hour(start_hour: int) -> str:
    if start_hour < 9:
        return "Sáng sớm"
    if start_hour < 11:
        return "Buổi sáng"
    if start_hour < 14:
        return "Giữa ngày"
    if start_hour < 16:
        return "Đầu giờ chiều"
    return "Chiều muộn"


def get_quality_note(score: int) -> str:
    if score >= 75:
        return "rất dễ chịu"
    if score >= 60:
        return "chấp nhận được"
    return "tạm ổn"


def get_best_windows(hours: list[HourData]) -> list[BestWindow]:
    runs = best_runs(
        hours,
        lambda hour: hour.score
        if hour.score is not None
        else calculate_hourly_score(
            hour.temp, hour.rain_prob, hour.uv, hour.hour
        ),
        55,
    )
    if not runs:
        if len(hours) > 6:
            fallback_score = hours[6].score
            if fallback_score is None:
                fallback_score = calculate_hourly_score(
                    hours[6].temp,
                    hours[6].rain_prob,
                    hours[6].uv,
                    6,
                )
        else:
            fallback_score = 50
        return [
            BestWindow(
                range=f"{pad(6)} – {pad(8)}",
                score=fallback_score,
                start=6,
                len=2,
                tag="Sáng sớm",
                note=get_quality_note(fallback_score),
            )
        ]
    return [
        BestWindow(
            range=run.range,
            score=run.score,
            start=run.start,
            len=run.len,
            tag=get_tag_for_start_hour(run.start),
            note=get_quality_note(run.score),
        )
        for run in runs
    ]


def calculate_factors(
    temp_now: float,
    uv_now: float,
    peak_rain: int,
    humidity: int,
    wind: int,
) -> list[Factor]:
    return [
        Factor(
            "Nhiệt độ",
            js_round(clamp(100 - abs(temp_now - 25) * 8, 5, 100)),
            f"{js_round(temp_now)}°C lúc này",
        ),
        Factor(
            "Mưa",
            js_round(clamp(100 - peak_rain, 5, 100)),
            f"cao nhất {peak_rain}%",
        ),
        Factor(
            "Tia UV",
            js_round(clamp(100 - max(0, uv_now - 3) * 14, 5, 100)),
            f"UV {uv_now:g}",
        ),
        Factor(
            "Gió & ẩm",
            js_round(
                clamp(118 - humidity - max(0, wind - 14) * 3, 5, 100)
            ),
            f"{humidity}% ẩm",
        ),
    ]


def score_running(hour: HourData) -> int:
    score = (
        100
        - abs(hour.temp - 23) * 4
        - hour.rain_prob * 0.9
        - max(0, hour.uv - 3) * 5.5
        - (34 if hour.hour < 5 or hour.hour > 20 else 0)
    )
    return int(clamp(js_round(score), 0, 99))


def score_photography(hour: HourData) -> int:
    score = (
        100
        - hour.rain_prob * 1.1
        - min(abs(hour.hour - 7), abs(hour.hour - 17)) * 9
        - (40 if hour.hour < 5 or hour.hour > 19 else 0)
    )
    return int(clamp(js_round(score), 0, 99))


def score_coffee(hour: HourData) -> int:
    score = (
        100
        - abs(hour.temp - 26) * 3
        - hour.rain_prob * 1.2
        - (26 if hour.hour < 7 or hour.hour > 21 else 0)
    )
    return int(clamp(js_round(score), 0, 99))


def score_drying(hour: HourData) -> int:
    score = (
        100
        - hour.rain_prob * 1.7
        - max(0, 28 - hour.temp) * 2.2
        + min(hour.uv, 6) * 2
        - (45 if hour.hour < 7 or hour.hour > 16 else 0)
    )
    return int(clamp(js_round(score), 0, 99))


def calculate_activity_windows(hours: list[HourData]) -> list[ActivityWindow]:
    configs: list[tuple[str, str, str, Callable[[HourData], int]]] = [
        ("running", "Chạy bộ", "Cần mát, khô, ít tia UV", score_running),
        (
            "photography",
            "Chụp ảnh ngoài trời",
            "Ánh sáng đẹp nhất quanh giờ vàng",
            score_photography,
        ),
        (
            "coffee",
            "Cà phê ngoài trời",
            "Dễ chịu khi trời khô, không quá nóng",
            score_coffee,
        ),
        (
            "drying",
            "Phơi quần áo",
            "Cần nắng liên tục và độ ẩm thấp",
            score_drying,
        ),
    ]
    activities: list[ActivityWindow] = []
    for activity_id, name, note, scorer in configs:
        runs = best_runs(hours, scorer, 45)
        if not runs:
            activities.append(
                ActivityWindow(
                    activity_id,
                    name,
                    4,
                    "Không có khung giờ phù hợp",
                    note,
                    False,
                )
            )
            continue
        top_run = max(runs, key=lambda run: run.score)
        activities.append(
            ActivityWindow(
                activity_id,
                name,
                top_run.score,
                top_run.range,
                note,
                True,
            )
        )
    return activities


def get_day_verdict(day_score: int) -> str:
    if day_score >= 72:
        return "Một ngày dễ chịu, gần như giờ nào ra ngoài cũng được."
    if day_score >= 58:
        return "Ra ngoài thoải mái vào buổi sáng, chiều nên linh hoạt."
    if day_score >= 45:
        return "Thời tiết thất thường, nên chọn giờ và mang theo áo mưa."
    return "Hôm nay khó chịu, chỉ nên ra ngoài trong khung giờ hẹp."


def get_uv_label(uv: float) -> str:
    if uv >= 8:
        return "rất cao"
    if uv >= 6:
        return "cao"
    if uv >= 3:
        return "trung bình"
    return "thấp"


def get_day_why(
    condition: str,
    humidity: int,
    wind: int,
    hours: list[HourData],
    uv_now: float,
) -> str:
    first_part = f"{condition}. Độ ẩm {humidity}%, gió {wind} km/h. "
    wet_hours = [hour for hour in hours if hour.rain_prob >= 45]
    if wet_hours:
        peak = max(hours, key=lambda hour: hour.rain_prob)
        second_part = (
            f"Khả năng mưa cao nhất khoảng {pad(peak.hour)} "
            f"({peak.rain_prob}%), kéo dài chừng {len(wet_hours)} giờ. "
        )
    else:
        second_part = "Cả ngày hầu như không mưa. "

    hot_uv_hours = [hour for hour in hours if hour.uv >= 8]
    if hot_uv_hours:
        third_part = (
            f"Tia UV ở mức có hại từ {pad(hot_uv_hours[0].hour)} đến "
            f"{pad(hot_uv_hours[-1].hour + 1)}, nên che chắn khi ra ngoài."
        )
    else:
        third_part = (
            f"Tia UV cả ngày ở mức {get_uv_label(uv_now)}, không cần lo nhiều."
        )
    return first_part + second_part + third_part


def get_rain_window(hours: list[HourData]) -> str:
    wet_hours = [hour for hour in hours if hour.rain_prob >= 45]
    if not wet_hours:
        return "không mưa"
    return f"{pad(wet_hours[0].hour)} – {pad(wet_hours[-1].hour + 1)}"


def get_weather_condition(rain_prob: int, uv: float, rain_sum: float) -> str:
    if rain_sum > 10 or rain_prob > 75:
        return "Mưa rào nhiều đợt, trời âm u"
    if rain_prob >= 45:
        return "Nắng gián đoạn, chiều có mưa rào"
    if uv >= 8:
        return "Nắng gắt, ít mây, trời khô nóng"
    if uv >= 5:
        return "Nắng đẹp, mây rải rác"
    return "Trời mát mẻ, nhiều mây"


def get_aqi_label(aqi: int) -> str:
    if aqi <= 50:
        return "Tốt"
    if aqi <= 100:
        return "Trung bình"
    return "Kém"
