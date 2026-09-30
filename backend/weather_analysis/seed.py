import csv
from pathlib import Path

from sqlalchemy.orm import Session

from weather_analysis.database import (
    acquire_transaction_lock,
    database_initialization_lock,
    ensure_database_exists,
    session_scope,
    upgrade_database,
)
from weather_analysis.repositories.location_repository import LocationRepository
from weather_analysis.repositories.user_repository import UserRepository
from weather_analysis.security import hash_password
from weather_analysis.services.location_alias_service import import_locations_with_aliases


DEFAULT_USERS_PATH = Path(__file__).resolve().parent.parent / "data" / "seed" / "users.csv"
LOCATIONS_SEED_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "seed" / "locations.csv"
)


def load_users(path: Path) -> list[tuple[str, str]]:
    """Đọc danh sách tài khoản seed từ tệp CSV."""
    users: list[tuple[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            username = row.get("username")
            password = row.get("password")
            if not username or not password:
                raise ValueError("Dữ liệu seed người dùng phải có username và password")
            users.append((username, password))
    return users


def seed_locations(session: Session) -> None:
    """Nạp địa điểm mẫu khi bảng chưa có dữ liệu."""
    acquire_transaction_lock(session, "weather:locations")
    if LocationRepository(session).count() == 0:
        import_locations_with_aliases(session, LOCATIONS_SEED_PATH.read_bytes())


def seed_all(session: Session) -> None:
    """Tạo dữ liệu mẫu theo cách lặp lại an toàn."""
    acquire_transaction_lock(session, "weather:seed")
    user_repository = UserRepository(session)
    for username, password in load_users(DEFAULT_USERS_PATH):
        if user_repository.find_by_username(username) is None:
            user_repository.insert(username, hash_password(password))
    seed_locations(session)


def main() -> None:
    """Khởi tạo schema và dữ liệu mẫu cho cơ sở dữ liệu."""
    ensure_database_exists()
    with database_initialization_lock():
        upgrade_database()
        with session_scope() as session:
            seed_all(session)


if __name__ == "__main__":
    main()
