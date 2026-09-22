import io
import sys

from weather_nlu.evaluation import (
    FIELD_NAMES,
    REFERENCE_DATE,
    EvaluationReport,
    Prediction,
    Score,
    evaluate,
    load_labeled_questions,
    score_place_without_keyword,
)
from weather_nlu.extractor import build_rule_minilm_extractor
from weather_nlu.intents import IntentKeywordMatcher, load_intents
from weather_nlu.question_info import QuestionInfo


def format_score(score: Score) -> str:
    return f"{score.correct}/{score.total} ({score.accuracy:.3f})"


def format_value(info: QuestionInfo, field_name: str) -> str:
    if field_name == "location":
        return str(info.location_slug)
    if field_name == "time":
        if info.time is None:
            return "None"
        return f"{info.time.kind} {info.time.start} → {info.time.end}"
    if field_name == "activity":
        return str(info.activity_id)
    return str(info.intent)


def print_report(report: EvaluationReport, place_without_keyword: Score) -> None:
    print(f"Độ chính xác tổng: {format_score(report.overall)}")

    print("\nTheo từng trường:")
    for name, score in report.by_field.items():
        print(f"  {FIELD_NAMES[name]}: {format_score(score)}")

    print("\nTheo nhóm câu hỏi:")
    for group, score in report.by_group.items():
        print(f"  {group}: {format_score(score)}")

    print(
        "\nCâu tìm điểm đến không có từ khóa được MiniLM nhận đúng: "
        f"{format_score(place_without_keyword)}"
    )

    print(f"\nCác câu sai ({len(report.mistakes)}):")
    for prediction in report.mistakes:
        print(f"- [{prediction.labeled.group}] {prediction.labeled.question}")
        for name in prediction.wrong_fields:
            expected = format_value(prediction.labeled.expected, name)
            predicted = format_value(prediction.predicted, name)
            print(f"    {FIELD_NAMES[name]}: cần {expected}, nhận {predicted}")


def main() -> None:
    # Console Windows có thể không dùng UTF-8 khi ghi kết quả ra file.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    extractor = build_rule_minilm_extractor()
    predictions = [
        Prediction(labeled, extractor.extract(labeled.question, REFERENCE_DATE))
        for labeled in load_labeled_questions()
    ]
    print_report(
        evaluate(predictions),
        score_place_without_keyword(predictions, IntentKeywordMatcher(load_intents())),
    )


if __name__ == "__main__":
    main()
