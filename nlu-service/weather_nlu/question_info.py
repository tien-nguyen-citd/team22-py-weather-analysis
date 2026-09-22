from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Generic, TypeVar


class TimeKind(StrEnum):
    NOW = "now"  # lúc này, bây giờ → thời tiết hiện tại
    DATES = "dates"  # hôm nay, cuối tuần, tuần sau → dự báo theo ngày
    MONTHS = "months"  # tháng 12, tháng sau, mùa này → khí hậu theo tháng
    BEST_TIME = "best_time"  # tháng mấy, khi nào → tìm thời điểm phù hợp nhất


class Intent(StrEnum):
    FIND_PLACE = "find_place"  # Tháng 12 đi biển ở đâu? → xếp hạng điểm đến
    FIND_TIME = "find_time"  # Tháng nào đi Đà Lạt đẹp? → tư vấn thời điểm tại một nơi


@dataclass(frozen=True)
class TimeSlot:
    """Khoảng thời gian người dùng hỏi.

    Với BEST_TIME, start và end là khoảng cần tìm thời điểm phù hợp nhất;
    để trống nghĩa là không giới hạn.
    """

    kind: TimeKind
    start: date | None = None
    end: date | None = None


class DecisionSource(StrEnum):
    """Cách bộ đọc câu hỏi đi tới kết quả của hoạt động hoặc ý định."""

    LOCATION = "location"  # câu nêu địa điểm trong danh mục → tìm thời điểm
    KEYWORD = "keyword"  # khớp từ khóa trong CSV
    BEST_TIME = "best_time"  # câu hỏi thời điểm tốt nhất → tìm thời điểm
    NO_WORDS = "no_words"  # bỏ địa điểm và từ khóa xong không còn chữ nào
    NEAREST_EXAMPLES = "nearest_examples"  # bỏ phiếu theo các câu mẫu gần nhất

    @property
    def method(self) -> "DecisionMethod":
        if self == DecisionSource.NEAREST_EXAMPLES:
            return DecisionMethod.MINILM
        return DecisionMethod.RULE


class DecisionMethod(StrEnum):
    """Kết quả đến từ quy tắc, từ khóa hay từ embedding MiniLM."""

    RULE = "rule"
    MINILM = "minilm"


# Covariant để Neighbor[Intent] dùng được ở chỗ cần Neighbor[str | None].
LabelT = TypeVar("LabelT", covariant=True)


@dataclass(frozen=True)
class Neighbor(Generic[LabelT]):
    """Một câu mẫu gần câu hỏi, similarity là cosine similarity từ -1 đến 1."""

    label: LabelT
    text: str
    similarity: float


@dataclass(frozen=True)
class Decision:
    source: DecisionSource
    matched_text: str | None = None  # cụm từ khớp khi source là KEYWORD
    neighbors: tuple[Neighbor[str | None], ...] = ()  # khi source là NEAREST_EXAMPLES


@dataclass(frozen=True)
class ExtractionExplanation:
    """Giải thích vì sao câu hỏi được hiểu như vậy, dùng để kiểm tra bộ đọc câu hỏi."""

    embedding_text: str  # phần câu hỏi đưa vào MiniLM sau khi bỏ các cụm từ đã nhận ra
    location_text: str | None  # tên địa điểm khớp trong câu
    activity: Decision
    intent: Decision


@dataclass(frozen=True)
class QuestionInfo:
    """Bốn thông tin cần để phân tích thời tiết cho một câu hỏi."""

    location_slug: str | None  # slug trong locations.csv
    time: TimeSlot | None
    activity_id: str | None  # id trong activities.csv
    intent: Intent = Intent.FIND_TIME  # id trong intents.csv
    # Không dùng khi so sánh để việc đánh giá độ chính xác chỉ xét bốn thông tin trên.
    explanation: ExtractionExplanation | None = field(default=None, compare=False)
