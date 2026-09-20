from datetime import date

import pytest

from weather_chatbot.activities import ActivityKeywordMatcher
from weather_chatbot.evaluation import load_questions, run_extractor, summarize
from weather_chatbot.extractors.rule_based import RuleBasedExtractor
from weather_chatbot.locations import LocationMatcher
from weather_chatbot.question_info import QuestionInfo, TimeKind, TimeSlot


TODAY = date(2026, 9, 16)


@pytest.fixture
def extractor(
    location_matcher: LocationMatcher, activity_matcher: ActivityKeywordMatcher
) -> RuleBasedExtractor:
    return RuleBasedExtractor(location_matcher, activity_matcher)


def test_extract_current_weather_question(extractor: RuleBasedExtractor) -> None:
    assert extractor.extract("Lúc này Đà Lạt có đang mưa không?", TODAY) == QuestionInfo(
        location_slug="da-lat",
        location_text="Đà Lạt",
        time=TimeSlot(TimeKind.NOW),
        activity_id=None,
    )


def test_extract_best_time_question_without_location(extractor: RuleBasedExtractor) -> None:
    assert extractor.extract("Đám cưới tháng mấy thì đẹp nhất?", TODAY) == QuestionInfo(
        location_slug=None,
        location_text=None,
        time=TimeSlot(TimeKind.BEST_TIME),
        activity_id="wedding",
    )


def test_going_to_a_location_means_travel(extractor: RuleBasedExtractor) -> None:
    info = extractor.extract("Mùa này đi Phú Quốc có hợp không?", TODAY)

    assert info.location_slug == "phu-quoc"
    assert info.time == TimeSlot(TimeKind.MONTHS, date(2026, 9, 1), date(2026, 11, 30))
    assert info.activity_id == "travel"


def test_upcoming_days_is_not_travel(extractor: RuleBasedExtractor) -> None:
    info = extractor.extract("Mấy ngày tới Quy Nhơn thời tiết ra sao?", TODAY)

    assert info.activity_id is None


def test_accuracy_on_basic_questions(extractor: RuleBasedExtractor) -> None:
    questions = [item for item in load_questions() if item.group == "basic"]

    summary = summarize(extractor.name, run_extractor(extractor, questions))

    assert summary.all_accuracy >= 0.9
