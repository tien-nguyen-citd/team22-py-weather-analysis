import unicodedata

from weather_chatbot.text import PhraseMatcher, normalize_word, remove_diacritics, tokenize


def test_remove_diacritics_handles_d_with_stroke() -> None:
    assert remove_diacritics("Đà Lạt đẹp") == "Da Lat dep"


def test_normalize_word_unifies_tone_mark_placement() -> None:
    assert normalize_word("Hoà") == normalize_word("hòa")
    assert normalize_word("Thuỷ") == normalize_word("thủy")


def test_tokenize_keeps_positions_in_original_text() -> None:
    text = "Lúc này, Đà Lạt?"
    tokens = tokenize(text)

    assert [token.word for token in tokens] == ["lúc", "này", "đà", "lạt"]
    assert text[tokens[2].start : tokens[3].end] == "Đà Lạt"


def test_token_matches_when_user_types_without_diacritics() -> None:
    expected = tokenize("đang")[0]

    assert tokenize("dang")[0].matches(expected)
    assert not tokenize("đáng")[0].matches(expected)


def test_phrase_matcher_prefers_longer_phrase() -> None:
    matcher = PhraseMatcher([("tuần sau", "next_week"), ("cuối tuần sau", "next_weekend")])

    matches = matcher.find_all("Cuối tuần sau có mưa không?")

    assert [(match.value, match.text) for match in matches] == [("next_weekend", "Cuối tuần sau")]


def test_phrase_matcher_accepts_decomposed_unicode_input() -> None:
    matcher = PhraseMatcher([("Phú Quốc", "phu-quoc")])
    decomposed = unicodedata.normalize("NFD", "Đi Phú Quốc")

    match = matcher.find_first(decomposed)

    assert match is not None
    assert match.value == "phu-quoc"
