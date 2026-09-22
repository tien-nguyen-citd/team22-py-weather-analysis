from weather_analysis.advisory.models import ActivityProfile, AdvisoryInputError


# Trọng số và khoảng nhiệt độ là quy ước sản phẩm, không phải chuẩn khí tượng.
ACTIVITY_PROFILES = (
    ActivityProfile(
        "general",
        "Nhu cầu chung",
        0.6,
        0.4,
        20,
        28,
        "Ưu tiên ít mưa và nhiệt độ trung bình ngày 20–28°C.",
    ),
    ActivityProfile(
        "travel",
        "Du lịch",
        0.6,
        0.4,
        16,
        28,
        "Ưu tiên ít mưa và nhiệt độ trung bình ngày 20–28°C.",
    ),
    ActivityProfile(
        "wedding",
        "Đám cưới",
        0.8,
        0.2,
        20,
        28,
        "Ưu tiên ít mưa; nhiệt độ trung bình ngày 20–28°C.",
    ),
    ActivityProfile(
        "running",
        "Chạy bộ, thể thao ngoài trời",
        0.8,
        0.2,
        16,
        30,
        "Ưu tiên nhiệt độ trung bình ngày 16–24°C và ít mưa.",
    ),
    ActivityProfile(
        "photography",
        "Chụp ảnh ngoài trời",
        0.9,
        0.1,
        18,
        30,
        "Ưu tiên ít mưa; chưa đánh giá ánh sáng hoặc mây.",
    ),
    ActivityProfile(
        "coffee",
        "Cà phê ngoài trời",
        0.6,
        0.4,
        20,
        28,
        "Ưu tiên ít mưa và nhiệt độ trung bình ngày 20–28°C.",
    ),
    ActivityProfile(
        "beach",
        "Tắm biển",
        0.6,
        0.4,
        28,
        34,
        "Ưu tiên ít mưa và nhiệt độ trung bình ngày 28–34°C; chưa đánh giá sóng, gió.",
    ),
    ActivityProfile(
        "camping",
        "Cắm trại, leo núi, dã ngoại",
        0.9,
        0.1,
        10,
        26,
        "Ưu tiên ít mưa; nhiệt độ trung bình ngày 10–26°C.",
    ),
)


def get_activity(activity_id: str | None) -> ActivityProfile:
    selected_id = "general" if activity_id is None else activity_id
    for profile in ACTIVITY_PROFILES:
        if profile.id == selected_id:
            return profile
    raise AdvisoryInputError("Hoạt động không nằm trong danh mục tư vấn")
