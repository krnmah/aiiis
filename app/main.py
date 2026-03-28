from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.logs import router as logs_router
from app.core.config import get_settings
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
app.include_router(health_router)
app.include_router(logs_router)
