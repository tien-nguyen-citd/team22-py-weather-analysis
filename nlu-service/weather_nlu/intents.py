import csv
from dataclasses import dataclass
from pathlib import Path

from weather_nlu.activities import split_keywords
from weather_nlu.paths import INTENT_EXAMPLES_PATH, INTENTS_PATH
from weather_nlu.question_info import Intent
from weather_nlu.text import PhraseMatch, PhraseMatcher


@dataclass(frozen=True)
class IntentDefinition:
    id: Intent
    name: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class IntentExample:
    intent: Intent
    text: str


def load_intents(path: Path = INTENTS_PATH) -> list[IntentDefinition]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return [
            IntentDefinition(
                id=Intent(row["id"]),
                name=row["name"],
                keywords=split_keywords(row["keywords"]),
            )
            for row in csv.DictReader(file)
        ]


def load_intent_examples(path: Path = INTENT_EXAMPLES_PATH) -> list[IntentExample]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return [
            IntentExample(intent=Intent(row["intent"]), text=row["text"])
            for row in csv.DictReader(file)
        ]


class IntentKeywordMatcher:
    """Tìm ý định theo từ khóa.

    Thứ tự các intent trong danh sách là thứ tự ưu tiên: khi câu có từ khóa của
    nhiều intent, intent đứng trước thắng. Cùng một intent thì lấy từ khóa xuất
    hiện đầu tiên trong câu.
    """

    def __init__(self, intents: list[IntentDefinition]) -> None:
        self._priority = {intent.id: index for index, intent in enumerate(intents)}
        self._matcher = PhraseMatcher(
            (keyword, intent.id) for intent in intents for keyword in intent.keywords
        )

    def find(self, text: str) -> PhraseMatch[Intent] | None:
        matches = self._matcher.find_all(text)
        return min(matches, key=lambda match: self._priority[match.value], default=None)
