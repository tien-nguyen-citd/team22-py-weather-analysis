import pytest

from weather_nlu.encoder import MINILM_MODEL
from weather_nlu.evaluation import REFERENCE_DATE, load_labeled_questions
from weather_nlu.extractor import RuleMiniLmExtractor, build_rule_minilm_extractor
from weather_nlu.intents import IntentKeywordMatcher, load_intents
from weather_nlu.models import find_downloaded_model
from weather_nlu.question_info import Intent


MINIMUM_ACCURACY = 0.72
MINIMUM_INTENT_ACCURACY = 0.9


@pytest.fixture(scope="module")
def extractor() -> RuleMiniLmExtractor:
    if find_downloaded_model(MINILM_MODEL) is None:
        pytest.skip("Chưa tải model, chạy python -m weather_nlu.download")

    return build_rule_minilm_extractor()


@pytest.mark.model
def test_rule_and_minilm_accuracy(extractor: RuleMiniLmExtractor) -> None:
    questions = load_labeled_questions()
    example = extractor.extract("Mùa này đi Phú Quốc có hợp không?", REFERENCE_DATE)
    correct = sum(
        extractor.extract(labeled.question, REFERENCE_DATE) == labeled.expected
        for labeled in questions
    )

    assert example.activity_id == "travel"
    assert correct / len(questions) >= MINIMUM_ACCURACY


@pytest.mark.model
def test_intent_accuracy(extractor: RuleMiniLmExtractor) -> None:
    questions = load_labeled_questions()
    correct = sum(
        extractor.extract(labeled.question, REFERENCE_DATE).intent
        == labeled.expected.intent
        for labeled in questions
    )

    assert correct / len(questions) >= MINIMUM_INTENT_ACCURACY


@pytest.mark.model
def test_minilm_finds_place_without_keywords(extractor: RuleMiniLmExtractor) -> None:
    keywords = IntentKeywordMatcher(load_intents())
    questions = [
        labeled.question
        for labeled in load_labeled_questions()
        if labeled.expected.intent == Intent.FIND_PLACE
        and keywords.find(labeled.question) is None
    ]
    correct = sum(
        extractor.extract(question, REFERENCE_DATE).intent == Intent.FIND_PLACE
        for question in questions
    )

    # Các câu này không có từ khóa nên chỉ MiniLM mới nhận ra được.
    assert questions
    assert correct / len(questions) > 0.5


@pytest.mark.model
@pytest.mark.parametrize(
    "question",
    [
        "Tháng 7 muốn đưa cả nhà đi nghỉ mát, gợi ý giúp mình vài nơi",
        "Tư vấn giúp tôi mấy điểm du lịch hợp đi vào tháng 12",
    ],
)
def test_demo_questions_find_place_for_travel(
    extractor: RuleMiniLmExtractor, question: str
) -> None:
    result = extractor.extract(question, REFERENCE_DATE)

    assert result.intent == Intent.FIND_PLACE
    assert result.activity_id == "travel"
