import csv
from datetime import date

import pytest

from weather_nlu.activities import (
    ActivityKeywordMatcher,
    load_activities,
    load_activity_examples,
)
from weather_nlu.encoder import MINILM_MODEL, MiniLmEncoder
from weather_nlu.extractor import RuleMiniLmExtractor
from weather_nlu.intents import IntentKeywordMatcher, load_intent_examples, load_intents
from weather_nlu.locations import LocationMatcher, load_locations
from weather_nlu.models import find_downloaded_model
from weather_nlu.paths import QUESTIONS_PATH
from weather_nlu.question_info import Intent, QuestionInfo, TimeKind, TimeSlot


REFERENCE_DATE = date(2026, 9, 16)
MINIMUM_ACCURACY = 0.72
MINIMUM_INTENT_ACCURACY = 0.9


def parse_optional_date(value: str) -> date | None:
    return date.fromisoformat(value) if value else None


def load_labeled_questions() -> list[tuple[str, QuestionInfo]]:
    with QUESTIONS_PATH.open(encoding="utf-8-sig", newline="") as file:
        return [
            (
                row["question"],
                QuestionInfo(
                    location_slug=row["location_slug"] or None,
                    time=TimeSlot(
                        TimeKind(row["time_kind"]),
                        parse_optional_date(row["time_start"]),
                        parse_optional_date(row["time_end"]),
                    )
                    if row["time_kind"]
                    else None,
                    activity_id=row["activity_id"] or None,
                    intent=Intent(row["intent"]),
                ),
            )
            for row in csv.DictReader(file)
        ]


@pytest.fixture(scope="module")
def extractor() -> RuleMiniLmExtractor:
    if find_downloaded_model(MINILM_MODEL) is None:
        pytest.skip("Chưa tải model, chạy python -m weather_nlu.download")

    return RuleMiniLmExtractor(
        MiniLmEncoder(),
        load_activity_examples(),
        LocationMatcher(load_locations()),
        ActivityKeywordMatcher(load_activities()),
        IntentKeywordMatcher(load_intents()),
        load_intent_examples(),
    )


@pytest.mark.model
def test_rule_and_minilm_accuracy(extractor: RuleMiniLmExtractor) -> None:
    questions = load_labeled_questions()
    example = extractor.extract("Mùa này đi Phú Quốc có hợp không?", REFERENCE_DATE)
    correct = sum(
        extractor.extract(question, REFERENCE_DATE) == expected
        for question, expected in questions
    )

    assert example.activity_id == "travel"
    assert correct / len(questions) >= MINIMUM_ACCURACY


@pytest.mark.model
def test_intent_accuracy(extractor: RuleMiniLmExtractor) -> None:
    questions = load_labeled_questions()
    correct = sum(
        extractor.extract(question, REFERENCE_DATE).intent == expected.intent
        for question, expected in questions
    )

    assert correct / len(questions) >= MINIMUM_INTENT_ACCURACY


@pytest.mark.model
def test_minilm_finds_place_without_keywords(extractor: RuleMiniLmExtractor) -> None:
    keywords = IntentKeywordMatcher(load_intents())
    questions = [
        question
        for question, expected in load_labeled_questions()
        if expected.intent == Intent.FIND_PLACE and keywords.find(question) is None
    ]
    correct = sum(
        extractor.extract(question, REFERENCE_DATE).intent == Intent.FIND_PLACE
        for question in questions
    )

    # Các câu này không có từ khóa nên chỉ MiniLM mới nhận ra được.
    assert questions
    assert correct / len(questions) > 0.5
