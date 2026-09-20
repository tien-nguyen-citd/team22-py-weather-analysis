from datetime import date
from pathlib import Path
from typing import Any, cast

from playwright.sync_api import Page, Route, expect
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


def advice_response(
    payload: dict[str, Any], low_suitability: bool = False
) -> dict[str, Any]:
    today = date(2026, 9, 20)
    period = calculate_climate_period(today)
    request = normalize_request(
        AdviceRequest.model_validate(payload).to_request(), today
    )

    def weather(day: date) -> tuple[float, float]:
        if low_suitability:
            return 42, 10
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


def fill_request(page: Page) -> None:
    page.get_by_label("Hoạt động", exact=True).select_option("wedding")
    page.get_by_label("Từ tháng", exact=True).fill("2027-01")
    page.get_by_label("Đến tháng", exact=True).fill("2027-03")


def test_advice_explanation_keyboard_chart_and_month_drilldown(
    page: Page,
    advisory_requests: list[dict[str, Any]],
    tmp_path: Path,
) -> None:
    page.goto("/ha-noi/tu-van")
    fill_request(page)
    page.get_by_role("button", name="Tìm thời điểm phù hợp", exact=True).click()
    results = page.get_by_role("region", name="Kết quả tư vấn")
    expect(results).to_be_visible()
    expect(results.get_by_role("article")).to_have_count(2)
    expect(results).to_contain_text("không phải dự báo cho ngày cụ thể")
    assert advisory_requests[-1]["locationSlug"] == "ha-noi"
    primary = results.get_by_role(
        "article", name="Đề xuất chính: Tháng 01/2027", exact=True
    )
    primary.get_by_text("Vì sao chọn?", exact=True).click()
    expect(primary).to_contain_text("100 × 80% = 80 điểm")
    february = results.get_by_role("button", name="Tháng 02/2027: 100 điểm", exact=True)
    february.focus()
    page.keyboard.press("Enter")
    expect(february).to_have_attribute("aria-pressed", "true")
    expect(
        results.get_by_role("heading", name="Tháng 02/2027 · Hạng 2/3")
    ).to_be_visible()
    page.screenshot(path=str(tmp_path / "advisory-desktop.png"), full_page=True)
    primary.get_by_role("button", name="Xem giai đoạn trong tháng này").click()
    expect(
        results.get_by_role("heading", name="Đầu tháng 01/2027", exact=True)
    ).to_be_visible()
    assert advisory_requests[-1]["time"] == {
        "startMonth": "2027-01",
        "endMonth": "2027-01",
    }
    page.get_by_label("Hoạt động", exact=True).select_option("running")
    expect(results).not_to_be_visible()


def test_validation_presets_and_mobile_layout(
    page: Page,
    advisory_requests: list[dict[str, Any]],
    tmp_path: Path,
) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto("/ha-noi/tu-van")
    fill_request(page)
    page.get_by_label("Đến tháng", exact=True).fill("2028-01")
    page.get_by_role("button", name="Tìm thời điểm phù hợp", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("1 đến 12 tháng")
    assert advisory_requests == []
    page.get_by_role("button", name="Du lịch Phú Quốc", exact=True).click()
    expect(page).to_have_url("/phu-quoc/tu-van?activity=travel")
    expect(page.get_by_label("Hoạt động", exact=True)).to_have_value("travel")
    page.get_by_role("button", name="Tìm thời điểm phù hợp", exact=True).click()
    results = page.get_by_role("region", name="Kết quả tư vấn")
    expect(results).to_be_visible()
    assert advisory_requests[-1]["locationSlug"] == "phu-quoc"
    assert advisory_requests[-1]["activityId"] == "travel"
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path=str(tmp_path / "advisory-mobile.png"), full_page=True)


def test_error_retry_and_low_suitability(
    page: Page, advisory_requests: list[dict[str, Any]]
) -> None:
    page.unroute("**/api/advisory")
    attempts = 0

    def respond(route: Route) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            route.fulfill(status=502, json={"detail": "Dữ liệu lịch sử chưa đủ ngày"})
        else:
            route.fulfill(
                json=advice_response(request_payload(route), low_suitability=True)
            )

    page.route("**/api/advisory", respond)
    page.goto("/ha-noi/tu-van")
    fill_request(page)
    page.get_by_role("button", name="Tìm thời điểm phù hợp", exact=True).click()
    expect(page.get_by_text("Dữ liệu lịch sử chưa đủ ngày", exact=True)).to_be_visible()
    page.get_by_role("button", name="Thử lại", exact=True).click()
    expect(page.get_by_role("region", name="Kết quả tư vấn")).to_contain_text(
        "ít phù hợp"
    )
    assert attempts == 2


def test_location_change_cancels_pending_advice(
    page: Page, advisory_requests: list[dict[str, Any]]
) -> None:
    page.unroute("**/api/advisory")
    pending: list[Route] = []

    def respond(route: Route) -> None:
        if request_payload(route)["locationSlug"] == "ha-noi":
            pending.append(route)
        else:
            route.fulfill(json=advice_response(request_payload(route)))

    page.route("**/api/advisory", respond)
    page.goto("/ha-noi/tu-van")
    fill_request(page)
    with page.expect_request("**/api/advisory"):
        page.get_by_role("button", name="Tìm thời điểm phù hợp", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("Lần đầu ở một địa điểm")
    with page.expect_event(
        "requestfailed", predicate=lambda request: request.url.endswith("/api/advisory")
    ):
        page.get_by_role("button", name="Cắm trại Đà Lạt", exact=True).click()
    expect(page.get_by_role("region", name="Kết quả tư vấn")).not_to_be_visible()
    page.get_by_role("button", name="Tìm thời điểm phù hợp", exact=True).click()
    expect(page.get_by_role("region", name="Kết quả tư vấn")).to_contain_text(
        "Cắm trại, leo núi, dã ngoại · Đà Lạt"
    )
    assert len(pending) == 1
