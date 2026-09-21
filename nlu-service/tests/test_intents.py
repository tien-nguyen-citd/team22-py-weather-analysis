import csv

import pytest

from weather_nlu.intents import IntentKeywordMatcher, load_intent_examples, load_intents
from weather_nlu.paths import QUESTIONS_PATH
from weather_nlu.question_info import Intent


@pytest.fixture(scope="module")
def intent_matcher() -> IntentKeywordMatcher:
    return IntentKeywordMatcher(load_intents())


def find_intent(matcher: IntentKeywordMatcher, text: str) -> Intent | None:
    match = matcher.find(text)
    return match.value if match else None


@pytest.mark.parametrize(
    ("text", "intent"),
    [
        ("Tháng 12 đi biển ở đâu?", Intent.FIND_PLACE),
        ("thang 12 di bien o dau", Intent.FIND_PLACE),
        ("Tháng sau tỉnh nào ít mưa?", Intent.FIND_PLACE),
        ("Cuối tuần đi đâu chơi?", Intent.FIND_PLACE),
        ("Đầu tháng 12 đi chơi được không?", None),
        ("Thời điểm nào tổ chức đám cưới tốt nhất?", None),
    ],
)
def test_find_intent_by_keyword(
    intent_matcher: IntentKeywordMatcher, text: str, intent: Intent | None
) -> None:
    assert find_intent(intent_matcher, text) == intent


def test_load_intents_reads_every_intent() -> None:
    intents = {intent.id: intent for intent in load_intents()}

    assert set(intents) == set(Intent)
    assert "ở đâu" in intents[Intent.FIND_PLACE].keywords
    assert intents[Intent.FIND_TIME].keywords == ()


def test_intent_examples_cover_every_intent() -> None:
    assert {example.intent for example in load_intent_examples()} == set(Intent)


def test_labeled_questions_only_use_known_intents() -> None:
    intent_ids = {intent.id.value for intent in load_intents()}
    with QUESTIONS_PATH.open(encoding="utf-8-sig", newline="") as file:
        labels = {row["intent"] for row in csv.DictReader(file)}

    assert labels <= intent_ids
