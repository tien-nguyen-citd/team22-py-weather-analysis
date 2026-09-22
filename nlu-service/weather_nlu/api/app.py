from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from weather_nlu.api.dependencies import set_extractor
from weather_nlu.api.routes import router
from weather_nlu.encoder import MINILM_MODEL
from weather_nlu.extractor import build_rule_minilm_extractor
from weather_nlu.models import download_model


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    download_model(MINILM_MODEL)
    set_extractor(build_rule_minilm_extractor())
    try:
        yield
    finally:
        set_extractor(None)


app = FastAPI(title="Dịch vụ đọc câu hỏi thời tiết", lifespan=lifespan)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    _request: Request, _error: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "Câu hỏi hoặc thông tin tham chiếu không hợp lệ."},
    )
