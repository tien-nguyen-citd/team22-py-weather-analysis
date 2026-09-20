import calendar
import re
from collections.abc import Callable
from datetime import date, timedelta

from weather_nlu.question_info import TimeKind, TimeSlot
from weather_nlu.text import PhraseMatcher


type TimeRule = Callable[[date], TimeSlot]

MAX_UPCOMING_DAYS = 16
DEFAULT_UPCOMING_DAYS = 3
SEASON_MONTHS = 3
DAY_MONTH_PATTERN = re.compile(r"\b(\d{1,2})/(\d{1,2})\b")

NOW_PHRASES = ["lúc này", "bây giờ", "giờ này", "hiện tại", "hiện giờ", "hiện nay", "đang"]
BEST_TIME_PHRASES = [
    "tháng mấy",
    "tháng nào",
    "mùa nào",
    "tuần nào",
    "ngày nào",
    "hôm nào",
    "dịp nào",
    "khi nào",
    "lúc nào",
    "bao giờ",
    "thời điểm nào",
    "thời gian nào",
]
TODAY_PHRASES = ["hôm nay", "sáng nay", "trưa nay", "chiều nay", "tối nay", "đêm nay"]
TOMORROW_PHRASES = ["mai", "ngày mai"]
DAY_AFTER_TOMORROW_PHRASES = ["ngày kia", "ngày mốt"]
UPCOMING_DAYS_WORDS = ["ngày tới", "hôm tới", "ngày tiếp theo", "ngày sắp tới"]
SOME_DAYS_WORDS = ["mấy", "vài", "những", "các"]
MONTH_WORDS = {
    1: ["một", "giêng"],
    2: ["hai"],
    3: ["ba"],
    4: ["tư", "bốn"],
    5: ["năm"],
    6: ["sáu"],
    7: ["bảy"],
    8: ["tám"],
    9: ["chín"],
    10: ["mười"],
    11: ["mười một"],
    12: ["mười hai", "chạp"],
}
# Mùa theo thói quen gọi ở miền Bắc: xuân 2-4, hè 5-7, thu 8-10, đông 11-1.
SEASON_START_MONTHS = {"xuân": 2, "hè": 5, "hạ": 5, "thu": 8, "đông": 11}


def last_day_of_month(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def add_months(year: int, month: int, count: int) -> tuple[int, int]:
    """Cộng thêm count tháng, trả về (năm, tháng)."""
    index = year * 12 + (month - 1) + count
    return index // 12, index % 12 + 1


def months_slot(year: int, month: int, count: int = 1) -> TimeSlot:
    """Khoảng từ ngày đầu tháng đến hết tháng thứ count."""
    end_year, end_month = add_months(year, month, count - 1)
    return TimeSlot(
        TimeKind.MONTHS,
        date(year, month, 1),
        last_day_of_month(end_year, end_month),
    )


def days_slot(start: date, end: date) -> TimeSlot:
    return TimeSlot(TimeKind.DATES, start, end)


def month_of_year(month: int) -> TimeRule:
    """Tháng đã qua trong năm nay được hiểu là tháng đó của năm sau."""

    def build(today: date) -> TimeSlot:
        year = today.year if month >= today.month else today.year + 1
        return months_slot(year, month)

    return build


def season(start_month: int) -> TimeRule:
    """Chọn mùa đang diễn ra, hoặc mùa gần nhất sắp tới."""

    def build(today: date) -> TimeSlot:
        for year in (today.year - 1, today.year, today.year + 1):
            slot = months_slot(year, start_month, SEASON_MONTHS)
            if slot.end is not None and slot.end >= today:
                return slot
        return months_slot(today.year + 1, start_month, SEASON_MONTHS)

    return build


def upcoming_days(count: int) -> TimeRule:
    return lambda today: days_slot(
        today + timedelta(days=1), today + timedelta(days=count)
    )


def this_weekend(today: date) -> TimeSlot:
    monday = today - timedelta(days=today.weekday())
    saturday = monday + timedelta(days=5)
    return days_slot(max(today, saturday), monday + timedelta(days=6))


def next_weekend(today: date) -> TimeSlot:
    monday = today - timedelta(days=today.weekday())
    return days_slot(monday + timedelta(days=12), monday + timedelta(days=13))


def this_week(today: date) -> TimeSlot:
    monday = today - timedelta(days=today.weekday())
    return days_slot(today, monday + timedelta(days=6))


def next_week(today: date) -> TimeSlot:
    monday = today - timedelta(days=today.weekday())
    return days_slot(monday + timedelta(days=7), monday + timedelta(days=13))


def this_month(today: date) -> TimeSlot:
    return months_slot(today.year, today.month)


def next_month(today: date) -> TimeSlot:
    year, month = add_months(today.year, today.month, 1)
    return months_slot(year, month)


def this_season(today: date) -> TimeSlot:
    """Hiểu "mùa này" là tháng hiện tại và hai tháng tiếp theo."""
    return months_slot(today.year, today.month, SEASON_MONTHS)


def build_time_rules() -> list[tuple[str, TimeRule]]:
    """Liệt kê các cụm từ chỉ thời gian và cách tính khoảng thời gian tương ứng."""
    rules: list[tuple[str, TimeRule]] = []
    rules += [(phrase, lambda today: TimeSlot(TimeKind.NOW)) for phrase in NOW_PHRASES]
    rules += [
        (phrase, lambda today: TimeSlot(TimeKind.BEST_TIME))
        for phrase in BEST_TIME_PHRASES
    ]
    rules += [(phrase, lambda today: days_slot(today, today)) for phrase in TODAY_PHRASES]
    rules += [(phrase, upcoming_days(1)) for phrase in TOMORROW_PHRASES]
    rules += [
        (phrase, lambda today: days_slot(today + timedelta(days=2), today + timedelta(days=2)))
        for phrase in DAY_AFTER_TOMORROW_PHRASES
    ]
    for days_word in UPCOMING_DAYS_WORDS:
        rules += [
            (f"{count} {days_word}", upcoming_days(count))
            for count in range(1, MAX_UPCOMING_DAYS + 1)
        ]
        rules += [
            (f"{some} {days_word}", upcoming_days(DEFAULT_UPCOMING_DAYS))
            for some in SOME_DAYS_WORDS
        ]
    rules += [
        ("cuối tuần", this_weekend),
        ("cuối tuần này", this_weekend),
        ("cuối tuần sau", next_weekend),
        ("cuối tuần tới", next_weekend),
        ("tuần này", this_week),
        ("tuần sau", next_week),
        ("tuần tới", next_week),
        ("tháng này", this_month),
        ("tháng sau", next_month),
        ("tháng tới", next_month),
        ("mùa này", this_season),
        ("năm nay", lambda today: months_slot(today.year, 1, 12)),
        ("năm sau", lambda today: months_slot(today.year + 1, 1, 12)),
        ("năm tới", lambda today: months_slot(today.year + 1, 1, 12)),
        ("sang năm", lambda today: months_slot(today.year + 1, 1, 12)),
    ]
    for month, words in MONTH_WORDS.items():
        rules.append((f"tháng {month}", month_of_year(month)))
        rules += [(f"tháng {word}", month_of_year(month)) for word in words]
    rules += [
        (f"mùa {name}", season(start_month))
        for name, start_month in SEASON_START_MONTHS.items()
    ]
    return rules


TIME_MATCHER = PhraseMatcher(build_time_rules())


def find_day_month(text: str, today: date) -> TimeSlot | None:
    """Tìm ngày dạng 20/10; ngày đã qua được hiểu là ngày đó của năm sau."""
    for match in DAY_MONTH_PATTERN.finditer(text):
        day, month = int(match.group(1)), int(match.group(2))
        try:
            found = date(today.year, month, day)
            if found < today:
                found = date(today.year + 1, month, day)
        except ValueError:
            continue
        return days_slot(found, found)
    return None


def parse_time(text: str, today: date) -> TimeSlot | None:
    """Đổi các cụm từ chỉ thời gian trong câu thành TimeSlot.

    Thứ tự ưu tiên: hỏi thời điểm tốt nhất > khoảng thời gian cụ thể > hiện tại.
    Khi hỏi thời điểm tốt nhất, khoảng thời gian cụ thể (nếu có) là phạm vi tìm.
    """
    slots = [match.value(today) for match in TIME_MATCHER.find_all(text)]
    day_month = find_day_month(text, today)
    if day_month is not None:
        slots.append(day_month)

    kinds = {slot.kind for slot in slots}
    period = next(
        (slot for slot in slots if slot.kind in (TimeKind.DATES, TimeKind.MONTHS)),
        None,
    )
    if TimeKind.BEST_TIME in kinds:
        if period is None:
            return TimeSlot(TimeKind.BEST_TIME)
        return TimeSlot(TimeKind.BEST_TIME, period.start, period.end)
    if period is not None:
        return period
    if TimeKind.NOW in kinds:
        return TimeSlot(TimeKind.NOW)
    return None
