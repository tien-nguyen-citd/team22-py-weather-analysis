from datetime import date

from weather_chatbot.activities import ActivityKeywordMatcher
from weather_chatbot.locations import LocationMatcher
from weather_chatbot.question_info import QuestionInfo
from weather_chatbot.text import tokenize
from weather_chatbot.time_parser import parse_time


TRAVEL_ACTIVITY_ID = "travel"
# "đi Phú Quốc", "lên Đà Lạt"... ngầm hiểu là đi du lịch.
TRAVEL_VERBS = tokenize("đi lên ra")


class RuleBasedExtractor:
    """Không dùng ML: dùng từ điển địa điểm, từ khóa hoạt động và luật thời gian."""

    name = "rule"

    def __init__(
        self, locations: LocationMatcher, activities: ActivityKeywordMatcher
    ) -> None:
        self._locations = locations
        self._activities = activities

    def extract(self, question: str, today: date) -> QuestionInfo:
        location = self._locations.find(question)
        activity = self._activities.find(question)
        activity_id = activity.value if activity else None

        if activity_id is None and location is not None and location.start > 0:
            word_before_location = tokenize(question)[location.start - 1]
            if any(word_before_location.matches(verb) for verb in TRAVEL_VERBS):
                activity_id = TRAVEL_ACTIVITY_ID

        return QuestionInfo(
            location_slug=location.value if location else None,
            location_text=location.text if location else None,
            time=parse_time(question, today),
            activity_id=activity_id,
        )
