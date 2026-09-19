from weather_analysis.services.climate_service import MonthClimate
from weather_analysis.services.compare_service import (
    get_compare_conclusion,
    get_compare_summary,
)


def test_compare_text_matches_existing_behavior() -> None:
    da_lat = MonthClimate(12, 17, 60, 6, 79)
    ho_chi_minh = MonthClimate(12, 27, 40, 4, 91)

    conclusion = get_compare_conclusion(
        12, "Đà Lạt", da_lat, "Hồ Chí Minh", ho_chi_minh
    )

    assert "Hồ Chí Minh khô hơn với 4 ngày mưa so với 6 ngày" in conclusion
    assert "Đà Lạt mát hơn khoảng 10°C" in conclusion
    assert "Hồ Chí Minh nhích hơn 12 điểm" in conclusion
    assert get_compare_summary("Đà Lạt", 12, da_lat).endswith(
        "Đi được, nên chuẩn bị áo mưa mỏng."
    )
