import csv
import math
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from weather_chatbot.extractors.base import QuestionExtractor
from weather_chatbot.paths import QUESTIONS_PATH
from weather_chatbot.question_info import QuestionInfo, TimeKind, TimeSlot
from weather_chatbot.text import tokenize


# Nhãn thời gian trong questions.csv được tính theo ngày này.
REFERENCE_DATE = date(2026, 9, 16)


@dataclass(frozen=True)
class LabeledQuestion:
    question: str
    expected: QuestionInfo
    group: str  # basic: cách hỏi thông thường, paraphrase: cách nói tự nhiên, ít từ khóa

    @property
    def asks_unknown_location(self) -> bool:
        """Câu hỏi nhắc tới địa điểm không có trong danh sách."""
        return self.expected.location_slug is None and bool(self.expected.location_text)


@dataclass(frozen=True)
class QuestionResult:
    item: LabeledQuestion
    predicted: QuestionInfo
    milliseconds: float

    @property
    def location_correct(self) -> bool:
        return self.predicted.location_slug == self.item.expected.location_slug

    @property
    def time_correct(self) -> bool:
        return self.predicted.time == self.item.expected.time

    @property
    def activity_correct(self) -> bool:
        return self.predicted.activity_id == self.item.expected.activity_id

    @property
    def all_correct(self) -> bool:
        return self.location_correct and self.time_correct and self.activity_correct

    @property
    def unknown_location_detected(self) -> bool:
        """Không gán nhầm slug và vẫn giữ được tên địa điểm lạ."""
        if self.predicted.location_slug is not None or not self.predicted.location_text:
            return False
        expected_words = {token.plain for token in tokenize(self.item.expected.location_text or "")}
        predicted_words = {token.plain for token in tokenize(self.predicted.location_text)}
        return bool(expected_words & predicted_words)


@dataclass(frozen=True)
class EvaluationSummary:
    extractor: str
    total: int
    location_accuracy: float
    time_accuracy: float
    activity_accuracy: float
    all_accuracy: float
    all_accuracy_by_group: dict[str, float]
    unknown_location_rate: float
    load_seconds: float
    average_ms: float
    p95_ms: float
    peak_ram_mb: float
    model_size_mb: float


def parse_optional_date(value: str) -> date | None:
    return date.fromisoformat(value) if value else None


def load_questions(path: Path = QUESTIONS_PATH) -> list[LabeledQuestion]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return [
            LabeledQuestion(
                question=row["question"],
                expected=QuestionInfo(
                    location_slug=row["location_slug"] or None,
                    location_text=row["location_text"] or None,
                    time=TimeSlot(
                        TimeKind(row["time_kind"]),
                        parse_optional_date(row["time_start"]),
                        parse_optional_date(row["time_end"]),
                    )
                    if row["time_kind"]
                    else None,
                    activity_id=row["activity_id"] or None,
                ),
                group=row["group"],
            )
            for row in csv.DictReader(file)
        ]


def run_extractor(
    extractor: QuestionExtractor,
    questions: list[LabeledQuestion],
    today: date = REFERENCE_DATE,
) -> list[QuestionResult]:
    results: list[QuestionResult] = []
    for item in questions:
        started = time.perf_counter()
        predicted = extractor.extract(item.question, today)
        milliseconds = (time.perf_counter() - started) * 1000
        results.append(QuestionResult(item, predicted, milliseconds))
    return results


def ratio(count: int, total: int) -> float:
    return count / total if total else 0.0


def percentile(values: list[float], percent: float) -> float:
    """Percentile theo cách lấy phần tử gần nhất."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(percent / 100 * len(ordered)) - 1)
    return ordered[index]


def summarize(
    extractor: str,
    results: list[QuestionResult],
    *,
    load_seconds: float = 0.0,
    peak_ram_mb: float = 0.0,
    model_size_mb: float = 0.0,
) -> EvaluationSummary:
    total = len(results)
    unknown_location_results = [result for result in results if result.item.asks_unknown_location]
    timings = [result.milliseconds for result in results]
    groups = sorted({result.item.group for result in results})
    results_by_group = {
        group: [result for result in results if result.item.group == group] for group in groups
    }
    return EvaluationSummary(
        extractor=extractor,
        total=total,
        location_accuracy=ratio(sum(result.location_correct for result in results), total),
        time_accuracy=ratio(sum(result.time_correct for result in results), total),
        activity_accuracy=ratio(sum(result.activity_correct for result in results), total),
        all_accuracy=ratio(sum(result.all_correct for result in results), total),
        all_accuracy_by_group={
            group: ratio(sum(result.all_correct for result in group_results), len(group_results))
            for group, group_results in results_by_group.items()
        },
        unknown_location_rate=ratio(
            sum(result.unknown_location_detected for result in unknown_location_results),
            len(unknown_location_results),
        ),
        load_seconds=load_seconds,
        average_ms=sum(timings) / total if total else 0.0,
        p95_ms=percentile(timings, 95),
        peak_ram_mb=peak_ram_mb,
        model_size_mb=model_size_mb,
    )
