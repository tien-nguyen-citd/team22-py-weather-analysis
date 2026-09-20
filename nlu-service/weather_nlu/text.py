import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass


# Một số từ có hai cách đặt dấu thanh (hoà/hòa, thuỷ/thủy).
# Đưa về cùng một cách để so khớp không phụ thuộc thói quen gõ.
TONE_MARK_VARIANTS = {
    "oà": "òa",
    "oá": "óa",
    "oả": "ỏa",
    "oã": "õa",
    "oạ": "ọa",
    "oè": "òe",
    "oé": "óe",
    "oẻ": "ỏe",
    "oẽ": "õe",
    "oẹ": "ọe",
    "uỳ": "ùy",
    "uý": "úy",
    "uỷ": "ủy",
    "uỹ": "ũy",
    "uỵ": "ụy",
}
WORD_PATTERN = re.compile(r"\w+")


def remove_diacritics(text: str) -> str:
    """Bỏ dấu tiếng Việt, đổi đ/Đ thành d/D."""
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize_word(word: str) -> str:
    """Đưa một từ về chữ thường và cùng một cách đặt dấu thanh."""
    word = unicodedata.normalize("NFC", word).casefold()
    for variant, standard in TONE_MARK_VARIANTS.items():
        word = word.replace(variant, standard)
    return word


@dataclass(frozen=True)
class Token:
    word: str  # từ đã chuẩn hóa, còn dấu
    plain: str  # từ đã bỏ dấu
    start: int  # vị trí ký tự đầu trong câu (dạng NFC)
    end: int  # vị trí sau ký tự cuối trong câu (dạng NFC)

    @property
    def has_diacritics(self) -> bool:
        return self.word != self.plain

    def matches(self, expected: "Token") -> bool:
        """So khớp đúng dấu, hoặc bỏ qua dấu khi người dùng gõ không dấu.

        Nhờ vậy "da lat" khớp với "Đà Lạt", nhưng "đáng" không khớp với "đang".
        """
        if self.word == expected.word:
            return True
        return not self.has_diacritics and self.plain == expected.plain


def tokenize(text: str) -> list[Token]:
    """Tách câu thành các từ, giữ vị trí để cắt lại đoạn gốc."""
    text = unicodedata.normalize("NFC", text)
    tokens: list[Token] = []
    for match in WORD_PATTERN.finditer(text):
        word = normalize_word(match.group())
        tokens.append(Token(word, remove_diacritics(word), match.start(), match.end()))
    return tokens


@dataclass(frozen=True)
class PhraseMatch[T]:
    value: T
    text: str  # đoạn khớp trong câu
    start: int  # chỉ số token đầu tiên
    end: int  # chỉ số sau token cuối cùng


class PhraseMatcher[T]:
    """Tìm các cụm từ đã biết trong câu, ưu tiên cụm dài hơn."""

    def __init__(self, phrases: Iterable[tuple[str, T]]) -> None:
        self._phrases = [
            (phrase_tokens, value)
            for phrase, value in phrases
            if (phrase_tokens := tokenize(phrase))
        ]
        self._phrases.sort(key=lambda item: len(item[0]), reverse=True)

    def find_all(self, text: str) -> list[PhraseMatch[T]]:
        """Trả về các cụm từ không chồng lên nhau, theo thứ tự xuất hiện."""
        text = unicodedata.normalize("NFC", text)
        tokens = tokenize(text)
        used = [False] * len(tokens)
        matches: list[PhraseMatch[T]] = []
        for phrase_tokens, value in self._phrases:
            size = len(phrase_tokens)
            for start in range(len(tokens) - size + 1):
                end = start + size
                if any(used[start:end]):
                    continue
                if all(
                    tokens[start + offset].matches(phrase_token)
                    for offset, phrase_token in enumerate(phrase_tokens)
                ):
                    used[start:end] = [True] * size
                    matched_text = text[tokens[start].start : tokens[end - 1].end]
                    matches.append(PhraseMatch(value, matched_text, start, end))
        return sorted(matches, key=lambda match: match.start)

    def find_first(self, text: str) -> PhraseMatch[T] | None:
        matches = self.find_all(text)
        return matches[0] if matches else None
