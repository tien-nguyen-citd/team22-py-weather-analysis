from fastapi import APIRouter

from weather_nlu.api.dependencies import Extractor, ReferenceDate
from weather_nlu.api.schemas import (
    DebugResponse,
    HealthResponse,
    TimeSlotResponse,
    UnderstandRequest,
    UnderstandResponse,
)


router = APIRouter(prefix="/nlu", tags=["nlu"])


@router.post(
    "/understand",
    response_model=UnderstandResponse,
    summary="Đọc câu hỏi tư vấn thời tiết",
)
def understand(
    request: UnderstandRequest,
    extractor: Extractor,
    reference_date: ReferenceDate,
) -> UnderstandResponse:
    result = extractor.extract(request.question, request.today or reference_date)
    location_from_question = result.location_slug is not None
    return UnderstandResponse(
        location_slug=result.location_slug or request.current_location_slug,
        location_from_question=location_from_question,
        activity_id=result.activity_id,
        time=TimeSlotResponse.from_slot(result.time) if result.time else None,
        intent=result.intent,
        debug=(
            DebugResponse.from_explanation(result.explanation)
            if result.explanation
            else None
        ),
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Kiểm tra tình trạng dịch vụ",
)
def health(extractor: Extractor) -> HealthResponse:
    return HealthResponse(status="ok", extractor=extractor.name)
