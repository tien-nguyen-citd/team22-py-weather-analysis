import csv
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from weather_nlu.intents import IntentKeywordMatcher
from weather_nlu.paths import QUESTIONS_PATH
from weather_nlu.question_info import Intent, QuestionInfo, TimeKind, TimeSlot


# Ngày dùng để tính nhãn thời gian trong questions.csv (thứ Tư).
REFERENCE_DATE = date(2026, 9, 16)
FIELD_NAMES = {
    "location": "Địa điểm",
    "time": "Thời gian",
    "activity": "Hoạt động",
    "intent": "Ý định",
}


@dataclass(frozen=True)
class LabeledQuestion:
    question: str
    expected: QuestionInfo
    group: str  # basic, paraphrase, place, holdout


@dataclass(frozen=True)
class Prediction:
    labeled: LabeledQuestion
    predicted: QuestionInfo

    @property
    def wrong_fields(self) -> list[str]:
        """Các trường dự đoán sai, theo khóa trong FIELD_NAMES."""
        expected, predicted = self.labeled.expected, self.predicted
        checks = {
            "location": expected.location_slug == predicted.location_slug,
            "time": expected.time == predicted.time,
            "activity": expected.activity_id == predicted.activity_id,
            "intent": expected.intent == predicted.intent,
        }
        return [name for name, is_correct in checks.items() if not is_correct]


@dataclass
class Score:
    correct: int = 0
    total: int = 0

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    def add(self, is_correct: bool) -> None:
        self.correct += is_correct
        self.total += 1


@dataclass
class EvaluationReport:
    overall: Score = field(default_factory=Score)
    by_field: dict[str, Score] = field(
        default_factory=lambda: {name: Score() for name in FIELD_NAMES}
    )
    by_group: dict[str, Score] = field(default_factory=dict)
    mistakes: list[Prediction] = field(default_factory=list)


def parse_optional_date(value: str) -> date | None:
    return date.fromisoformat(value) if value else None


def load_labeled_questions(path: Path = QUESTIONS_PATH) -> list[LabeledQuestion]:
    """Đọc các câu hỏi đã gán nhãn, nhãn thời gian tính theo REFERENCE_DATE."""
    with path.open(encoding="utf-8-sig", newline="") as file:
        return [
            LabeledQuestion(
                question=row["question"],
                expected=QuestionInfo(
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
                group=row["group"],
            )
            for row in csv.DictReader(file)
        ]


def evaluate(predictions: list[Prediction]) -> EvaluationReport:
    """Tính độ chính xác tổng, theo từng trường và theo từng nhóm câu hỏi.

    Một câu chỉ được tính đúng ở độ chính xác tổng khi cả bốn trường đều đúng.
    """
    report = EvaluationReport()
    for prediction in predictions:
        wrong_fields = prediction.wrong_fields
        is_correct = not wrong_fields
        report.overall.add(is_correct)
        report.by_group.setdefault(prediction.labeled.group, Score()).add(is_correct)
        for name, score in report.by_field.items():
            score.add(name not in wrong_fields)
        if not is_correct:
            report.mistakes.append(prediction)
    return report


def score_place_without_keyword(
    predictions: list[Prediction], keywords: IntentKeywordMatcher
) -> Score:
    """Chấm các câu tìm điểm đến không có từ khóa, chỉ MiniLM mới nhận ra được."""
    score = Score()
    for prediction in predictions:
        labeled = prediction.labeled
        if labeled.expected.intent != Intent.FIND_PLACE:
            continue
        if keywords.find(labeled.question) is not None:
            continue
        score.add(prediction.predicted.intent == Intent.FIND_PLACE)
    return score
