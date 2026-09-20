from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class TimeKind(StrEnum):
    NOW = "now"  # lúc này, bây giờ → thời tiết hiện tại
    DATES = "dates"  # hôm nay, cuối tuần, tuần sau → dự báo theo ngày
    MONTHS = "months"  # tháng 12, tháng sau, mùa này → khí hậu theo tháng
    BEST_TIME = "best_time"  # tháng mấy, khi nào → tìm thời điểm phù hợp nhất


@dataclass(frozen=True)
class TimeSlot:
    """Khoảng thời gian người dùng hỏi.

    Với BEST_TIME, start và end là khoảng cần tìm thời điểm phù hợp nhất;
    để trống nghĩa là không giới hạn.
    """

    kind: TimeKind
    start: date | None = None
    end: date | None = None


@dataclass(frozen=True)
class QuestionInfo:
    """Ba thông tin cần để phân tích thời tiết cho một câu hỏi."""

    location_slug: str | None  # slug trong locations.csv
    time: TimeSlot | None
    activity_id: str | None  # id trong activities.csv
