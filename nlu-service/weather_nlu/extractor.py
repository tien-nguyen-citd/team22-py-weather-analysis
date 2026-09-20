import unicodedata
from datetime import date
from typing import Protocol

import numpy as np

from weather_nlu.activities import ActivityExample, ActivityKeywordMatcher
from weather_nlu.encoder import normalize_rows
from weather_nlu.locations import LocationMatcher
from weather_nlu.question_info import QuestionInfo
from weather_nlu.text import tokenize
from weather_nlu.time_parser import parse_time


class QuestionExtractor(Protocol):
    """Lấy thời gian, địa điểm và hoạt động từ một câu hỏi."""

    name: str

    def extract(self, question: str, today: date) -> QuestionInfo: ...


class TextEncoder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray: ...


class RuleMiniLmExtractor:
    """Dùng từ khóa trước, rồi dùng MiniLM để nhận diện hoạt động.

    Địa điểm được tra theo từ điển và thời gian được đọc bằng các quy tắc tiếng Việt.
    Tên địa điểm được bỏ khỏi câu hỏi trước khi so sánh embedding.
    """

    name = "rule+minilm"

    def __init__(
        self,
        encoder: TextEncoder,
        examples: list[ActivityExample],
        locations: LocationMatcher,
        keywords: ActivityKeywordMatcher,
    ) -> None:
        self._encoder = encoder
        self._locations = locations
        self._keywords = keywords
        self._example_activity_ids = [example.activity_id for example in examples]
        self._example_vectors = normalize_rows(
            encoder.encode([example.text for example in examples])
        )

    def classify_activity(self, text: str) -> str | None:
        question_vector = normalize_rows(self._encoder.encode([text]))[0]
        similarities = self._example_vectors @ question_vector
        return self._example_activity_ids[int(np.argmax(similarities))]

    def find_activity(self, question: str, location_text: str | None) -> str | None:
        question = unicodedata.normalize("NFC", question)
        keyword = self._keywords.find(question)
        if keyword is not None:
            return keyword.value
        if location_text:
            location_text = unicodedata.normalize("NFC", location_text)
            question = question.replace(location_text, " ")
        if not tokenize(question):
            return None
        return self.classify_activity(question)

    def extract(self, question: str, today: date) -> QuestionInfo:
        question = unicodedata.normalize("NFC", question)
        location = self._locations.find(question)
        location_text = location.text if location else None
        return QuestionInfo(
            location_slug=location.value if location else None,
            time=parse_time(question, today),
            activity_id=self.find_activity(question, location_text),
        )
