from datetime import date
from typing import Any, cast

from playwright.sync_api import Page, Route
import pytest

from tests.advisory_helpers import make_history
from weather_analysis.advisory.candidates import normalize_request
from weather_analysis.advisory.service import build_advice
from weather_analysis.api.advisory_schemas import AdviceRequest, AdviceResponse
from weather_analysis.services.climate_service import calculate_climate_period


def request_payload(route: Route) -> dict[str, Any]:
    payload = route.request.post_data_json
    assert isinstance(payload, dict)
    return cast(dict[str, Any], payload)


def advice_response(payload: dict[str, Any]) -> dict[str, Any]:
    today = date(2026, 9, 20)
    period = calculate_climate_period(today)
    request = normalize_request(
        AdviceRequest.model_validate(payload).to_request(), today
    )

    def weather(day: date) -> tuple[float, float]:
        return (22, 0) if day.month <= 3 else (30, 5)

    return AdviceResponse.model_validate(
        build_advice(request, make_history(period, weather), period)
    ).model_dump(mode="json", by_alias=True)


@pytest.fixture
def advisory_requests(page: Page) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    # Luồng tư vấn phải hoạt động ngay cả khi dự báo hiện tại lỗi.
    page.route(
        "**/api/locations/*/forecast",
        lambda route: route.fulfill(
            status=502, json={"detail": "Không lấy được dự báo"}
        ),
    )
    page.route("**/api/locations/temperatures*", lambda route: route.fulfill(json={}))

    def respond(route: Route) -> None:
        payload = request_payload(route)
        requests.append(payload)
        route.fulfill(json=advice_response(payload))

    page.route("**/api/advisory", respond)
    return requests
