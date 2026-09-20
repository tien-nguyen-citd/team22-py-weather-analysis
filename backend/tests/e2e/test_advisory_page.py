from typing import Any

from playwright.sync_api import Page, Route, expect
import pytest

from tests.e2e.advisory_fixtures import (  # noqa: F401
    advisory_requests,
    request_payload,
)


SAMPLE_TRAVEL = "Mùa này đi Phú Quốc có hợp không?"
FREE_QUESTION = "Đám cưới tháng mấy thì đẹp nhất?"


@pytest.fixture
def nlu_requests(page: Page) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    page.route(
        "**/nlu/health",
        lambda route: route.fulfill(json={"status": "ok", "extractor": "test"}),
    )

    def understand(route: Route) -> None:
        payload = request_payload(route)
        requests.append(payload)
        if payload["question"] == SAMPLE_TRAVEL:
            route.fulfill(
                json={
                    "locationSlug": "phu-quoc",
                    "locationFromQuestion": True,
                    "activityId": "travel",
                    "time": {
                        "kind": "months",
                        "startDate": "2026-09-01",
                        "endDate": "2026-11-30",
                    },
                }
            )
            return
        route.fulfill(
            json={
                "locationSlug": None,
                "locationFromQuestion": False,
                "activityId": "wedding",
                "time": {
                    "kind": "best_time",
                    "startDate": "2027-01-01",
                    "endDate": "2027-03-31",
                },
            }
        )

    page.route("**/nlu/understand", understand)
    return requests


def test_chat_landing_has_no_location_bar(
    page: Page,
    advisory_requests: list[dict[str, Any]],  # noqa: F811
    nlu_requests: list[dict[str, Any]],
) -> None:
    page.goto("/ha-noi/tu-van")
    expect(page.get_by_role("heading", name="Bạn cần tư vấn thời tiết?")).to_be_visible()
    expect(page.get_by_role("group", name="Địa điểm yêu thích và gợi ý")).to_have_count(0)
    assert advisory_requests == []
    assert nlu_requests == []


def test_sample_question_gives_advice_and_shows_what_was_understood(
    page: Page,
    advisory_requests: list[dict[str, Any]],  # noqa: F811
    nlu_requests: list[dict[str, Any]],
) -> None:
    page.goto("/ha-noi/tu-van")
    page.get_by_role("button", name=SAMPLE_TRAVEL, exact=True).click()

    results = page.get_by_role("region", name="Kết quả tư vấn")
    expect(results).to_be_visible()
    expect(results.get_by_role("article")).to_have_count(2)

    assert nlu_requests[-1]["currentLocationSlug"] == "ha-noi"
    assert len(nlu_requests[-1]["today"]) == 10
    assert advisory_requests[-1] == {
        "locationSlug": "phu-quoc",
        "activityId": "travel",
        "time": {"startMonth": "2026-09", "endMonth": "2026-11"},
        "topK": 2,
    }

    understood = page.get_by_text("Hiểu là", exact=True).locator("..")
    expect(understood).to_contain_text("Phú Quốc")
    expect(understood).to_contain_text("Du lịch")


def test_free_question_uses_the_current_location_when_nlu_returns_none(
    page: Page,
    advisory_requests: list[dict[str, Any]],  # noqa: F811
    nlu_requests: list[dict[str, Any]],
) -> None:
    page.goto("/ha-noi/tu-van")
    page.get_by_label("Câu hỏi của bạn", exact=True).fill(FREE_QUESTION)
    page.get_by_role("button", name="Gửi câu hỏi", exact=True).click()

    expect(page.get_by_role("region", name="Kết quả tư vấn")).to_be_visible()
    assert nlu_requests[-1]["question"] == FREE_QUESTION
    assert advisory_requests[-1]["locationSlug"] == "ha-noi"
    assert advisory_requests[-1]["activityId"] == "wedding"
    assert advisory_requests[-1]["time"] == {
        "startMonth": "2027-01",
        "endMonth": "2027-03",
    }


def test_saved_user_location_is_independent_from_viewed_location(
    page: Page,
    advisory_requests: list[dict[str, Any]],  # noqa: F811
    nlu_requests: list[dict[str, Any]],
) -> None:
    page.add_init_script(
        "localStorage.setItem('nang_mua_user_location', 'da-nang')"
    )
    page.goto("/ha-noi/tu-van")

    expect(page.get_by_role("button", name="Vị trí của tôi: Đà Nẵng")).to_be_visible()
    page.get_by_label("Câu hỏi của bạn", exact=True).fill(FREE_QUESTION)
    page.get_by_role("button", name="Gửi câu hỏi", exact=True).click()

    expect(page.get_by_role("region", name="Kết quả tư vấn")).to_be_visible()
    assert page.url.endswith("/ha-noi/tu-van")
    assert nlu_requests[-1]["currentLocationSlug"] == "da-nang"
    assert advisory_requests[-1]["locationSlug"] == "da-nang"


def test_user_can_search_change_and_keep_user_location(
    page: Page,
    advisory_requests: list[dict[str, Any]],  # noqa: F811
    nlu_requests: list[dict[str, Any]],
) -> None:
    page.goto("/ha-noi/tu-van")

    expect(page.get_by_role("button", name="Vị trí của tôi: Hà Nội")).to_be_visible()
    page.get_by_role("button", name="Vị trí của tôi: Hà Nội").click()
    page.get_by_label("Tìm vị trí của tôi").fill("Đà Nẵng")
    page.get_by_role("option", name="Đà Nẵng Trung Trung Bộ").click()

    assert page.url.endswith("/ha-noi/tu-van")
    expect(page.get_by_role("button", name="Vị trí của tôi: Đà Nẵng")).to_be_visible()
    page.reload()
    expect(page.get_by_role("button", name="Vị trí của tôi: Đà Nẵng")).to_be_visible()


def test_first_visit_uses_browser_location_for_user_location_and_root_route(
    page: Page,
    advisory_requests: list[dict[str, Any]],  # noqa: F811
) -> None:
    page.add_init_script(
        """
        Object.defineProperty(navigator, 'geolocation', {
          configurable: true,
          value: {
            getCurrentPosition(success) {
              success({ coords: { latitude: 16.05, longitude: 108.2 } });
            },
          },
        });
        """
    )
    page.goto("/")

    page.wait_for_url("**/da-nang/tong-quan")
    expect(page.get_by_role("button", name="Vị trí của tôi: Đà Nẵng")).to_be_visible()


def test_failed_manual_detection_keeps_the_saved_location(
    page: Page,
    advisory_requests: list[dict[str, Any]],  # noqa: F811
) -> None:
    page.add_init_script(
        """
        localStorage.setItem('nang_mua_user_location', 'ha-noi');
        Object.defineProperty(navigator, 'geolocation', {
          configurable: true,
          value: {
            getCurrentPosition(_success, error) {
              error({ code: 1, message: 'permission denied' });
            },
          },
        });
        """
    )
    page.goto("/ha-noi/tu-van")

    page.get_by_role("button", name="Vị trí của tôi: Hà Nội").click()
    page.get_by_role("button", name="Dùng vị trí hiện tại").click()

    expect(page.get_by_role("alert")).to_contain_text("Không xác định được vị trí")
    expect(page.get_by_role("button", name="Vị trí của tôi: Hà Nội")).to_be_visible()


def test_unavailable_nlu_opens_the_manual_form_without_a_back_button(
    page: Page,
    advisory_requests: list[dict[str, Any]],  # noqa: F811
) -> None:
    page.route(
        "**/nlu/health",
        lambda route: route.fulfill(
            status=503, json={"detail": "NLU service không khả dụng"}
        ),
    )
    page.goto("/ha-noi/tu-van")

    form = page.get_by_role("region", name="Điền tiêu chí tư vấn")
    expect(form).to_be_visible()
    expect(page.get_by_role("heading", name="Bạn cần tư vấn thời tiết?")).to_have_count(0)
    expect(form.get_by_role("button", name="Quay lại hỏi bằng câu")).to_have_count(0)
    expect(form.get_by_label("Địa điểm", exact=True)).to_have_value("ha-noi")
    assert advisory_requests == []


def test_edit_opens_the_form_with_the_values_just_used(
    page: Page,
    advisory_requests: list[dict[str, Any]],  # noqa: F811
    nlu_requests: list[dict[str, Any]],
) -> None:
    page.goto("/ha-noi/tu-van")
    page.get_by_role("button", name=SAMPLE_TRAVEL, exact=True).click()
    expect(page.get_by_role("region", name="Kết quả tư vấn")).to_be_visible()

    page.get_by_role("button", name="Sửa", exact=True).click()
    form = page.get_by_role("region", name="Điền tiêu chí tư vấn")
    expect(form).to_be_visible()
    expect(form.get_by_label("Địa điểm", exact=True)).to_have_value("phu-quoc")
    expect(form.get_by_label("Hoạt động", exact=True)).to_have_value("travel")

    form.get_by_role("button", name="Quay lại hỏi bằng câu", exact=True).click()
    expect(page.get_by_role("heading", name="Bạn cần tư vấn thời tiết?")).to_be_visible()
    assert nlu_requests[-1]["question"] == SAMPLE_TRAVEL
