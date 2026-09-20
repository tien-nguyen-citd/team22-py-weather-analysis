import pytest

from weather_chatbot.activities import ActivityKeywordMatcher, load_activities
from weather_chatbot.locations import LocationMatcher, load_locations


@pytest.fixture(scope="session")
def location_matcher() -> LocationMatcher:
    return LocationMatcher(load_locations())


@pytest.fixture(scope="session")
def activity_matcher() -> ActivityKeywordMatcher:
    return ActivityKeywordMatcher(load_activities())
