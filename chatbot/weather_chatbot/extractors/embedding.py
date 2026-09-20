import warnings
from datetime import date
from typing import Protocol

import numpy as np

from weather_chatbot.activities import ActivityExample, ActivityKeywordMatcher
from weather_chatbot.locations import LocationMatcher
from weather_chatbot.models import ModelFiles, download_model
from weather_chatbot.question_info import QuestionInfo
from weather_chatbot.time_parser import parse_time


POTION_MODEL = ModelFiles(
    "minishlab/potion-multilingual-128M",
    ("config.json", "model.safetensors", "tokenizer.json"),
)
MINILM_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MINILM_MODEL = ModelFiles("qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q")


class TextEncoder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray: ...


class Model2VecEncoder:
    """Embedding tĩnh: mỗi token có sẵn một vector, câu là trung bình các vector."""

    def __init__(self) -> None:
        from model2vec import StaticModel

        self._model = StaticModel.from_pretrained(str(download_model(POTION_MODEL)))

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self._model.encode(texts))


class MiniLmEncoder:
    """Embedding theo ngữ cảnh bằng mô hình transformer nhỏ, chạy qua ONNX Runtime."""

    def __init__(self) -> None:
        from fastembed import TextEmbedding

        # fastembed cảnh báo đã đổi sang mean pooling. Đây đúng là cách model này
        # được huấn luyện nên bỏ qua cảnh báo.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*mean pooling.*")
            self._model = TextEmbedding(
                MINILM_MODEL_NAME,
                specific_model_path=str(download_model(MINILM_MODEL)),
            )

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray(list(self._model.embed(texts)))


def normalize_rows(vectors: np.ndarray) -> np.ndarray:
    """Chuẩn hóa độ dài vector về 1 để tích vô hướng chính là cosine similarity."""
    lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.maximum(lengths, 1e-12)


class EmbeddingExtractor:
    """Dùng ML để nhận diện hoạt động; địa điểm và thời gian dùng luật.

    Hoạt động được chọn theo câu ví dụ giống câu hỏi nhất (1-nearest neighbor).
    Tên địa điểm được bỏ khỏi câu hỏi trước khi so sánh để không ảnh hưởng kết quả.
    Nếu có keywords, từ khóa được ưu tiên và embedding chỉ dùng khi không khớp từ khóa nào.
    """

    def __init__(
        self,
        name: str,
        encoder: TextEncoder,
        examples: list[ActivityExample],
        locations: LocationMatcher,
        keywords: ActivityKeywordMatcher | None = None,
    ) -> None:
        self.name = name
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
        keyword = self._keywords.find(question) if self._keywords else None
        if keyword is not None:
            return keyword.value
        if location_text:
            question = question.replace(location_text, " ")
        return self.classify_activity(question)

    def extract(self, question: str, today: date) -> QuestionInfo:
        location = self._locations.find(question)
        location_text = location.text if location else None
        return QuestionInfo(
            location_slug=location.value if location else None,
            location_text=location_text,
            time=parse_time(question, today),
            activity_id=self.find_activity(question, location_text),
        )
