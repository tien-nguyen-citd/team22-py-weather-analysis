import warnings

import numpy as np

from weather_nlu.models import ModelFiles, download_model


MINILM_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MINILM_MODEL = ModelFiles("qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q")


class MiniLmEncoder:
    """Embedding theo ngữ cảnh bằng mô hình transformer chạy qua ONNX Runtime."""

    def __init__(self) -> None:
        from fastembed import TextEmbedding

        # Mean pooling là cách model này được huấn luyện nên có thể bỏ qua cảnh báo.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*mean pooling.*")
            self._model = TextEmbedding(
                MINILM_MODEL_NAME,
                specific_model_path=str(download_model(MINILM_MODEL)),
            )

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.asarray(list(self._model.embed(texts)))


def normalize_rows(vectors: np.ndarray) -> np.ndarray:
    """Chuẩn hóa độ dài vector về 1 để tích vô hướng là cosine similarity."""
    lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.maximum(lengths, 1e-12)
