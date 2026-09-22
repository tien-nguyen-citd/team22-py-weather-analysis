import unicodedata
from collections import Counter
from datetime import date
from typing import Protocol

import numpy as np

from weather_nlu.activities import (
    ActivityExample,
    ActivityKeywordMatcher,
    load_activities,
    load_activity_examples,
)
from weather_nlu.encoder import MiniLmEncoder, normalize_rows
from weather_nlu.intents import (
    IntentExample,
    IntentKeywordMatcher,
    load_intent_examples,
    load_intents,
)
from weather_nlu.locations import LocationMatcher, load_locations
from weather_nlu.question_info import Intent, QuestionInfo, TimeKind, TimeSlot
from weather_nlu.text import remove_diacritics, tokenize
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


DEFAULT_NEIGHBOR_COUNT = 3


class NearestExampleClassifier[T]:
    """Gán nhãn cho câu hỏi theo k câu mẫu gần nghĩa nhất (k-NN theo cosine similarity).

    k câu mẫu gần nhất bỏ phiếu cho nhãn của mình. Khi hòa phiếu, nhãn của câu mẫu
    gần nhất thắng. Mỗi câu mẫu được thêm một bản không dấu để nhận ra câu hỏi
    gõ không dấu.
    """

    def __init__(
        self,
        encoder: TextEncoder,
        labels: list[T],
        texts: list[str],
        k: int = DEFAULT_NEIGHBOR_COUNT,
    ) -> None:
        self._labels = labels + labels
        self._vectors = normalize_rows(
            encoder.encode(texts + [remove_diacritics(text) for text in texts])
        )
        self._k = k

    def classify(self, question_vector: np.ndarray) -> T:
        similarities = self._vectors @ question_vector
        nearest = np.argsort(-similarities)[: self._k]
        labels = [self._labels[int(index)] for index in nearest]
        votes = Counter(labels)
        most_votes = max(votes.values())
        return next(label for label in labels if votes[label] == most_votes)


def remove_phrases(question: str, phrases: list[str]) -> str:
    """Bỏ các cụm từ đã nhận ra để embedding tập trung vào phần còn lại của câu."""
    for phrase in phrases:
        question = question.replace(unicodedata.normalize("NFC", phrase), " ")
    return question


class RuleMiniLmExtractor:
    """Dùng từ khóa trước, rồi dùng MiniLM để nhận diện hoạt động và ý định.

    Địa điểm được tra theo từ điển và thời gian được đọc bằng các quy tắc tiếng Việt.
    Tên địa điểm và các cụm từ khóa hoạt động được bỏ khỏi câu hỏi trước khi so sánh
    embedding. Nhờ vậy MiniLM tập trung vào dạng câu hỏi thay vì chủ đề của câu.

    Ý định được xác định theo thứ tự: câu nêu địa điểm trong danh mục là tìm thời điểm,
    có từ khóa ý định thì theo từ khóa, hỏi thời điểm tốt nhất là tìm thời điểm,
    còn lại bỏ phiếu theo các câu mẫu gần nhất.
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
        # Hoạt động chỉ dùng embedding khi câu không có từ khóa hoạt động, còn ý định
        # chỉ dùng khi câu không có địa điểm. Vì vậy bỏ cả hai loại cụm từ vẫn đúng
        # cho cả hai việc và mỗi câu hỏi chỉ cần encode tối đa một lần.
        known_phrases = [match.text for match in self._keywords.find_all(question)]
        if location is not None:
            known_phrases.append(location.text)
        vector = QuestionVector(self._encoder, remove_phrases(question, known_phrases))
        return QuestionInfo(
            location_slug=location.value if location else None,
            time=time,
            activity_id=self.find_activity(question, vector),
            intent=self.find_intent(question, location is not None, time, vector),
        )


def build_rule_minilm_extractor() -> RuleMiniLmExtractor:
    """Tạo bộ đọc câu hỏi với MiniLM và dữ liệu trong thư mục data."""
    return RuleMiniLmExtractor(
        MiniLmEncoder(),
        load_activity_examples(),
        LocationMatcher(load_locations()),
        ActivityKeywordMatcher(load_activities()),
        IntentKeywordMatcher(load_intents()),
        load_intent_examples(),
    )
