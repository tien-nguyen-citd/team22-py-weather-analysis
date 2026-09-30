from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from weather_analysis.database import acquire_transaction_lock
from weather_analysis.models import Location


class LocationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[Location]:
        return list(self._session.scalars(select(Location).order_by(Location.name)))

    def list_pinned(self) -> list[Location]:
        statement = (
            select(Location)
            .where(Location.pin_order.is_not(None))
            .order_by(Location.pin_order)
        )
        return list(self._session.scalars(statement))

    def find_by_slug(self, slug: str) -> Location | None:
        return self._session.scalar(
            select(Location).where(Location.slug == slug)
        )

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(Location)) or 0

    def replace_all(self, locations: list[Location]) -> None:
        acquire_transaction_lock(self._session, "weather:locations")
        self._session.execute(delete(Location))
        self._session.add_all(locations)
        self._session.flush()
