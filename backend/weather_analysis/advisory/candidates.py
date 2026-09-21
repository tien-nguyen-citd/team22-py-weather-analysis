import calendar
from datetime import date
import re

from weather_analysis.advisory.activities import get_activity
from weather_analysis.advisory.models import (
    AdvisoryInputError,
    AdvisoryRequest,
    CandidateWindow,
    MonthRange,
    NormalizedRequest,
)


def parse_month(value: str) -> date:
    if re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", value) is None:
        raise AdvisoryInputError("Tháng phải có định dạng YYYY-MM hợp lệ")
    try:
        return date.fromisoformat(f"{value}-01")
    except ValueError as error:
        raise AdvisoryInputError("Tháng phải có định dạng YYYY-MM hợp lệ") from error


def add_months(value: date, offset: int) -> date:
    month_index = value.year * 12 + value.month - 1 + offset
    try:
        return date(month_index // 12, month_index % 12 + 1, 1)
    except ValueError as error:
        raise AdvisoryInputError(
            "Khoảng thời gian vượt giới hạn năm được hỗ trợ"
        ) from error


def format_month(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def normalize_request(request: AdvisoryRequest, today: date) -> NormalizedRequest:
    slug = request.location_slug.strip()
    if not slug:
        raise AdvisoryInputError("Cần chọn địa điểm để tư vấn")
    if type(request.top_k) is not int or not 1 <= request.top_k <= 3:
        raise AdvisoryInputError("Số lựa chọn phải là số nguyên từ 1 đến 3")
    profile = get_activity(request.activity_id)
    time = request.time
    if time is None:
        start = add_months(today, 1)
        time = MonthRange(format_month(start), format_month(add_months(start, 11)))
    start = parse_month(time.start_month)
    end = parse_month(time.end_month)
    month_count = (end.year - start.year) * 12 + end.month - start.month + 1
    if not 1 <= month_count <= 12:
        raise AdvisoryInputError("Khoảng tìm kiếm phải từ 1 đến 12 tháng liên tiếp")
    return NormalizedRequest(slug, time, profile.id, request.top_k)


def month_window(month: date) -> CandidateWindow:
    last_day = calendar.monthrange(month.year, month.month)[1]
    label = f"{month.month:02d}/{month.year:04d}"
    return CandidateWindow(month, month.replace(day=last_day), f"Tháng {label}", "month")


def generate_candidates(time: MonthRange) -> list[CandidateWindow]:
    start = parse_month(time.start_month)
    end = parse_month(time.end_month)
    month_count = (end.year - start.year) * 12 + end.month - start.month + 1
    if not 1 <= month_count <= 12:
        raise AdvisoryInputError("Khoảng tìm kiếm phải từ 1 đến 12 tháng liên tiếp")
    windows: list[CandidateWindow] = []
    for offset in range(month_count):
        month = add_months(start, offset)
        if month_count >= 3:
            windows.append(month_window(month))
        else:
            last_day = calendar.monthrange(month.year, month.month)[1]
            label = f"{month.month:02d}/{month.year:04d}"
            for first, last, name in (
                (1, 10, "Đầu"),
                (11, 20, "Giữa"),
                (21, last_day, "Cuối"),
            ):
                windows.append(
                    CandidateWindow(
                        month.replace(day=first),
                        month.replace(day=last),
                        f"{name} tháng {label}",
                        "period",
                    )
                )
    return windows
