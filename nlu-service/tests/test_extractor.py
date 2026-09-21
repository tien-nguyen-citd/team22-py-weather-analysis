import unicodedata
from datetime import date

import numpy as np
import pytest

from weather_nlu.activities import ActivityExample, ActivityKeywordMatcher, load_activities
from weather_nlu.extractor import RuleMiniLmExtractor
from weather_nlu.intents import IntentExample, IntentKeywordMatcher, load_intents
from weather_nlu.locations import LocationMatcher, load_locations
from weather_nlu.question_info import Intent


TODAY = date(2026, 9, 20)
PLACE_VECTOR = [1.0, 0.0]
TIME_VECTOR = [0.0, 1.0]


class RecordingEncoder:
    """Encoder giả: câu có chữ "gợi ý" gần câu mẫu tìm điểm đến, câu khác gần câu mẫu còn lại."""

    def __init__(self) -> None:
        self.batches: list[list[str]] = []

    def encode(self, texts: list[str]) -> np.ndarray:
        self.batches.append(texts)
        return np.array(
            [PLACE_VECTOR if "gợi ý" in text.lower() else TIME_VECTOR for text in texts]
        )


@pytest.fixture
def encoder() -> RecordingEncoder:
    return RecordingEncoder()


@pytest.fixture
def extractor(encoder: RecordingEncoder) -> RuleMiniLmExtractor:
    return RuleMiniLmExtractor(
        encoder,
        [ActivityExample(None, "Thời tiết thế nào?")],
        LocationMatcher(load_locations()),
        ActivityKeywordMatcher(load_activities()),
        IntentKeywordMatcher(load_intents()),
        [
            IntentExample(Intent.FIND_PLACE, "Gợi ý điểm đến cho kỳ nghỉ"),
            IntentExample(Intent.FIND_TIME, "Trời hôm nay thế nào?"),
        ],
    )


def encoded_after_setup(encoder: RecordingEncoder) -> list[list[str]]:
    """Bỏ hai lần encode câu mẫu lúc khởi tạo, chỉ giữ các lần encode câu hỏi."""
    return encoder.batches[2:]


@pytest.mark.parametrize(
    "question",
    [
        "Vũng Tàu",
        unicodedata.normalize("NFD", "Vũng tàu"),
        "Nha Trang?",
        "Hà Nội!",
    ],
)
def test_location_only_has_no_explicit_activity(
    extractor: RuleMiniLmExtractor, question: str
) -> None:
    result = extractor.extract(question, TODAY)

    assert result.location_slug is not None
    assert result.activity_id is None


def test_explicit_activity_wins_for_location(
    extractor: RuleMiniLmExtractor,
) -> None:
    result = extractor.extract("Uống cafe ở Vũng Tàu", TODAY)

    assert result.location_slug == "vung-tau"
    assert result.activity_id == "coffee"


def test_question_with_known_location_finds_time(
    extractor: RuleMiniLmExtractor, encoder: RecordingEncoder
) -> None:
    result = extractor.extract("Gợi ý tháng nào đi Đà Lạt đẹp?", TODAY)

    assert result.intent == Intent.FIND_TIME
    # Chỉ encode một lần để đoán hoạt động, câu đã bỏ tên địa điểm.
    assert encoded_after_setup(encoder) == [["Gợi ý tháng nào đi   đẹp?"]]


@pytest.mark.parametrize(
    "question",
    ["Tháng 12 đi biển ở đâu?", "thang 12 di bien o dau"],
)
def test_place_keyword_finds_place(extractor: RuleMiniLmExtractor, question: str) -> None:
    assert extractor.extract(question, TODAY).intent == Intent.FIND_PLACE


def test_best_time_question_finds_time(
    extractor: RuleMiniLmExtractor, encoder: RecordingEncoder
) -> None:
    result = extractor.extract("Gợi ý đám cưới tháng mấy thì đẹp nhất?", TODAY)

    assert result.intent == Intent.FIND_TIME
    assert encoded_after_setup(encoder) == []


@pytest.mark.parametrize(
    ("question", "intent"),
    [
        ("Gợi ý giúp mình điểm nghỉ mát cho tháng 7", Intent.FIND_PLACE),
        ("Tháng 7 trời có oi bức không?", Intent.FIND_TIME),
    ],
)
def test_other_questions_use_nearest_example(
    extractor: RuleMiniLmExtractor, question: str, intent: Intent
) -> None:
    assert extractor.extract(question, TODAY).intent == intent


def test_question_is_encoded_once_for_activity_and_intent(
    extractor: RuleMiniLmExtractor, encoder: RecordingEncoder
) -> None:
    result = extractor.extract("Gợi ý giúp mình điểm nghỉ mát cho tháng 7", TODAY)

    assert result.activity_id is None
    assert result.intent == Intent.FIND_PLACE
    assert encoded_after_setup(encoder) == [["Gợi ý giúp mình điểm nghỉ mát cho tháng 7"]]
