from datetime import date
from typing import Any

from weather_chatbot.activities import ActivityKeywordMatcher
from weather_chatbot.locations import LocationMatcher
from weather_chatbot.models import ModelFiles, download_model
from weather_chatbot.question_info import QuestionInfo
from weather_chatbot.time_parser import parse_time


GLINER_X_SMALL_MODEL = ModelFiles(
    "knowledgator/gliner-x-small",
    ("*.json", "spiece.model", "onnx/model_quantized.onnx"),
)
GLINER_X_SMALL_ONNX_FILE = "onnx/model_quantized.onnx"
GLINER_MULTI_MODEL = ModelFiles("urchade/gliner_multi-v2.1", ("*.json", "model.safetensors"))
# gliner_multi-v2.1 không kèm tokenizer, thư viện lấy tokenizer từ model gốc mDeBERTa.
MDEBERTA_TOKENIZER = ModelFiles("microsoft/mdeberta-v3-base", ("*.json", "spm.model"))

LOCATION_LABEL = "location"
TIME_LABEL = "time"
ACTIVITY_LABEL = "activity"
ENTITY_LABELS = [LOCATION_LABEL, TIME_LABEL, ACTIVITY_LABEL]
DEFAULT_THRESHOLD = 0.3


def load_gliner_x_small() -> Any:
    from gliner import GLiNER
    from gliner.data_processing.tokenizer import WordsSplitter

    # Model mặc định tách từ bằng stanza (thư viện nặng). Tiếng Việt đã tách âm tiết
    # bằng dấu cách nên chỉ cần tách theo khoảng trắng.
    return GLiNER.from_pretrained(
        str(download_model(GLINER_X_SMALL_MODEL)),
        runtime="onnxruntime",
        runtime_model_file=GLINER_X_SMALL_ONNX_FILE,
        words_splitter=WordsSplitter("whitespace"),
    )


def load_gliner_multi() -> Any:
    from gliner import GLiNER

    download_model(MDEBERTA_TOKENIZER)
    # low_cpu_mem_usage bỏ bước khởi tạo trọng số ngẫu nhiên trước khi nạp,
    # giảm RAM cao nhất khi load từ khoảng 3.5GB xuống dưới 1GB.
    return GLiNER.from_pretrained(
        str(download_model(GLINER_MULTI_MODEL)), low_cpu_mem_usage=True
    )


class GlinerExtractor:
    """Zero-shot NER: model tự tìm cụm địa điểm, thời gian, hoạt động theo tên nhãn.

    Các cụm tìm được sau đó đổi sang slug, TimeSlot và id hoạt động bằng bộ chuẩn hóa chung.
    """

    def __init__(
        self,
        name: str,
        model: Any,
        locations: LocationMatcher,
        activities: ActivityKeywordMatcher,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        self.name = name
        self._model = model
        self._locations = locations
        self._activities = activities
        self._threshold = threshold

    def find_spans(self, question: str) -> dict[str, list[str]]:
        """Trả về các cụm từ tìm được, nhóm theo nhãn."""
        entities = self._model.predict_entities(
            question, ENTITY_LABELS, threshold=self._threshold
        )
        spans: dict[str, list[str]] = {label: [] for label in ENTITY_LABELS}
        for entity in entities:
            spans[entity["label"]].append(entity["text"])
        return spans

    def extract(self, question: str, today: date) -> QuestionInfo:
        spans = self.find_spans(question)
        location_slug, location_text = self._pick_location(spans[LOCATION_LABEL])
        activity = self._activities.find(" ".join(spans[ACTIVITY_LABEL]))
        return QuestionInfo(
            location_slug=location_slug,
            location_text=location_text,
            time=parse_time(" ".join(spans[TIME_LABEL]), today),
            activity_id=activity.value if activity else None,
        )

    def _pick_location(self, location_spans: list[str]) -> tuple[str | None, str | None]:
        """Ưu tiên cụm khớp được địa điểm trong danh sách, nếu không thì giữ cụm đầu tiên."""
        for span in location_spans:
            location = self._locations.find(span)
            if location is not None:
                return location.value, span
        return None, location_spans[0] if location_spans else None
