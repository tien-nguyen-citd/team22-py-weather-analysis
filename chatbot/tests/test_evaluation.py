from datetime import date

from weather_chatbot.activities import load_activities
from weather_chatbot.evaluation import (
    LabeledQuestion,
    QuestionResult,
    load_questions,
    percentile,
    run_extractor,
    summarize,
)
from weather_chatbot.locations import load_locations
from weather_chatbot.question_info import QuestionInfo, TimeKind, TimeSlot


NOW = TimeSlot(TimeKind.NOW)


def make_info(
    location_slug: str | None = None,
    location_text: str | None = None,
    activity_id: str | None = None,
) -> QuestionInfo:
    return QuestionInfo(location_slug, location_text, NOW, activity_id)


class FixedExtractor:
    name = "fixed"

    def __init__(self, info: QuestionInfo) -> None:
        self._info = info

    def extract(self, question: str, today: date) -> QuestionInfo:
        return self._info


def test_summarize_counts_each_field_and_group() -> None:
    basic = LabeledQuestion("a", make_info("da-lat", activity_id="travel"), "basic")
    paraphrase = LabeledQuestion("b", make_info("hue", activity_id="wedding"), "paraphrase")
    results = [
        QuestionResult(basic, make_info("da-lat", activity_id="travel"), 10),
        QuestionResult(paraphrase, make_info("hue", activity_id=None), 30),
    ]

    summary = summarize("fixed", results)

    assert summary.location_accuracy == 1
    assert summary.activity_accuracy == 0.5
    assert summary.all_accuracy == 0.5
    assert summary.all_accuracy_by_group == {"basic": 1.0, "paraphrase": 0.0}
    assert summary.average_ms == 20


def test_unknown_location_needs_empty_slug_and_similar_text() -> None:
    item = LabeledQuestion("Côn Đảo có mưa không?", make_info(None, "Côn Đảo"), "basic")

    assert QuestionResult(item, make_info(None, "Con Dao"), 1).unknown_location_detected
    assert not QuestionResult(item, make_info(None, None), 1).unknown_location_detected
    assert not QuestionResult(item, make_info("da-lat", "Côn Đảo"), 1).unknown_location_detected


def test_run_extractor_keeps_question_order() -> None:
    questions = [
        LabeledQuestion("a", make_info("da-lat"), "basic"),
        LabeledQuestion("b", make_info("hue"), "basic"),
    ]

    results = run_extractor(FixedExtractor(make_info("da-lat")), questions)

    assert [result.item.question for result in results] == ["a", "b"]
    assert [result.location_correct for result in results] == [True, False]


def test_percentile_uses_nearest_rank() -> None:
    assert percentile([5, 1, 3, 2, 4], 95) == 5
    assert percentile([5, 1, 3, 2, 4], 50) == 3
    assert percentile([], 95) == 0


def test_question_labels_use_known_values() -> None:
    slugs = {location.slug for location in load_locations()}
    activity_ids = {activity.id for activity in load_activities()}

    for item in load_questions():
        assert item.group in {"basic", "paraphrase"}
        assert item.expected.location_slug in slugs | {None}
        assert item.expected.activity_id in activity_ids | {None}
        if item.expected.time and item.expected.time.start and item.expected.time.end:
            assert item.expected.time.start <= item.expected.time.end
