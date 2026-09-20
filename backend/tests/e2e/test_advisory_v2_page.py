from typing import Any

from playwright.sync_api import Page, expect

from tests.e2e.test_advisory_page import advisory_requests  # noqa: F401


SAMPLE_WEDDING = "Đám cưới ở Hà Nội tháng mấy thì đẹp nhất?"


def test_chat_landing_has_no_location_bar(
    page: Page,
    advisory_requests: list[dict[str, Any]],  # noqa: F811
) -> None:
    page.goto("/ha-noi/tu-van-v2")
    expect(page.get_by_role("heading", name="Bạn cần tư vấn thời tiết?")).to_be_visible()
    expect(page.get_by_role("group", name="Địa điểm yêu thích và gợi ý")).to_have_count(0)
    assert advisory_requests == []


def test_sample_question_gives_advice_and_shows_what_was_understood(
    page: Page,
    advisory_requests: list[dict[str, Any]],  # noqa: F811
) -> None:
    page.goto("/ha-noi/tu-van-v2")
    page.get_by_role("button", name=SAMPLE_WEDDING, exact=True).click()

    results = page.get_by_role("region", name="Kết quả tư vấn")
    expect(results).to_be_visible()
    expect(results.get_by_role("article")).to_have_count(2)

    assert advisory_requests[-1]["locationSlug"] == "ha-noi"
    assert advisory_requests[-1]["activityId"] == "wedding"
    assert advisory_requests[-1]["topK"] == 2

    understood = page.get_by_text("Hiểu là", exact=True).locator("..")
    expect(understood).to_contain_text("Hà Nội")
    expect(understood).to_contain_text("Đám cưới")


def test_free_question_explains_the_limit_without_calling_the_api(
    page: Page,
    advisory_requests: list[dict[str, Any]],  # noqa: F811
) -> None:
    page.goto("/ha-noi/tu-van-v2")
    page.get_by_label("Câu hỏi của bạn", exact=True).fill("Ngày mai Huế có mưa không?")
    page.get_by_role("button", name="Gửi câu hỏi", exact=True).click()

    expect(page.get_by_role("alert")).to_contain_text("ba câu mẫu")
    expect(page.get_by_role("region", name="Kết quả tư vấn")).to_have_count(0)
    assert advisory_requests == []


def test_edit_opens_the_form_with_the_values_just_used(
    page: Page,
    advisory_requests: list[dict[str, Any]],  # noqa: F811
) -> None:
    page.goto("/ha-noi/tu-van-v2")
    page.get_by_role("button", name=SAMPLE_WEDDING, exact=True).click()
    expect(page.get_by_role("region", name="Kết quả tư vấn")).to_be_visible()

    page.get_by_role("button", name="Sửa", exact=True).click()
    form = page.get_by_role("region", name="Điền tiêu chí tư vấn")
    expect(form).to_be_visible()
    expect(form.get_by_label("Địa điểm", exact=True)).to_have_value("ha-noi")
    expect(form.get_by_label("Hoạt động", exact=True)).to_have_value("wedding")

    form.get_by_role("button", name="Quay lại hỏi bằng câu", exact=True).click()
    expect(page.get_by_role("heading", name="Bạn cần tư vấn thời tiết?")).to_be_visible()
