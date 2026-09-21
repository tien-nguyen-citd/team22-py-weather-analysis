import unicodedata
from datetime import date
from typing import Protocol

import numpy as np

from weather_nlu.activities import ActivityExample, ActivityKeywordMatcher
from weather_nlu.encoder import normalize_rows
from weather_nlu.intents import IntentExample, IntentKeywordMatcher
from weather_nlu.locations import LocationMatcher
from weather_nlu.question_info import Intent, QuestionInfo, TimeKind, TimeSlot
from weather_nlu.text import tokenize
from weather_nlu.time_parser import parse_time


class QuestionExtractor(Protocol):
    """Lấy thời gian, địa điểm, hoạt động và ý định từ một câu hỏi."""

    name: str

    def extract(self, question: str, today: date) -> QuestionInfo: ...


class TextEncoder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray: ...


class QuestionVector:
    """Vector embedding của câu hỏi, chỉ encode ở lần đầu cần dùng.

    Hoạt động và ý định cùng dùng một vector nên mỗi câu hỏi encode tối đa một lần.
    """

    def __init__(self, encoder: TextEncoder, text: str) -> None:
        self._encoder = encoder
        self.text = text
        self._vector: np.ndarray | None = None

    @property
    def has_words(self) -> bool:
        return bool(tokenize(self.text))

    def get(self) -> np.ndarray:
        vector = self._vector
        if vector is None:
            vector = normalize_rows(self._encoder.encode([self.text]))[0]
            self._vector = vector
        return vector


class NearestExampleClassifier[T]:
    """Gán cho câu hỏi nhãn của câu mẫu gần nghĩa nhất (1-NN theo cosine similarity)."""

    def __init__(self, encoder: TextEncoder, labels: list[T], texts: list[str]) -> None:
        self._labels = labels
        self._vectors = normalize_rows(encoder.encode(texts))

    def classify(self, question_vector: np.ndarray) -> T:
        similarities = self._vectors @ question_vector
        return self._labels[int(np.argmax(similarities))]


def remove_location(question: str, location_text: str | None) -> str:
    """Bỏ tên địa điểm khỏi câu để embedding tập trung vào phần còn lại."""
    if not location_text:
        return question
    return question.replace(unicodedata.normalize("NFC", location_text), " ")


class RuleMiniLmExtractor:
    """Dùng từ khóa trước, rồi dùng MiniLM để nhận diện hoạt động và ý định.

    Địa điểm được tra theo từ điển và thời gian được đọc bằng các quy tắc tiếng Việt.
    Tên địa điểm được bỏ khỏi câu hỏi trước khi so sánh embedding.

    Ý định được xác định theo thứ tự: câu nêu địa điểm trong danh mục là tìm thời điểm,
    có từ khóa ý định thì theo từ khóa, hỏi thời điểm tốt nhất là tìm thời điểm,
    còn lại lấy nhãn của câu mẫu gần nhất.
    """

    name = "rule+minilm"

    def __init__(
        self,
        encoder: TextEncoder,
        examples: list[ActivityExample],
        locations: LocationMatcher,
        keywords: ActivityKeywordMatcher,
        intents: IntentKeywordMatcher,
        intent_examples: list[IntentExample],
    ) -> None:
        self._encoder = encoder
        self._locations = locations
        self._keywords = keywords
        self._intents = intents
        self._activity_classifier = NearestExampleClassifier(
            encoder,
            [example.activity_id for example in examples],
            [example.text for example in examples],
        )
        self._intent_classifier = NearestExampleClassifier(
            encoder,
            [example.intent for example in intent_examples],
            [example.text for example in intent_examples],
        )

    def find_activity(self, question: str, vector: QuestionVector) -> str | None:
        keyword = self._keywords.find(question)
        if keyword is not None:
            return keyword.value
        if not vector.has_words:
            return None
        return self._activity_classifier.classify(vector.get())

    def find_intent(
        self,
        question: str,
        has_location: bool,
        time: TimeSlot | None,
        vector: QuestionVector,
    ) -> Intent:
        if has_location:
            return Intent.FIND_TIME
        keyword = self._intents.find(question)
        if keyword is not None:
            return keyword.value
        if time is not None and time.kind == TimeKind.BEST_TIME:
            return Intent.FIND_TIME
        if not vector.has_words:
            return Intent.FIND_TIME
        return self._intent_classifier.classify(vector.get())

    def extract(self, question: str, today: date) -> QuestionInfo:
        question = unicodedata.normalize("NFC", question)
        location = self._locations.find(question)
        time = parse_time(question, today)
        vector = QuestionVector(
            self._encoder, remove_location(question, location.text if location else None)
        )
        return QuestionInfo(
            location_slug=location.value if location else None,
            time=time,
            activity_id=self.find_activity(question, vector),
            intent=self.find_intent(question, location is not None, time, vector),
        )
