from datetime import date

import pytest

from weather_nlu.question_info import TimeKind, TimeSlot
from weather_nlu.time_parser import parse_time


# Thứ Tư
TODAY = date(2026, 9, 16)


def dates(start: date, end: date) -> TimeSlot:
    return TimeSlot(TimeKind.DATES, start, end)


def months(start: date, end: date) -> TimeSlot:
    return TimeSlot(TimeKind.MONTHS, start, end)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Lúc này có mưa không?", TimeSlot(TimeKind.NOW)),
        ("Trời có đang mưa không?", TimeSlot(TimeKind.NOW)),
        ("Hôm nay có mưa không?", dates(date(2026, 9, 16), date(2026, 9, 16))),
        ("chieu nay co mua khong", dates(date(2026, 9, 16), date(2026, 9, 16))),
        ("Sáng mai có mưa không?", dates(date(2026, 9, 17), date(2026, 9, 17))),
        ("Ngày kia có mưa không?", dates(date(2026, 9, 18), date(2026, 9, 18))),
        ("5 ngày tới có mưa không?", dates(date(2026, 9, 17), date(2026, 9, 21))),
        ("Mấy ngày tới có mưa không?", dates(date(2026, 9, 17), date(2026, 9, 19))),
        ("Cuối tuần này có mưa không?", dates(date(2026, 9, 19), date(2026, 9, 20))),
        ("Cuối tuần sau có mưa không?", dates(date(2026, 9, 26), date(2026, 9, 27))),
        ("Tuần này có mưa không?", dates(date(2026, 9, 16), date(2026, 9, 20))),
        ("Tuần sau có mưa không?", dates(date(2026, 9, 21), date(2026, 9, 27))),
        ("Ngày 20/10 có mưa không?", dates(date(2026, 10, 20), date(2026, 10, 20))),
        ("Ngày 2/9 có mưa không?", dates(date(2027, 9, 2), date(2027, 9, 2))),
        ("Tháng này có mưa không?", months(date(2026, 9, 1), date(2026, 9, 30))),
        ("Tháng sau có mưa không?", months(date(2026, 10, 1), date(2026, 10, 31))),
        ("Tháng 12 có lạnh không?", months(date(2026, 12, 1), date(2026, 12, 31))),
        ("Tháng mười hai có lạnh không?", months(date(2026, 12, 1), date(2026, 12, 31))),
        ("Tháng 3 có nồm không?", months(date(2027, 3, 1), date(2027, 3, 31))),
        ("Mùa này có mưa không?", months(date(2026, 9, 1), date(2026, 11, 30))),
        ("Mùa thu có đẹp không?", months(date(2026, 8, 1), date(2026, 10, 31))),
        ("Mùa đông có lạnh không?", months(date(2026, 11, 1), date(2027, 1, 31))),
        ("Mùa hè có nóng không?", months(date(2027, 5, 1), date(2027, 7, 31))),
        ("Năm sau có nhiều bão không?", months(date(2027, 1, 1), date(2027, 12, 31))),
        ("Hè này muốn trốn nóng ở đâu?", months(date(2027, 5, 1), date(2027, 7, 31))),
        ("Nghỉ hè đi đâu cho mát?", months(date(2027, 5, 1), date(2027, 7, 31))),
        ("Đông này có rét đậm không?", months(date(2026, 11, 1), date(2027, 1, 31))),
        ("Tết đi đâu cho ấm?", months(date(2027, 1, 1), date(2027, 2, 28))),
        ("tet nay di dau", months(date(2027, 1, 1), date(2027, 2, 28))),
        ("Tết dương lịch có lạnh không?", months(date(2027, 1, 1), date(2027, 1, 31))),
        ("Trung thu có mưa không?", months(date(2026, 9, 1), date(2026, 10, 31))),
        ("Tết trung thu có mưa không?", months(date(2026, 9, 1), date(2026, 10, 31))),
        ("Ngồi cafe vỉa hè có nóng không?", None),
        ("Tháng mấy thì đẹp nhất?", TimeSlot(TimeKind.BEST_TIME)),
        ("Khi nào nên đi?", TimeSlot(TimeKind.BEST_TIME)),
        (
            "Tuần sau ngày nào chạy bộ được?",
            TimeSlot(TimeKind.BEST_TIME, date(2026, 9, 21), date(2026, 9, 27)),
        ),
        ("Thời tiết Hà Nội thế nào?", None),
    ],
)
def test_parse_time(text: str, expected: TimeSlot | None) -> None:
    assert parse_time(text, TODAY) == expected


def test_specific_period_wins_over_now() -> None:
    assert parse_time("Mình đang định đi chơi tháng sau", TODAY) == months(
        date(2026, 10, 1), date(2026, 10, 31)
    )


def test_this_weekend_on_sunday_only_includes_today() -> None:
    sunday = date(2026, 9, 20)

    assert parse_time("Cuối tuần này có mưa không?", sunday) == dates(sunday, sunday)


def test_winter_in_january_is_current_winter() -> None:
    assert parse_time("Mùa đông có lạnh không?", date(2027, 1, 10)) == months(
        date(2026, 11, 1), date(2027, 1, 31)
    )


def test_lunar_new_year_in_february_is_current_one() -> None:
    assert parse_time("Tết có lạnh không?", date(2027, 2, 10)) == months(
        date(2027, 1, 1), date(2027, 2, 28)
    )
