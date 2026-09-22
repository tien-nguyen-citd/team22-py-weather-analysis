import pytest

from weather_nlu.locations import Location, LocationMatcher, build_location_phrases


def find_slug(matcher: LocationMatcher, text: str) -> str | None:
    match = matcher.find(text)
    return match.value if match else None


@pytest.mark.parametrize(
    ("text", "slug"),
    [
        ("Lúc này Đà Lạt có mưa không?", "da-lat"),
        ("da lat co mua khong", "da-lat"),
        ("dalat co lanh khong", "da-lat"),
        ("HCM hôm nay nóng không?", "ho-chi-minh"),
        ("TP.HCM hôm nay nóng không?", "ho-chi-minh"),
        ("Thời tiết Sài Gòn thế nào?", "ho-chi-minh"),
        ("SG chiều nay có mưa không?", "ho-chi-minh"),
        ("Sài Thành cuối tuần này có nắng không?", "ho-chi-minh"),
        ("Thủ đô hôm nay có mưa không?", "ha-noi"),
        ("ĐL tháng này đi chơi được không?", "da-lat"),
        ("Tháng sau ra đảo ngọc chơi có mưa không?", "phu-quoc"),
        ("Biên Hòa có mưa không?", "bien-hoa"),
        ("Thanh Hóa có mưa không?", "thanh-hoa"),
        ("Bà Rịa Vũng Tàu có bão không?", "ba-ria-vung-tau"),
        ("Vũng Tàu có bão không?", "vung-tau"),
    ],
)
def test_find_location(location_matcher: LocationMatcher, text: str, slug: str) -> None:
    assert find_slug(location_matcher, text) == slug


def test_accented_word_does_not_match_other_location(location_matcher: LocationMatcher) -> None:
    assert find_slug(location_matcher, "Vịnh Hạ Long có đẹp không?") is None


def test_find_returns_original_text(location_matcher: LocationMatcher) -> None:
    match = location_matcher.find("Mai đi Phu Quoc nhé")

    assert match is not None
    assert match.text == "Phu Quoc"


def test_build_location_phrases_adds_joined_spelling() -> None:
    location = Location(slug="da-lat", name="Đà Lạt", aliases=("ĐL",))

    assert build_location_phrases(location) == ["Đà Lạt", "dalat", "ĐL"]
