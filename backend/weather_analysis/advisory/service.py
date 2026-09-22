from datetime import date

from sqlalchemy.orm import Session

from weather_analysis.advisory.activities import get_activity
from weather_analysis.advisory.candidates import generate_candidates, normalize_request
from weather_analysis.advisory.models import (
    Advice,
    AdvisoryRequest,
    NormalizedRequest,
    WeatherDay,
)
from weather_analysis.advisory.repository import AdvisoryWeatherRepository
from weather_analysis.advisory.scoring import (
    LOW_SUITABILITY_SCORE,
    rank_candidates,
    score_candidates,
)
from weather_analysis.services.climate_service import (
    ClimateClient,
    ClimatePeriod,
    calculate_climate_period,
    get_location_climate,
)
from weather_analysis.services.location_service import get_location_by_slug


ADVICE_NOTES = [
    "Tham khảo từ lịch sử khí hậu, không phải dự báo cho ngày cụ thể.",
    "Điểm phù hợp không phải xác suất thời tiết trong tương lai.",
    "Ngày mưa là ngày có tổng lượng mưa từ 10 mm, theo chỉ số R10mm (ngày mưa lớn) "
    "do ETCCDI, nhóm chuyên gia về chỉ số biến đổi khí hậu của WMO, định nghĩa. "
    "Tổng theo ngày không cho biết mưa rơi vào giờ nào.",
    "Trọng số và khoảng nhiệt độ là quy ước sản phẩm, không phải chuẩn khí tượng.",
    "Chỉ xét lượng mưa và nhiệt độ trung bình ngày; chưa xét gió, nắng, sóng biển hoặc độ ẩm.",
    "Không dùng ngày 29/2 khi tính các chỉ số so sánh giữa các năm.",
]


def get_advice(
    session: Session,
    request: AdvisoryRequest,
    client: ClimateClient,
    today: date,
) -> Advice:
    normalized = normalize_request(request, today)
    location = get_location_by_slug(session, normalized.location_slug)
    period = calculate_climate_period(today)
    # Luồng khí hậu hiện có chịu trách nhiệm nạp và kiểm tra lịch sử.
    get_location_climate(session, location, client, today)
    days = AdvisoryWeatherRepository(session).read_days(
        location.latitude,
        location.longitude,
        period.start_date,
        period.baseline_end,
    )
    return build_advice(normalized, days, period)


def build_advice(
    request: NormalizedRequest,
    days: list[WeatherDay],
    period: ClimatePeriod,
) -> Advice:
    activity = get_activity(request.activity_id)
    windows = generate_candidates(request.time)
    ranked = rank_candidates(
        score_candidates(
            windows,
            days,
            period.start_date,
            period.baseline_end,
            activity,
        )
    )
    recommendations = ranked[: request.top_k]
    best = recommendations[0]
    low_suitability = best.score < LOW_SUITABILITY_SCORE
    if low_suitability:
        summary = (
            "Khoảng này ít phù hợp với tiêu chí đã chọn. "
            f"{best.window.label} đứng đầu trong phạm vi tìm kiếm với {best.score:.1f}/100 điểm."
        )
    else:
        summary = (
            f"Ưu tiên {best.window.label.lower()} cho {activity.name.lower()}: "
            f"{best.score:.1f}/100 điểm theo lịch sử khí hậu."
        )
    similar = [item.window.label for item in recommendations if item.similar_to_best]
    if similar:
        summary += (
            f" Các lựa chọn có mức phù hợp gần tương đương: {', '.join(similar)}."
        )
    return Advice(
        request=request,
        baseline_start=period.start_date,
        baseline_end=period.baseline_end,
        activity=activity,
        recommendations=recommendations,
        candidates=sorted(ranked, key=lambda item: item.window.start_date),
        summary=summary,
        low_suitability=low_suitability,
        notes=ADVICE_NOTES,
    )
