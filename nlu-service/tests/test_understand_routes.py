from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient

from weather_nlu.api.app import app
from weather_nlu.api.dependencies import get_extractor, get_reference_date
from weather_nlu.question_info import QuestionInfo, TimeKind, TimeSlot


class FakeExtractor:
    name = "rule+minilm"

    def __init__(self) -> None:
        self.received_dates: list[date] = []

    def extract(self, question: str, today: date) -> QuestionInfo:
        self.received_dates.append(today)
        if question == "Mùa này đi Phú Quốc có hợp không?":
            return QuestionInfo(
                location_slug="phu-quoc",
                time=TimeSlot(
                    TimeKind.MONTHS,
                    date(2026, 9, 1),
                    date(2026, 11, 30),
                ),
                activity_id="travel",
            )
        return QuestionInfo(location_slug=None, time=None, activity_id=None)


@pytest.fixture
def fake_extractor() -> FakeExtractor:
    return FakeExtractor()


@pytest.fixture
def client(fake_extractor: FakeExtractor) -> Iterator[TestClient]:
    overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_extractor] = lambda: fake_extractor
    app.dependency_overrides[get_reference_date] = lambda: date(2026, 9, 20)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides)


def test_understand_returns_all_extracted_information(client: TestClient) -> None:
    response = client.post(
        "/nlu/understand",
        json={
            "question": "Mùa này đi Phú Quốc có hợp không?",
            "currentLocationSlug": "ha-noi",
            "today": "2026-09-20",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "locationSlug": "phu-quoc",
        "locationFromQuestion": True,
        "activityId": "travel",
        "time": {
            "kind": "months",
            "startDate": "2026-09-01",
            "endDate": "2026-11-30",
        },
    }


def test_understand_falls_back_to_current_location(client: TestClient) -> None:
    response = client.post(
        "/nlu/understand",
        json={"question": "Thời tiết thế nào?", "currentLocationSlug": "ha-noi"},
    )

    assert response.status_code == 200
    assert response.json()["locationSlug"] == "ha-noi"
    assert response.json()["locationFromQuestion"] is False


def test_understand_uses_vietnam_today_by_default(
    client: TestClient, fake_extractor: FakeExtractor
) -> None:
    response = client.post("/nlu/understand", json={"question": "Ngày mai có mưa không?"})

    assert response.status_code == 200
    assert fake_extractor.received_dates[-1] == date(2026, 9, 20)


def test_understand_returns_null_when_time_is_missing(client: TestClient) -> None:
    response = client.post("/nlu/understand", json={"question": "Thời tiết thế nào?"})

    assert response.status_code == 200
    assert response.json()["time"] is None


@pytest.mark.parametrize("question", ["", "   ", "x" * 501])
def test_understand_rejects_invalid_question(
    client: TestClient, question: str
) -> None:
    response = client.post("/nlu/understand", json={"question": question})

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


def test_health_reports_loaded_extractor(client: TestClient) -> None:
    response = client.get("/nlu/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "extractor": "rule+minilm"}
