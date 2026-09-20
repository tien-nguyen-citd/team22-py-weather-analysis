import pytest

from weather_chatbot.evaluation import load_questions, run_extractor, summarize
from weather_chatbot.extractors.factory import EXTRACTORS
from weather_chatbot.models import find_downloaded_model


# Ngưỡng thấp hơn kết quả đo được khoảng 5 điểm để phát hiện khi thay đổi làm giảm chất lượng.
# qwen-0.5b mất khoảng 12 phút để chạy hết bộ câu hỏi trên CPU nên không đưa vào test.
MINIMUM_ALL_ACCURACY = {
    "model2vec": 0.65,
    "minilm": 0.53,
    "rule+model2vec": 0.75,
    "rule+minilm": 0.72,
    "gliner-x-small": 0.05,
    "gliner-multi": 0.45,
}


@pytest.mark.model
@pytest.mark.parametrize("name", list(MINIMUM_ALL_ACCURACY))
def test_extractor_accuracy(name: str) -> None:
    spec = EXTRACTORS[name]
    if any(find_downloaded_model(model) is None for model in spec.models):
        pytest.skip(
            f"Chưa tải model, chạy python -m weather_chatbot.evaluate --extractor {name}"
        )

    summary = summarize(name, run_extractor(spec.create(), load_questions()))

    assert summary.all_accuracy >= MINIMUM_ALL_ACCURACY[name]
