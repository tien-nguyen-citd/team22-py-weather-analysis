from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from weather_analysis.api.admin_location_routes import router as admin_location_router
from weather_analysis.api.admin_settings_routes import router as admin_settings_router
from weather_analysis.api.auth_routes import router as auth_router
from weather_analysis.api.climate_routes import router as climate_router
from weather_analysis.api.forecast_routes import router as forecast_router
from weather_analysis.api.location_routes import router as location_router
from weather_analysis.config import get_session_secret
from weather_analysis.database import (
    ensure_database_exists,
    session_scope,
    upgrade_database,
)
from weather_analysis.seed import seed_all


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    ensure_database_exists()
    upgrade_database()
    with session_scope() as session:
        seed_all(session)
    yield


app = FastAPI(title="Phân tích thời tiết", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=get_session_secret())
app.include_router(auth_router)
app.include_router(location_router)
app.include_router(forecast_router)
app.include_router(climate_router)
app.include_router(admin_location_router)
app.include_router(admin_settings_router)
