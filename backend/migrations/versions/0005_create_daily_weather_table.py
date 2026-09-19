"""Thêm bảng dữ liệu thời tiết lịch sử theo ngày."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "daily_weather",
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("temperature_mean", sa.Float(), nullable=False),
        sa.Column("precipitation_sum", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("latitude", "longitude", "date"),
    )


def downgrade() -> None:
    op.drop_table("daily_weather")
