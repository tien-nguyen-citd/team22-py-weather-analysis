"""Chạy bộ câu hỏi mẫu để đo độ chính xác và tài nguyên của từng cách trích xuất.

Cách dùng:
    python -m weather_chatbot.evaluate --extractor rule --show-errors
    python -m weather_chatbot.evaluate --extractor rule model2vec
    python -m weather_chatbot.evaluate --all
"""

import argparse
import dataclasses
import json
import subprocess
import sys
import time

import psutil

from weather_chatbot.evaluation import (
    EvaluationSummary,
    QuestionResult,
    load_questions,
    run_extractor,
    summarize,
)
from weather_chatbot.extractors.factory import EXTRACTORS
from weather_chatbot.models import downloaded_size_mb
from weather_chatbot.question_info import QuestionInfo, TimeSlot


GROUPS = ("basic", "paraphrase")


def peak_ram_mb() -> float:
    """RAM cao nhất mà process đã dùng (peak_wset chỉ có trên Windows)."""
    memory = psutil.Process().memory_info()
    return getattr(memory, "peak_wset", memory.rss) / 1024**2


def evaluate(extractor_name: str) -> tuple[EvaluationSummary, list[QuestionResult]]:
    spec = EXTRACTORS[extractor_name]
    started = time.perf_counter()
    extractor = spec.create()
    load_seconds = time.perf_counter() - started

    results = run_extractor(extractor, load_questions())
    summary = summarize(
        extractor_name,
        results,
        load_seconds=load_seconds,
        peak_ram_mb=peak_ram_mb(),
        model_size_mb=downloaded_size_mb(list(spec.models)),
    )
    return summary, results


def format_time(slot: TimeSlot | None) -> str:
    if slot is None:
        return "-"
    if slot.start is None:
        return slot.kind.value
    return f"{slot.kind.value} {slot.start}→{slot.end}"


def format_info(info: QuestionInfo) -> str:
    location = info.location_slug or (f'"{info.location_text}"' if info.location_text else "-")
    return f"địa điểm={location} | thời gian={format_time(info.time)} | hoạt động={info.activity_id or '-'}"


def print_errors(results: list[QuestionResult]) -> None:
    wrong_results = [result for result in results if not result.all_correct]
    print(f"\nCâu trả lời sai ({len(wrong_results)}/{len(results)}):")
    for result in wrong_results:
        print(f"\n- [{result.item.group}] {result.item.question}")
        print(f"  mong đợi: {format_info(result.item.expected)}")
        print(f"  kết quả : {format_info(result.predicted)}")


def percent(value: float) -> str:
    return f"{value * 100:.0f}%"


def print_table(summaries: list[EvaluationSummary]) -> None:
    headers = [
        "Cấu hình",
        "Địa điểm",
        "Thời gian",
        "Hoạt động",
        "Đủ 3",
        *(f"Đủ 3 ({group})" for group in GROUPS),
        "Địa điểm lạ",
        "Load (s)",
        "TB (ms)",
        "p95 (ms)",
        "RAM (MB)",
        "Model (MB)",
    ]
    rows = [
        [
            summary.extractor,
            percent(summary.location_accuracy),
            percent(summary.time_accuracy),
            percent(summary.activity_accuracy),
            percent(summary.all_accuracy),
            *(percent(summary.all_accuracy_by_group.get(group, 0.0)) for group in GROUPS),
            percent(summary.unknown_location_rate),
            f"{summary.load_seconds:.1f}",
            f"{summary.average_ms:.1f}",
            f"{summary.p95_ms:.1f}",
            f"{summary.peak_ram_mb:.0f}",
            f"{summary.model_size_mb:.0f}",
        ]
        for summary in summaries
    ]
    widths = [max(len(row[index]) for row in [headers, *rows]) for index in range(len(headers))]
    for row in [headers, *rows]:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)))
    print(f"\nSố câu hỏi: {summaries[0].total if summaries else 0}")


def evaluate_in_subprocess(extractor_name: str) -> EvaluationSummary:
    """Chạy mỗi cấu hình trong một process riêng để đo RAM không bị lẫn nhau."""
    completed = subprocess.run(
        [sys.executable, "-m", "weather_chatbot.evaluate", "--extractor", extractor_name, "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return EvaluationSummary(**json.loads(completed.stdout.strip().splitlines()[-1]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Đánh giá các cách trích xuất thông tin từ câu hỏi")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--extractor", nargs="+", choices=list(EXTRACTORS), help="một hoặc nhiều cấu hình cần đánh giá"
    )
    selection.add_argument("--all", action="store_true", help="đánh giá lần lượt mọi cấu hình")
    parser.add_argument(
        "--show-errors", action="store_true", help="in các câu trả lời sai (chỉ khi đánh giá một cấu hình)"
    )
    parser.add_argument(
        "--json", action="store_true", help="chỉ in kết quả dạng JSON (chỉ khi đánh giá một cấu hình)"
    )
    args = parser.parse_args()
    names = list(EXTRACTORS) if args.all else list(dict.fromkeys(args.extractor))

    if len(names) == 1:
        summary, results = evaluate(names[0])
        if args.json:
            print(json.dumps(dataclasses.asdict(summary), ensure_ascii=False))
            return
        print_table([summary])
        if args.show_errors:
            print_errors(results)
        return

    if args.show_errors or args.json:
        parser.error("--show-errors và --json chỉ dùng khi đánh giá một cấu hình")
    summaries: list[EvaluationSummary] = []
    for name in names:
        print(f"Đang đánh giá {name}...", file=sys.stderr, flush=True)
        summaries.append(evaluate_in_subprocess(name))
    print_table(summaries)


if __name__ == "__main__":
    main()
