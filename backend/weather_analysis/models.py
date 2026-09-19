from datetime import date as Date
from datetime import datetime

from sqlalchemy import Index, String, Unicode, UnicodeText, func, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column

from weather_analysis.database import Base


class User(Base):
    """Tài khoản có thể đăng nhập vào ứng dụng."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(Unicode(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(server_default=func.sysutcdatetime())


class Location(Base):
    """Địa điểm người dùng có thể chọn để xem thời tiết."""

    __tablename__ = "locations"
    __table_args__ = (
        Index(
            "ux_locations_pin_order",
            "pin_order",
            unique=True,
            mssql_where=text("pin_order IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        Unicode(100, collation="Vietnamese_CI_AS"), unique=True
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    region_code: Mapped[str] = mapped_column(String(50))
    region_label: Mapped[str] = mapped_column(Unicode(100))
    temp_offset: Mapped[float]
    latitude: Mapped[float]
    longitude: Mapped[float]
    pin_order: Mapped[int | None]
    aliases: Mapped[str | None] = mapped_column(Unicode(500))


class SystemSetting(Base):
    """Giá trị cài đặt hệ thống đã được quản trị viên thay đổi."""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(UnicodeText)
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME2, server_default=func.sysutcdatetime()
    )


class DailyWeather(Base):
    """Dữ liệu thời tiết lịch sử theo ngày tại một tọa độ."""

    __tablename__ = "daily_weather"

    latitude: Mapped[float] = mapped_column(primary_key=True)
    longitude: Mapped[float] = mapped_column(primary_key=True)
    date: Mapped[Date] = mapped_column(primary_key=True)
    temperature_mean: Mapped[float]
    precipitation_sum: Mapped[float]
