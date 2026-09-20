import csv
from dataclasses import dataclass
from pathlib import Path

from weather_chatbot.paths import ACTIVITIES_PATH, ACTIVITY_EXAMPLES_PATH
from weather_chatbot.text import PhraseMatch, PhraseMatcher


KEYWORD_SEPARATOR = ";"


@dataclass(frozen=True)
class Activity:
    id: str
    name: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class ActivityExample:
    activity_id: str | None  # None là câu hỏi thời tiết chung, không nêu hoạt động
    text: str


def load_activities(path: Path = ACTIVITIES_PATH) -> list[Activity]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return [
            Activity(
                id=row["id"],
                name=row["name"],
                keywords=tuple(
                    keyword.strip()
                    for keyword in row["keywords"].split(KEYWORD_SEPARATOR)
                    if keyword.strip()
                ),
            )
            for row in csv.DictReader(file)
        ]


def load_activity_examples(path: Path = ACTIVITY_EXAMPLES_PATH) -> list[ActivityExample]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return [
            ActivityExample(activity_id=row["activity_id"] or None, text=row["text"])
            for row in csv.DictReader(file)
        ]


class ActivityKeywordMatcher:
    """Tìm hoạt động theo từ khóa, lấy từ khóa xuất hiện đầu tiên trong câu."""

    def __init__(self, activities: list[Activity]) -> None:
        self._matcher = PhraseMatcher(
            (keyword, activity.id)
            for activity in activities
            for keyword in activity.keywords
        )

    def find(self, text: str) -> PhraseMatch[str] | None:
        return self._matcher.find_first(text)
