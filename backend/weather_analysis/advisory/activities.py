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
        "Ưu tiên ít mưa và nhiệt độ trung bình ngày 16–28°C.",
    ),
    ActivityProfile(
        "wedding",
        "Tổ chức đám cưới",
        0.8,
        0.2,
        20,
        28,
        "Ưu tiên ít mưa; nhiệt độ trung bình ngày 20–28°C.",
    ),
    ActivityProfile(
        "sports",
        "Thể thao ngoài trời",
        0.8,
        0.2,
        16,
        30,
        "Ưu tiên ít mưa; nhiệt độ trung bình ngày 16–30°C.",
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
        "Cắm trại, dã ngoại",
        0.9,
        0.1,
        10,
        26,
        "Ưu tiên ít mưa; nhiệt độ trung bình ngày 10–26°C.",
    ),
    ActivityProfile(
        "construction",
        "Thi công xây dựng",
        0.8,
        0.2,
        15,
        30,
        "Ưu tiên ít mưa; nhiệt độ trung bình ngày 15–30°C; chưa đánh giá gió hoặc độ ẩm.",
    ),
    ActivityProfile(
        "outdoor_event",
        "Sự kiện ngoài trời",
        0.7,
        0.3,
        20,
        28,
        "Ưu tiên ít mưa và nhiệt độ trung bình ngày 20–28°C.",
    ),
)


def get_activity(activity_id: str | None) -> ActivityProfile:
    selected_id = "general" if activity_id is None else activity_id
    for profile in ACTIVITY_PROFILES:
        if profile.id == selected_id:
            return profile
    raise AdvisoryInputError("Hoạt động không nằm trong danh mục tư vấn")
