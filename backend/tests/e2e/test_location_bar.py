from playwright.sync_api import Page, expect

from tests.e2e.pages.location_bar import LocationBar


def test_search_shows_matching_location(page: Page) -> None:
    location_bar = LocationBar(page)

    location_bar.open()
    location_bar.search("Đà Nẵng")

    expect(location_bar.results).to_have_count(1)
    expect(location_bar.results).to_contain_text("Đà Nẵng")


def test_search_by_abbreviation_shows_full_name(page: Page) -> None:
    location_bar = LocationBar(page)

    location_bar.open()
    location_bar.search("HCM")

    expect(location_bar.results).to_have_count(1)
    expect(location_bar.results).to_contain_text("Hồ Chí Minh")


def test_compare_page_does_not_show_location_bar(page: Page) -> None:
    page.goto("/ha-noi/so-sanh")

    expect(page.get_by_placeholder("Tìm tỉnh, thành phố…")).to_have_count(0)
    expect(
        page.get_by_role("group", name="Địa điểm yêu thích và gợi ý")
    ).to_have_count(0)
