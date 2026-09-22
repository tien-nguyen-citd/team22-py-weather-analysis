from playwright.sync_api import Page


class LocationBar:
    """Thanh tìm kiếm và chọn địa điểm."""

    PATH = "/"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.search_input = page.get_by_placeholder("Tìm tỉnh, thành phố…")
        self.results = page.get_by_role(
            "listbox", name="Kết quả tìm địa điểm"
        ).get_by_role("option")

    def open(self) -> None:
        """Mở trang tổng quan."""
        self.page.goto(self.PATH)

    def search(self, query: str) -> None:
        """Nhập nội dung cần tìm vào ô tìm kiếm địa điểm."""
        self.search_input.fill(query)
