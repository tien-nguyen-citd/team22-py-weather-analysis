from collections.abc import Iterator
from datetime import date

from httpx import Client
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tests.advisory_helpers import FakeArchiveClient
from weather_analysis.api.advisory_routes import get_advisory_today
from weather_analysis.api.app import app
from weather_analysis.api.dependencies import get_open_meteo_client
from weather_analysis.models import DailyWeather


@pytest.fixture(autouse=True)
def archive_client() -> Iterator[FakeArchiveClient]:
    fake = FakeArchiveClient()
    overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_open_meteo_client] = lambda: fake
    app.dependency_overrides[get_advisory_today] = lambda: date(2026, 9, 20)
    try:
        yield fake
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides)


def test_activities_catalog_does_not_call_weather_provider(
    client: Client, archive_client: FakeArchiveClient
) -> None:
    response = client.get("/api/advisory/activities")
    assert response.status_code == 200
    profiles = {profile["id"]: profile for profile in response.json()}
    assert set(profiles) == {
        "general",
        "travel",
        "wedding",
        "running",
        "photography",
        "coffee",
        "beach",
        "camping",
        "drying",
    }
    assert profiles["wedding"]["rainWeight"] == 0.8
    assert profiles["drying"]["temperatureMin"] is None
    assert profiles["drying"]["rainThresholdMm"] == 1
    assert archive_client.calls == []


def test_advice_returns_explained_candidates_and_reuses_history(
    client: Client, archive_client: FakeArchiveClient
) -> None:
    payload = {
        "locationSlug": "ha-noi",
        "time": {"startMonth": "2027-01", "endMonth": "2027-03"},
        "activityId": "wedding",
        "topK": 1,
    }
    response = client.post("/api/advisory", json=payload)
    repeated = client.post("/api/advisory", json=payload)
    assert response.status_code == repeated.status_code == 200
    body = response.json()
    assert body == repeated.json()
    assert len(archive_client.calls) == 1
    assert body["request"] == payload
    assert body["baselineStart"] == "2015-09-01"
    assert body["baselineEnd"] == "2025-08-31"
    assert len(body["recommendations"]) == 1
    assert len(body["candidates"]) == 3
    best = body["recommendations"][0]
    assert best["window"]["startDate"] == "2027-01-01"
    assert best["window"]["resolution"] == "month"
    assert best["rainContribution"] == 80
    assert best["temperatureContribution"] == 20
    assert best["score"] == 100
    assert best["sampleYears"] == 10
    assert "Tổng 100.0/100" in best["explanation"]
    assert body["lowSuitability"] is False
    assert any("không phải dự báo" in note for note in body["notes"])


def test_defaults_and_short_month_range(client: Client) -> None:
    response = client.post("/api/advisory", json={"locationSlug": "ha-noi"})
    assert response.status_code == 200
    body = response.json()
    assert body["request"]["time"] == {"startMonth": "2026-10", "endMonth": "2027-09"}
    assert body["request"]["activityId"] == "general"
    assert len(body["recommendations"]) == 3
    assert len(body["candidates"]) == 12
    short = client.post(
        "/api/advisory",
        json={
            "locationSlug": "ha-noi",
            "activityId": "drying",
            "time": {"startMonth": "2028-02", "endMonth": "2028-02"},
        },
    )
    assert short.status_code == 200
    last = short.json()["candidates"][-1]
    assert last["window"]["endDate"] == "2028-02-29"
    assert last["sampleDays"] == 80
    assert last["temperatureScore"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"locationSlug": " "},
        {"locationSlug": 123},
        {"locationSlug": "ha-noi", "activityId": "unknown"},
        {"locationSlug": "ha-noi", "time": {"startMonth": "2027-01"}},
        {
            "locationSlug": "ha-noi",
            "time": {"startMonth": "2027-13", "endMonth": "2027-12"},
        },
        {
            "locationSlug": "ha-noi",
            "time": {"startMonth": "2027-1", "endMonth": "2027-12"},
        },
        {
            "locationSlug": "ha-noi",
            "time": {"startMonth": "2027-01", "endMonth": "2028-01"},
        },
        {
            "locationSlug": "ha-noi",
            "time": {"startMonth": "2027-02", "endMonth": "2027-01"},
        },
        {"locationSlug": "ha-noi", "topK": 4},
        {"locationSlug": "ha-noi", "topK": True},
        {"locationSlug": "ha-noi", "topK": 1.5},
        {"locationSlug": "ha-noi", "topK": "1"},
        {"locationSlug": "ha-noi", "unexpected": True},
    ],
)
def test_invalid_input_returns_vietnamese_error_without_fetching(
    client: Client,
    archive_client: FakeArchiveClient,
    payload: dict[str, object],
) -> None:
    response = client.post("/api/advisory", json=payload)
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)
    assert archive_client.calls == []


def test_unknown_location_returns_404_without_fetching(
    client: Client, archive_client: FakeArchiveClient
) -> None:
    response = client.post("/api/advisory", json={"locationSlug": "khong-ton-tai"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Không tìm thấy địa điểm"
    assert archive_client.calls == []


@pytest.mark.parametrize("problem", ["provider", "incomplete", "missing_value"])
def test_history_errors_return_502_and_do_not_leave_partial_data(
    client: Client,
    archive_client: FakeArchiveClient,
    session: Session,
    problem: str,
) -> None:
    archive_client.fail = problem == "provider"
    archive_client.omit_last_day = problem == "incomplete"
    archive_client.missing_value = problem == "missing_value"
    response = client.post("/api/advisory", json={"locationSlug": "ha-noi"})
    assert response.status_code == 502
    assert isinstance(response.json()["detail"], str)
    assert session.scalar(select(func.count()).select_from(DailyWeather)) == 0


def test_openapi_exposes_typed_contract(client: Client) -> None:
    schema = client.get("/openapi.json").json()
    assert "/api/advisory" in schema["paths"]
    assert "/api/advisory/activities" in schema["paths"]
    request_schema = schema["components"]["schemas"]["AdviceRequest"]
    assert set(request_schema["properties"]) == {
        "locationSlug",
        "time",
        "activityId",
        "topK",
    }
    assert request_schema["properties"]["topK"]["maximum"] == 3
    error_schema = schema["paths"]["/api/advisory"]["post"]["responses"]["422"][
        "content"
    ]["application/json"]["schema"]
    assert error_schema["$ref"].endswith("/AdvisoryErrorResponse")
