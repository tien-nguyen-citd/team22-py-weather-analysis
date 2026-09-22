from datetime import date

from weather_nlu.evaluation import (
    LabeledQuestion,
    Prediction,
    evaluate,
    load_labeled_questions,
    score_place_without_keyword,
)
from weather_nlu.intents import IntentKeywordMatcher, load_intents
from weather_nlu.question_info import Intent, QuestionInfo, TimeKind, TimeSlot


DECEMBER = TimeSlot(TimeKind.MONTHS, date(2026, 12, 1), date(2026, 12, 31))


def labeled(
    question: str, info: QuestionInfo, group: str = "basic"
) -> LabeledQuestion:
    return LabeledQuestion(question, info, group)


def test_wrong_fields_lists_every_mismatch() -> None:
    expected = QuestionInfo("da-lat", DECEMBER, "travel", Intent.FIND_TIME)
    predicted = QuestionInfo(None, DECEMBER, "camping", Intent.FIND_TIME)

    prediction = Prediction(labeled("Tháng 12 đi Đà Lạt?", expected), predicted)

    assert prediction.wrong_fields == ["location", "activity"]


def test_evaluate_scores_overall_fields_and_groups() -> None:
    place = QuestionInfo(None, DECEMBER, "beach", Intent.FIND_PLACE)
    time = QuestionInfo("hue", None, None, Intent.FIND_TIME)
    predictions = [
        Prediction(labeled("Tháng 12 đi biển ở đâu?", place, "place"), place),
        Prediction(
            labeled("Gợi ý nơi đi biển tháng 12", place, "holdout"),
            QuestionInfo(None, DECEMBER, "beach", Intent.FIND_TIME),
        ),
        Prediction(labeled("Huế thế nào?", time, "holdout"), time),
    ]

    report = evaluate(predictions)

    assert (report.overall.correct, report.overall.total) == (2, 3)
    assert report.by_field["intent"].correct == 2
    assert report.by_field["location"].correct == 3
    assert report.by_group["place"].accuracy == 1.0
    assert (report.by_group["holdout"].correct, report.by_group["holdout"].total) == (1, 2)
    assert [mistake.labeled.question for mistake in report.mistakes] == [
        "Gợi ý nơi đi biển tháng 12"
    ]


def test_score_place_without_keyword_skips_keyword_questions() -> None:
    place = QuestionInfo(None, DECEMBER, None, Intent.FIND_PLACE)
    predictions = [
        Prediction(labeled("Tháng 12 đi biển ở đâu?", place), place),
        Prediction(
            labeled("Gợi ý vài điểm đến cho tháng 12", place),
            QuestionInfo(None, DECEMBER, None, Intent.FIND_TIME),
        ),
    ]

    score = score_place_without_keyword(predictions, IntentKeywordMatcher(load_intents()))

    assert (score.correct, score.total) == (0, 1)


def test_labeled_questions_include_holdout_group() -> None:
    groups = {question.group for question in load_labeled_questions()}

    assert "holdout" in groups
