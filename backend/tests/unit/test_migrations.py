from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from weather_analysis.database import ALEMBIC_CONFIG_PATH, get_engine


def test_migrations_can_downgrade_and_upgrade(test_database_url: str) -> None:
    config = Config(ALEMBIC_CONFIG_PATH)
    command.downgrade(config, "base")

    assert "users" not in inspect(get_engine()).get_table_names()
    assert "locations" not in inspect(get_engine()).get_table_names()
    assert "system_settings" not in inspect(get_engine()).get_table_names()
    assert "daily_weather" not in inspect(get_engine()).get_table_names()

    command.upgrade(config, "head")
    inspector = inspect(get_engine())

    assert {column["name"] for column in inspector.get_columns("users")} == {
        "id",
        "username",
        "password_hash",
        "created_at",
    }
    assert {column["name"] for column in inspector.get_columns("locations")} == {
        "id",
        "name",
        "slug",
        "region_code",
        "region_label",
        "temp_offset",
        "latitude",
        "longitude",
        "pin_order",
        "aliases",
    }
    assert {
        column["name"]
        for column in inspector.get_columns("system_settings")
    } == {"key", "value", "updated_at"}
    assert {
        column["name"]
        for column in inspector.get_columns("daily_weather")
    } == {
        "latitude",
        "longitude",
        "date",
        "temperature_mean",
        "precipitation_sum",
    }
