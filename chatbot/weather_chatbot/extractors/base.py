from datetime import date
from typing import Protocol

from weather_chatbot.question_info import QuestionInfo


class QuestionExtractor(Protocol):
    """Lấy thời gian, địa điểm và hoạt động từ một câu hỏi."""

    name: str

    def extract(self, question: str, today: date) -> QuestionInfo: ...
