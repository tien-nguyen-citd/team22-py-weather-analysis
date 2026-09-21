from collections.abc import Callable, Coroutine
from datetime import date, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from weather_analysis.advisory.activities import ACTIVITY_PROFILES
from weather_analysis.advisory.destinations import get_destination_ranking
from weather_analysis.advisory.models import AdvisoryInputError
from weather_analysis.advisory.service import get_advice
from weather_analysis.api.advisory_schemas import (
    ActivityProfileResponse,
    AdviceRequest,
    AdviceResponse,
    AdvisoryErrorResponse,
    DestinationRankingResponse,
    DestinationRequestBody,
)
from weather_analysis.api.dependencies import DbSession, WeatherClient
from weather_analysis.clients.open_meteo_client import (
    VIETNAM_TIMEZONE,
    WeatherProviderError,
)
from weather_analysis.services.climate_service import ClimateDataError
from weather_analysis.services.location_service import LocationNotFoundError


class AdvisoryRoute(APIRoute):
    """Thông báo lỗi cấu trúc yêu cầu bằng tiếng Việt, chỉ cho API tư vấn."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            try:
                return await handler(request)
            except RequestValidationError:
                return JSONResponse(
                    status_code=422,
                    content={
                        "detail": "Thông tin tư vấn không hợp lệ. Kiểm tra địa điểm, khoảng tháng, hoạt động và số lựa chọn (1–3).",
                    },
                )

        return handle


router = APIRouter(prefix="/api/advisory", tags=["advisory"], route_class=AdvisoryRoute)


def get_advisory_today() -> date:
    return datetime.now(VIETNAM_TIMEZONE).date()


@router.get(
    "/activities",
    response_model=list[ActivityProfileResponse],
    summary="Danh mục hoạt động và tiêu chí",
)
def get_activities() -> list[ActivityProfileResponse]:
    return [
        ActivityProfileResponse.model_validate(profile) for profile in ACTIVITY_PROFILES
    ]


@router.post(
    "",
    response_model=AdviceResponse,
    summary="Tìm thời điểm phù hợp theo lịch sử khí hậu",
    responses={
        422: {"model": AdvisoryErrorResponse, "description": "Yêu cầu không hợp lệ"},
        404: {"model": AdvisoryErrorResponse, "description": "Không tìm thấy địa điểm"},
        502: {
            "model": AdvisoryErrorResponse,
            "description": "Không đủ dữ liệu lịch sử hợp lệ",
        },
    },
)
def advise(
    request: AdviceRequest,
    session: DbSession,
    client: WeatherClient,
    today: Annotated[date, Depends(get_advisory_today)],
) -> AdviceResponse:
    try:
        advice = get_advice(session, request.to_request(), client, today)
    except AdvisoryInputError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except LocationNotFoundError as error:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy địa điểm"
        ) from error
    except (WeatherProviderError, ClimateDataError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return AdviceResponse.model_validate(advice)


@router.post(
    "/destinations",
    response_model=DestinationRankingResponse,
    summary="Xếp hạng điểm đến theo tháng và hoạt động",
    responses={
        422: {"model": AdvisoryErrorResponse, "description": "Yêu cầu không hợp lệ"},
        502: {
            "model": AdvisoryErrorResponse,
            "description": "Không đủ dữ liệu lịch sử hợp lệ",
        },
    },
)
def rank_destinations(
    request: DestinationRequestBody,
    session: DbSession,
    client: WeatherClient,
    today: Annotated[date, Depends(get_advisory_today)],
) -> DestinationRankingResponse:
    try:
        ranking = get_destination_ranking(session, request.to_request(), client, today)
    except AdvisoryInputError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except (WeatherProviderError, ClimateDataError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return DestinationRankingResponse.from_ranking(ranking)
