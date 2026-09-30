from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from weather_analysis.database import acquire_transaction_lock
from weather_analysis.models import SystemSetting


class SystemSettingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_key(self, key: str) -> SystemSetting | None:
        return self._session.scalar(
            select(SystemSetting).where(SystemSetting.key == key)
        )

    def save(self, key: str, value: str) -> SystemSetting:
        acquire_transaction_lock(self._session, f"weather:setting:{key}")
        setting = self.find_by_key(key)
        if setting is None:
            setting = SystemSetting(key=key, value=value)
            self._session.add(setting)
        else:
            setting.value = value
            setting.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self._session.flush()
        return setting

    def delete(self, key: str) -> None:
        acquire_transaction_lock(self._session, f"weather:setting:{key}")
        self._session.execute(
            delete(SystemSetting).where(SystemSetting.key == key)
        )
        self._session.flush()
