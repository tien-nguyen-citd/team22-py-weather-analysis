import json
from dataclasses import dataclass

from sqlalchemy.orm import Session

from weather_analysis.repositories.system_setting_repository import (
    SystemSettingRepository,
)


@dataclass(frozen=True)
class SettingDefinition:
    key: str
    category: str
    title: str
    description: str
    default: int
    minimum: int
    maximum: int
    type: str = "integer"


@dataclass(frozen=True)
class SettingState:
    definition: SettingDefinition
    value: int
    is_modified: bool


FORECAST_CACHE_DURATION = SettingDefinition(
    key="forecast.cacheDurationMinutes",
    category="Dự báo thời tiết",
    title="Thời gian lưu cache (phút)",
    description=(
        "Thời gian lưu kết quả dự báo và nhiệt độ hiện tại từ Open-Meteo. "
        "Thay đổi chỉ áp dụng "
        "cho lần gọi Open-Meteo mới, không làm thay đổi thời hạn của dữ liệu "
        "đã có trong cache."
    ),
    default=30,
    minimum=1,
    maximum=1440,
)

SETTING_DEFINITIONS = (FORECAST_CACHE_DURATION,)
_DEFINITIONS_BY_KEY = {
    definition.key: definition for definition in SETTING_DEFINITIONS
}


class SettingNotFoundError(Exception):
    """Không tìm thấy định nghĩa cài đặt theo key."""


class InvalidSettingValueError(Exception):
    """Giá trị cài đặt không đúng kiểu hoặc nằm ngoài phạm vi cho phép."""


def list_settings(session: Session) -> list[SettingState]:
    return [
        _get_setting_state(session, definition)
        for definition in SETTING_DEFINITIONS
    ]


def update_setting(
    session: Session, key: str, value: object
) -> SettingState:
    definition = _get_definition(key)
    validated_value = _validate_value(definition, value)
    repository = SystemSettingRepository(session)

    if validated_value == definition.default:
        repository.delete(key)
        return SettingState(definition, definition.default, False)

    repository.save(key, json.dumps(validated_value))
    return SettingState(definition, validated_value, True)


def reset_setting(session: Session, key: str) -> SettingState:
    definition = _get_definition(key)
    SystemSettingRepository(session).delete(key)
    return SettingState(definition, definition.default, False)


def get_setting_value(
    session: Session, definition: SettingDefinition
) -> int:
    return _get_setting_state(session, definition).value


def _get_setting_state(
    session: Session, definition: SettingDefinition
) -> SettingState:
    record = SystemSettingRepository(session).find_by_key(definition.key)
    if record is None:
        return SettingState(definition, definition.default, False)

    try:
        value = json.loads(record.value)
        validated_value = _validate_value(definition, value)
    except (json.JSONDecodeError, InvalidSettingValueError):
        return SettingState(definition, definition.default, False)

    return SettingState(
        definition,
        validated_value,
        validated_value != definition.default,
    )


def _get_definition(key: str) -> SettingDefinition:
    definition = _DEFINITIONS_BY_KEY.get(key)
    if definition is None:
        raise SettingNotFoundError(key)
    return definition


def _validate_value(definition: SettingDefinition, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidSettingValueError("Giá trị phải là số nguyên")
    if value < definition.minimum or value > definition.maximum:
        raise InvalidSettingValueError(
            f"Giá trị phải từ {definition.minimum} đến {definition.maximum}"
        )
    return value
