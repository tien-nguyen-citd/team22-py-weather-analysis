import unicodedata
from datetime import date

import numpy as np
import pytest

from weather_nlu.activities import ActivityExample, ActivityKeywordMatcher, load_activities
from weather_nlu.extractor import NearestExampleClassifier, RuleMiniLmExtractor
from weather_nlu.intents import IntentExample, IntentKeywordMatcher, load_intents
from weather_nlu.locations import LocationMatcher, load_locations
from weather_nlu.question_info import DecisionSource, ExtractionExplanation, Intent
from weather_nlu.text import remove_diacritics


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
            [
                PLACE_VECTOR if "goi y" in remove_diacritics(text).lower() else TIME_VECTOR
                for text in texts
            ]
        )


class LookupEncoder:
    """Encoder giả trả vector cho sẵn, bản không dấu dùng chung vector với bản gốc."""

    def __init__(self, vectors: dict[str, list[float]]) -> None:
        self._vectors = vectors
        self.texts: list[str] = []

    def encode(self, texts: list[str]) -> np.ndarray:
        self.texts += texts
        return np.array([self._vectors[remove_diacritics(text)] for text in texts])


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
        ("Tư vấn giúp tôi mấy điểm du lịch, gợi ý cho tháng 12", Intent.FIND_PLACE),
        ("Tháng 7 trời có oi bức không?", Intent.FIND_TIME),
    ],
)
def test_other_questions_use_nearest_examples(
    extractor: RuleMiniLmExtractor, question: str, intent: Intent
) -> None:
    assert extractor.extract(question, TODAY).intent == intent


def test_question_is_encoded_once_for_activity_and_intent(
    extractor: RuleMiniLmExtractor, encoder: RecordingEncoder
) -> None:
    result = extractor.extract("Gợi ý giúp mình vài nơi đẹp cho tháng 7", TODAY)

    assert result.activity_id is None
    assert result.intent == Intent.FIND_PLACE
    assert encoded_after_setup(encoder) == [["Gợi ý giúp mình vài nơi đẹp cho tháng 7"]]


def test_activity_phrases_are_removed_before_encoding(
    extractor: RuleMiniLmExtractor, encoder: RecordingEncoder
) -> None:
    result = extractor.extract(
        "Tháng 7 muốn đưa cả nhà đi nghỉ mát, gợi ý giúp mình vài nơi", TODAY
    )

    assert result.activity_id == "travel"
    assert result.intent == Intent.FIND_PLACE
    assert encoded_after_setup(encoder) == [
        ["Tháng 7 muốn đưa cả nhà đi  , gợi ý giúp mình vài nơi"]
    ]


def test_all_activity_phrases_are_removed(
    extractor: RuleMiniLmExtractor, encoder: RecordingEncoder
) -> None:
    extractor.extract("Gợi ý thành phố hợp chạy marathon tháng 12", TODAY)

    [[encoded]] = encoded_after_setup(encoder)
    assert "chạy" not in encoded
    assert "marathon" not in encoded


def explain(extractor: RuleMiniLmExtractor, question: str) -> ExtractionExplanation:
    explanation = extractor.extract(question, TODAY).explanation
    assert explanation is not None
    return explanation


def test_explanation_shows_matched_location_and_keyword(
    extractor: RuleMiniLmExtractor,
) -> None:
    explanation = explain(extractor, "Uống cafe ở Vũng Tàu")

    assert explanation.location_text == "Vũng Tàu"
    assert explanation.activity.source == DecisionSource.KEYWORD
    assert explanation.activity.matched_text == "cafe"
    assert explanation.intent.source == DecisionSource.LOCATION


def test_explanation_shows_intent_keyword(extractor: RuleMiniLmExtractor) -> None:
    explanation = explain(extractor, "Tháng 12 đi biển ở đâu?")

    assert explanation.intent.source == DecisionSource.KEYWORD
    assert explanation.intent.matched_text == "ở đâu"


def test_explanation_shows_best_time_question(extractor: RuleMiniLmExtractor) -> None:
    explanation = explain(extractor, "Gợi ý đám cưới tháng mấy thì đẹp nhất?")

    assert explanation.intent.source == DecisionSource.BEST_TIME


def test_explanation_shows_question_without_remaining_words(
    extractor: RuleMiniLmExtractor,
) -> None:
    explanation = explain(extractor, "cafe")

    assert explanation.embedding_text.strip() == ""
    assert explanation.intent.source == DecisionSource.NO_WORDS


def test_explanation_lists_nearest_examples(extractor: RuleMiniLmExtractor) -> None:
    explanation = explain(extractor, "Tháng 7 trời có oi bức không?")

    assert explanation.embedding_text == "Tháng 7 trời có oi bức không?"
    assert explanation.intent.source == DecisionSource.NEAREST_EXAMPLES
    neighbors = explanation.intent.neighbors
    assert len(neighbors) == 3
    similarities = [neighbor.similarity for neighbor in neighbors]
    assert similarities == sorted(similarities, reverse=True)
    assert neighbors[0].label == Intent.FIND_TIME
    # Câu mẫu không dấu cũng được liệt kê để thấy câu hỏi khớp với bản nào.
    assert "Troi hom nay the nao?" in [neighbor.text for neighbor in neighbors]


# Mỗi câu mẫu có thêm một bản không dấu nên được tính hai lần khi bỏ phiếu.
NEIGHBOR_VECTORS = {
    "a": [1.0, 0.0],
    "b": [0.8, 0.6],
    "c": [0.6, 0.8],
}


def test_majority_of_neighbors_beats_nearest_example() -> None:
    classifier = NearestExampleClassifier(
        LookupEncoder(NEIGHBOR_VECTORS), ["x", "y", "y"], ["a", "b", "c"], k=6
    )

    assert classifier.classify(np.array([1.0, 0.0])) == "y"


def test_tied_vote_uses_nearest_example() -> None:
    classifier = NearestExampleClassifier(
        LookupEncoder(NEIGHBOR_VECTORS), ["x", "y", "y"], ["a", "b", "c"], k=4
    )

    assert classifier.classify(np.array([1.0, 0.0])) == "x"


def test_examples_are_also_encoded_without_diacritics() -> None:
    encoder = LookupEncoder({"Da Lat": [1.0, 0.0]})

    NearestExampleClassifier(encoder, ["travel"], ["Đà Lạt"])

    assert encoder.texts == ["Đà Lạt", "Da Lat"]
