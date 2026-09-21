from collections.abc import Iterator
from datetime import date

from httpx import Client
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tests.advisory_helpers import FakeArchiveClient
from weather_analysis.advisory import destinations
from weather_analysis.advisory.destinations import Destination
from weather_analysis.api.advisory_routes import get_advisory_today
from weather_analysis.api.app import app
from weather_analysis.api.dependencies import get_open_meteo_client
from weather_analysis.models import DailyWeather


@pytest.fixture(autouse=True)
def archive_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeArchiveClient]:
    monkeypatch.setattr(
        destinations,
        "DESTINATIONS",
        (
            Destination("ha-noi", False),
            Destination("da-nang", True),
            Destination("phu-quoc", True),
        ),
    )
    fake = FakeArchiveClient()
    overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_open_meteo_client] = lambda: fake
    app.dependency_overrides[get_advisory_today] = lambda: date(2026, 9, 20)
    try:
        yield fake
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides)


def test_defaults_return_general_ranking_for_next_month_and_reuses_history(
    client: Client, archive_client: FakeArchiveClient
) -> None:
    response = client.post("/api/advisory/destinations", json={})
    repeated = client.post("/api/advisory/destinations", json={})

    assert response.status_code == repeated.status_code == 200
    body = response.json()
    assert body == repeated.json()
    assert len(archive_client.calls) == 3
    assert body["month"] == "2026-10"
    assert body["activity"]["id"] == "general"
    assert {item["location"]["slug"] for item in body["destinations"]} == {
        "ha-noi",
        "da-nang",
        "phu-quoc",
    }
    assert isinstance(body["summary"], str)
    assert body["lowSuitability"] is False
    assert any("không phải dự báo" in note for note in body["notes"])


def test_beach_activity_only_returns_coastal_destinations(
    client: Client, archive_client: FakeArchiveClient
) -> None:
    response = client.post("/api/advisory/destinations", json={"activityId": "beach"})

    assert response.status_code == 200
    slugs = {item["location"]["slug"] for item in response.json()["destinations"]}
    assert slugs == {"da-nang", "phu-quoc"}


@pytest.mark.parametrize(
    "payload",
    [
        {"month": "2026-13"},
        {"month": "2026-1"},
        {"activityId": "unknown"},
        {"unexpected": True},
        {"month": 12},
    ],
)
def test_invalid_input_returns_vietnamese_error_without_fetching(
    client: Client,
    archive_client: FakeArchiveClient,
    payload: dict[str, object],
) -> None:
    response = client.post("/api/advisory/destinations", json=payload)

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)
    assert archive_client.calls == []


def test_provider_error_returns_502_and_leaves_no_partial_data(
    client: Client, archive_client: FakeArchiveClient, session: Session
) -> None:
    archive_client.fail = True

    response = client.post("/api/advisory/destinations", json={})

    assert response.status_code == 502
    assert isinstance(response.json()["detail"], str)
    assert session.scalar(select(func.count()).select_from(DailyWeather)) == 0


def test_openapi_exposes_destinations_path(client: Client) -> None:
    schema = client.get("/openapi.json").json()

    assert "/api/advisory/destinations" in schema["paths"]
