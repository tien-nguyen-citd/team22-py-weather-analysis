import unicodedata
from datetime import date

import numpy as np
import pytest

from weather_nlu.activities import ActivityExample, ActivityKeywordMatcher, load_activities
from weather_nlu.extractor import RuleMiniLmExtractor
from weather_nlu.locations import LocationMatcher, load_locations


class RecordingEncoder:
    def __init__(self) -> None:
        self.encoded_texts: list[str] = []

    def encode(self, texts: list[str]) -> np.ndarray:
        self.encoded_texts.extend(texts)
        return np.ones((len(texts), 2))


@pytest.fixture
def extractor() -> RuleMiniLmExtractor:
    return RuleMiniLmExtractor(
        RecordingEncoder(),
        [ActivityExample(None, "Thời tiết thế nào?")],
        LocationMatcher(load_locations()),
        ActivityKeywordMatcher(load_activities()),
    )


@pytest.mark.parametrize(
    "question",
    [
        "Vũng Tàu",
        unicodedata.normalize("NFD", "Vũng tàu"),
        "Nha Trang?",
        "Hà Nội!",
    ],
)
def test_location_only_has_no_explicit_activity(
    extractor: RuleMiniLmExtractor, question: str
) -> None:
    result = extractor.extract(question, date(2026, 9, 20))

    assert result.location_slug is not None
    assert result.activity_id is None


def test_explicit_activity_wins_for_location(
    extractor: RuleMiniLmExtractor,
) -> None:
    result = extractor.extract("Uống cafe ở Vũng Tàu", date(2026, 9, 20))

    assert result.location_slug == "vung-tau"
    assert result.activity_id == "coffee"
