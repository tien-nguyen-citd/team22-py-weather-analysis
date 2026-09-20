import csv
from dataclasses import dataclass
from pathlib import Path

from weather_nlu.paths import LOCATION_ALIASES_PATH, LOCATIONS_PATH
from weather_nlu.text import PhraseMatch, PhraseMatcher, tokenize


@dataclass(frozen=True)
class Location:
    slug: str
    name: str
    aliases: tuple[str, ...]


def load_locations(
    locations_path: Path = LOCATIONS_PATH,
    aliases_path: Path = LOCATION_ALIASES_PATH,
) -> list[Location]:
    """Đọc danh sách địa điểm và tên gọi khác từ dữ liệu mẫu của backend."""
    aliases_by_slug: dict[str, list[str]] = {}
    with aliases_path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            aliases_by_slug.setdefault(row["slug"], []).append(row["alias"])

    with locations_path.open(encoding="utf-8-sig", newline="") as file:
        return [
            Location(
                slug=row["slug"],
                name=row["name"],
                aliases=tuple(aliases_by_slug.get(row["slug"], [])),
            )
            for row in csv.DictReader(file)
        ]


def build_location_phrases(location: Location) -> list[str]:
    """Liệt kê các cách viết của một địa điểm, kể cả kiểu viết liền "dalat"."""
    phrases: list[str] = []
    for name in (location.name, *location.aliases):
        phrases.append(name)
        words = [token.plain for token in tokenize(name)]
        if len(words) > 1:
            phrases.append("".join(words))
    return phrases


class LocationMatcher:
    """Tìm địa điểm có trong danh sách bằng cách so khớp tên và tên gọi khác."""

    def __init__(self, locations: list[Location]) -> None:
        self._matcher = PhraseMatcher(
            (phrase, location.slug)
            for location in locations
            for phrase in build_location_phrases(location)
        )

    def find(self, text: str) -> PhraseMatch[str] | None:
        """Trả về địa điểm xuất hiện đầu tiên, value là slug."""
        return self._matcher.find_first(text)
