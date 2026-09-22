import csv

import pytest

from weather_nlu.evaluation import load_labeled_questions
from weather_nlu.intents import IntentKeywordMatcher, load_intent_examples, load_intents
from weather_nlu.paths import QUESTIONS_PATH
from weather_nlu.question_info import Intent
from weather_nlu.text import PhraseMatcher


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
        ("Du lịch Cát Bà vào tháng 7 thế nào?", Intent.FIND_TIME),
        ("Mình định đi Mũi Né tháng sau, thời tiết có ổn không?", Intent.FIND_TIME),
        ("Đầu tháng 12 đi chơi được không?", None),
        ("Thời điểm nào tổ chức đám cưới tốt nhất?", None),
    ],
)
def test_find_intent_by_keyword(
    intent_matcher: IntentKeywordMatcher, text: str, intent: Intent | None
) -> None:
    assert find_intent(intent_matcher, text) == intent


def test_earlier_intent_wins_when_both_keywords_appear(
    intent_matcher: IntentKeywordMatcher,
) -> None:
    assert find_intent(intent_matcher, "Tháng 12 đi đâu thì có hợp không?") == Intent.FIND_PLACE


def test_load_intents_reads_every_intent_in_priority_order() -> None:
    intents = load_intents()
    by_id = {intent.id: intent for intent in intents}

    assert [intent.id for intent in intents] == [Intent.FIND_PLACE, Intent.FIND_TIME]
    assert "ở đâu" in by_id[Intent.FIND_PLACE].keywords
    assert "thế nào" in by_id[Intent.FIND_TIME].keywords


def test_find_time_keywords_do_not_match_place_questions() -> None:
    find_time = next(intent for intent in load_intents() if intent.id == Intent.FIND_TIME)
    matcher = PhraseMatcher((keyword, keyword) for keyword in find_time.keywords)
    place_questions = [
        example.text
        for example in load_intent_examples()
        if example.intent == Intent.FIND_PLACE
    ] + [
        labeled.question
        for labeled in load_labeled_questions()
        if labeled.expected.intent == Intent.FIND_PLACE
    ]

    matched = [text for text in place_questions if matcher.find_first(text) is not None]

    assert matched == []


def test_intent_examples_cover_every_intent() -> None:
    assert {example.intent for example in load_intent_examples()} == set(Intent)


def test_labeled_questions_only_use_known_intents() -> None:
    intent_ids = {intent.id.value for intent in load_intents()}
    with QUESTIONS_PATH.open(encoding="utf-8-sig", newline="") as file:
        labels = {row["intent"] for row in csv.DictReader(file)}

    assert labels <= intent_ids
