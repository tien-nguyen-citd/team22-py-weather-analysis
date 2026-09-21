from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from weather_nlu.activities import (
    ActivityKeywordMatcher,
    load_activities,
    load_activity_examples,
)
from weather_nlu.api.dependencies import set_extractor
from weather_nlu.api.routes import router
from weather_nlu.encoder import MINILM_MODEL, MiniLmEncoder
from weather_nlu.extractor import RuleMiniLmExtractor
from weather_nlu.intents import IntentKeywordMatcher, load_intent_examples, load_intents
from weather_nlu.locations import LocationMatcher, load_locations
from weather_nlu.models import download_model


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    download_model(MINILM_MODEL)
    set_extractor(
        RuleMiniLmExtractor(
            MiniLmEncoder(),
            load_activity_examples(),
            LocationMatcher(load_locations()),
            ActivityKeywordMatcher(load_activities()),
            IntentKeywordMatcher(load_intents()),
            load_intent_examples(),
        )
    )
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
