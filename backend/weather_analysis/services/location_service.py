import unicodedata

from sqlalchemy.orm import Session

from weather_analysis.models import Location
from weather_analysis.repositories.location_repository import LocationRepository


class LocationNotFoundError(Exception):
    """Không tìm thấy địa điểm theo slug."""


def get_location_by_slug(session: Session, slug: str) -> Location:
    location = LocationRepository(session).find_by_slug(slug)
    if location is None:
        raise LocationNotFoundError(slug)
    return location


def normalize_vietnamese(text: str) -> str:
    """Chuẩn hóa chữ thường và bỏ dấu tiếng Việt để tìm kiếm."""
    normalized = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    ).strip()


def search_locations(session: Session, query: str) -> list[Location]:
    """Tìm địa điểm theo tên, vùng hoặc tên gọi khác, không phân biệt dấu."""
    locations = LocationRepository(session).list_all()
    normalized_query = normalize_vietnamese(query)
    if not normalized_query:
        return locations
    matches: list[Location] = []
    for location in locations:
        aliases = (location.aliases or "").split(";")
        if (
            normalized_query in normalize_vietnamese(location.name)
            or normalized_query in normalize_vietnamese(location.region_label)
            or any(
                normalized_query in normalize_vietnamese(alias)
                for alias in aliases
                if alias.strip()
            )
        ):
            matches.append(location)
    return matches


def get_pinned_locations(session: Session) -> list[Location]:
    """Lấy các địa điểm ghim theo thứ tự hiển thị."""
    return LocationRepository(session).list_pinned()
