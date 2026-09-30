import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session

from weather_analysis.config import (
    build_localdb_url,
    get_data_directory,
    get_database_file_path,
    get_database_name,
    get_database_url,
)


class Base(DeclarativeBase):
    """Lớp cơ sở cho các model ORM."""


_engines: dict[str, Engine] = {}
ALEMBIC_CONFIG_PATH = Path(__file__).resolve().parent.parent / "alembic.ini"


def get_engine() -> Engine:
    """Lấy engine tương ứng với URL cấu hình hiện tại."""
    database_url = get_database_url()
    if database_url not in _engines:
        _engines[database_url] = create_engine(database_url)
    return _engines[database_url]


def _sql_string(value: str) -> str:
    return value.replace("'", "''")


@contextmanager
def session_scope() -> Iterator[Session]:
    """Quản lý vòng đời và giao dịch của một database session."""
    session = Session(get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class TransactionLockError(RuntimeError):
    """Không thể khóa tài nguyên để hoàn tất giao dịch an toàn."""


def acquire_transaction_lock(session: Session, resource: str) -> None:
    """Khóa tài nguyên trên SQL Server cho đến khi transaction commit hoặc rollback."""
    result = session.scalar(
        text(
            """
            SET NOCOUNT ON;
            DECLARE @lock_result int;
            EXEC @lock_result = sys.sp_getapplock
                @Resource = :resource,
                @LockMode = 'Exclusive',
                @LockOwner = 'Transaction',
                @LockTimeout = -1;
            SELECT @lock_result;
            """
        ),
        {"resource": resource},
    )
    if result is None or result < 0:
        raise TransactionLockError(f"Không thể khóa giao dịch {resource}: {result}")


@contextmanager
def database_initialization_lock() -> Iterator[None]:
    """Chỉ một worker được chạy migration và seed tại một thời điểm."""
    with session_scope() as session:
        acquire_transaction_lock(session, "weather:initialize")
        yield


def ensure_database_exists() -> None:
    """Tạo hoặc attach database LocalDB khi dùng cấu hình mặc định."""
    if os.environ.get("WEATHER_DB_URL"):
        return

    database_name = get_database_name()
    if re.fullmatch(r"[A-Za-z0-9_]+", database_name) is None:
        raise ValueError("Tên cơ sở dữ liệu chỉ được chứa chữ, số và dấu gạch dưới")

    data_directory = get_data_directory()
    data_directory.mkdir(parents=True, exist_ok=True)
    database_file = get_database_file_path().resolve()
    log_file = database_file.with_name(f"{database_name}_log.ldf")

    escaped_name = _sql_string(database_name)
    escaped_database_file = _sql_string(str(database_file))
    escaped_log_file = _sql_string(str(log_file))
    if database_file.exists():
        create_statement = (
            f"CREATE DATABASE [{database_name}] "
            f"ON (FILENAME = N'{escaped_database_file}') FOR ATTACH"
        )
    else:
        create_statement = (
            f"CREATE DATABASE [{database_name}] "
            f"ON (NAME = N'{escaped_name}', FILENAME = N'{escaped_database_file}') "
            f"LOG ON (NAME = N'{escaped_name}_log', FILENAME = N'{escaped_log_file}')"
        )

    master_engine = create_engine(
        build_localdb_url("master"), isolation_level="AUTOCOMMIT"
    )
    try:
        with master_engine.connect() as connection:
            lock_resource = f"weather:create-database:{database_name}"
            lock_result = connection.scalar(
                text(
                    """
                    SET NOCOUNT ON;
                    DECLARE @lock_result int;
                    EXEC @lock_result = sys.sp_getapplock
                        @Resource = :resource,
                        @LockMode = 'Exclusive',
                        @LockOwner = 'Session',
                        @LockTimeout = -1;
                    SELECT @lock_result;
                    """
                ),
                {"resource": lock_resource},
            )
            if lock_result is None or lock_result < 0:
                raise TransactionLockError(
                    f"Không thể khóa tạo database {database_name}: {lock_result}"
                )
            try:
                connection.execute(
                    text(
                        f"""
                        IF DB_ID(:database_name) IS NULL
                        BEGIN
                            {create_statement}
                        END
                        """
                    ),
                    {"database_name": database_name},
                )
            finally:
                connection.execute(
                    text(
                        "EXEC sys.sp_releaseapplock "
                        "@Resource = :resource, @LockOwner = 'Session'"
                    ),
                    {"resource": lock_resource},
                )
    finally:
        master_engine.dispose()


def upgrade_database() -> None:
    """Chạy các migration còn thiếu để schema lên phiên bản mới nhất."""
    config = Config(ALEMBIC_CONFIG_PATH)
    command.upgrade(config, "head")
