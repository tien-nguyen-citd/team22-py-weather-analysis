from pathlib import Path
from typing import Protocol, cast
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from weather_analysis import database
from weather_analysis.api.dependencies import DbSession


class _Poster(Protocol):
    def post(self, url: str) -> Response: ...


def test_session_scope_commits_success_and_rolls_back_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'transactions.db'}")
    monkeypatch.setattr(database, "get_engine", lambda: engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE values_for_test (value INTEGER)"))

    with database.session_scope() as session:
        session.execute(text("INSERT INTO values_for_test (value) VALUES (1)"))

    with pytest.raises(RuntimeError, match="thất bại"):
        with database.session_scope() as session:
            session.execute(text("INSERT INTO values_for_test (value) VALUES (2)"))
            raise RuntimeError("thất bại")

    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM values_for_test")) == 1
    engine.dispose()


def test_transaction_lock_checks_sql_server_result() -> None:
    with Session() as session, patch.object(Session, "scalar", return_value=1) as scalar:
        database.acquire_transaction_lock(session, "weather:locations")

    statement, parameters = scalar.call_args.args
    assert "sp_getapplock" in statement.text
    assert "@LockOwner = 'Transaction'" in statement.text
    assert parameters == {"resource": "weather:locations"}


def test_transaction_lock_rejects_failed_acquisition() -> None:
    with Session() as session, patch.object(Session, "scalar", return_value=-3):
        with pytest.raises(database.TransactionLockError, match="weather:seed"):
            database.acquire_transaction_lock(session, "weather:seed")


def test_api_does_not_send_success_when_commit_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'api-transactions.db'}")
    monkeypatch.setattr(database, "get_engine", lambda: engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE values_for_test (value INTEGER)"))

    app = FastAPI()

    def write_value(session: DbSession) -> dict[str, bool]:
        session.execute(text("INSERT INTO values_for_test (value) VALUES (1)"))
        return {"saved": True}

    app.add_api_route("/write", write_value, methods=["POST"])
    with patch.object(Session, "commit", side_effect=RuntimeError("commit failed")):
        with TestClient(app, raise_server_exceptions=False) as client:
            response = cast(_Poster, client).post("/write")

    assert response.status_code == 500
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM values_for_test")) == 0
    engine.dispose()
