import json
import re
from datetime import date
from typing import Any

from weather_chatbot.activities import Activity
from weather_chatbot.locations import LocationMatcher
from weather_chatbot.models import ModelFiles, download_model
from weather_chatbot.question_info import QuestionInfo
from weather_chatbot.time_parser import parse_time


QWEN_MODEL = ModelFiles(
    "Qwen/Qwen2.5-0.5B-Instruct",
    ("*.json", "model.safetensors", "merges.txt"),
)
MAX_NEW_TOKENS = 64
JSON_PATTERN = re.compile(r"\{.*\}", re.DOTALL)

SYSTEM_PROMPT = """Bạn trích xuất thông tin từ câu hỏi về thời tiết bằng tiếng Việt.
Trả về đúng một đối tượng JSON gồm 3 khóa:
- "location": tên địa danh được nhắc tới, viết đầy đủ có dấu (ví dụ "SG" thành "Sài Gòn"). Dùng null nếu không có.
- "time": cụm từ chỉ thời gian, chép nguyên văn từ câu hỏi. Dùng null nếu không có.
- "activity": một mã hoạt động trong danh sách dưới đây. Dùng null nếu câu hỏi không nói tới hoạt động nào.
Danh sách mã hoạt động:
{activities}
Chỉ trả về JSON, không giải thích."""

# Ví dụ mẫu cho model, không trùng với bộ câu hỏi đánh giá.
FEW_SHOT_EXAMPLES = [
    (
        "Tối mai làm tiệc cưới ở sân vườn tại Pleiku có mưa không?",
        {"location": "Pleiku", "time": "Tối mai", "activity": "wedding"},
    ),
    (
        "Hiện giờ ở Hải Phòng trời có oi không?",
        {"location": "Hải Phòng", "time": "Hiện giờ", "activity": None},
    ),
    (
        "Tháng mấy đi Kon Tum ngắm hoa dã quỳ là đẹp nhất?",
        {"location": "Kon Tum", "time": "Tháng mấy", "activity": "travel"},
    ),
]


def build_messages(question: str, activities: list[Activity]) -> list[dict[str, str]]:
    activity_lines = "\n".join(f"- {activity.id}: {activity.name}" for activity in activities)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(activities=activity_lines)}
    ]
    for example_question, example_answer in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": example_question})
        messages.append(
            {"role": "assistant", "content": json.dumps(example_answer, ensure_ascii=False)}
        )
    messages.append({"role": "user", "content": question})
    return messages


def parse_answer(answer: str) -> dict[str, Any]:
    """Lấy đối tượng JSON trong câu trả lời, trả về dict rỗng nếu model trả sai định dạng."""
    match = JSON_PATTERN.search(answer)
    if match is None:
        return {}
    try:
        parsed = json.loads(match.group())
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def as_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


class SmallLlmExtractor:
    """Mô hình ngôn ngữ nhỏ đọc câu hỏi và trả về JSON gồm 3 thông tin."""

    name = "qwen-0.5b"

    def __init__(self, locations: LocationMatcher, activities: list[Activity]) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_dir = download_model(QWEN_MODEL)
        self._torch = torch
        self._tokenizer = AutoTokenizer.from_pretrained(model_dir)
        # bfloat16 tốn ít RAM hơn nhưng chạy trên CPU chậm hơn float32 khoảng 2-3 lần.
        self._model: Any = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.float32)
        self._model.eval()
        self._locations = locations
        self._activities = activities
        self._activity_ids = {activity.id for activity in activities}

    def ask(self, question: str) -> str:
        """Trả về câu trả lời thô của model."""
        inputs = self._tokenizer.apply_chat_template(
            build_messages(question, self._activities),
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        )
        with self._torch.no_grad():
            output = self._model.generate(
                **inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False
            )
        prompt_length = inputs["input_ids"].shape[1]
        return self._tokenizer.decode(output[0][prompt_length:], skip_special_tokens=True)

    def extract(self, question: str, today: date) -> QuestionInfo:
        answer = parse_answer(self.ask(question))
        location_text = as_text(answer.get("location"))
        location = self._locations.find(location_text) if location_text else None
        time_text = as_text(answer.get("time"))
        activity_id = as_text(answer.get("activity"))
        return QuestionInfo(
            location_slug=location.value if location else None,
            location_text=location_text,
            time=parse_time(time_text, today) if time_text else None,
            activity_id=activity_id if activity_id in self._activity_ids else None,
        )
