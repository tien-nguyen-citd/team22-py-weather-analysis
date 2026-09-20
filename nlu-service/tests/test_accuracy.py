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
from weather_nlu.locations import LocationMatcher, load_locations
from weather_nlu.models import find_downloaded_model
from weather_nlu.paths import QUESTIONS_PATH
from weather_nlu.question_info import QuestionInfo, TimeKind, TimeSlot


REFERENCE_DATE = date(2026, 9, 16)
MINIMUM_ACCURACY = 0.72


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
                ),
            )
            for row in csv.DictReader(file)
        ]


@pytest.mark.model
def test_rule_and_minilm_accuracy() -> None:
    if find_downloaded_model(MINILM_MODEL) is None:
        pytest.skip("Chưa tải model, chạy python -m weather_nlu.download")

    extractor = RuleMiniLmExtractor(
        MiniLmEncoder(),
        load_activity_examples(),
        LocationMatcher(load_locations()),
        ActivityKeywordMatcher(load_activities()),
    )
    questions = load_labeled_questions()
    example = extractor.extract("Mùa này đi Phú Quốc có hợp không?", REFERENCE_DATE)
    correct = sum(
        extractor.extract(question, REFERENCE_DATE) == expected
        for question, expected in questions
    )

    assert example.activity_id == "travel"
    assert correct / len(questions) >= MINIMUM_ACCURACY
