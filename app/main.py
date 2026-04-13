from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.llm import router as llm_router
from app.api.routes.logs import router as logs_router
from app.api.routes.metrics import router as metrics_router
from app.core.config import get_settings, parse_csv_setting
from app.core.logging_config import configure_logging
from app.db.database import initialize_database

settings = get_settings()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # configured logging first so startup/shutdown and db init logs are structured too.
    configure_logging(log_level=settings.app_log_level)
    logger.info("application_startup_begin", extra={"app_env": settings.app_env})
    initialize_database()
    logger.info("application_startup_complete")
    yield
    logger.info("application_shutdown")


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_csv_setting(settings.cors_allow_origins),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=parse_csv_setting(settings.cors_allow_methods),
    allow_headers=parse_csv_setting(settings.cors_allow_headers),
)
app.include_router(health_router)
app.include_router(logs_router)
app.include_router(llm_router)
app.include_router(incidents_router)
app.include_router(metrics_router)
