import pytest

from weather_nlu.activities import (
    ActivityKeywordMatcher,
    load_activities,
    load_activity_examples,
)


def find_activity(matcher: ActivityKeywordMatcher, text: str) -> str | None:
    match = matcher.find(text)
    return match.value if match else None


@pytest.mark.parametrize(
    ("text", "activity_id"),
    [
        ("Đám cưới tháng mấy thì đẹp nhất?", "wedding"),
        ("Sáng mai chạy bộ được không?", "running"),
        ("Hôm nay phơi đồ có khô không?", "drying"),
        ("Cuối tuần tắm biển được không?", "beach"),
        ("Lúc này Đà Lạt có đang mưa không?", None),
    ],
)
def test_find_activity_by_keyword(
    activity_matcher: ActivityKeywordMatcher, text: str, activity_id: str | None
) -> None:
    assert find_activity(activity_matcher, text) == activity_id


def test_first_keyword_in_question_wins(activity_matcher: ActivityKeywordMatcher) -> None:
    assert find_activity(activity_matcher, "Phơi cà phê có nắng không?") == "drying"


def test_activity_examples_only_use_known_activities() -> None:
    activity_ids = {activity.id for activity in load_activities()}
    example_ids = {example.activity_id for example in load_activity_examples()}

    assert example_ids - {None} <= activity_ids
    assert None in example_ids
