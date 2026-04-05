from time import perf_counter

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db.database import check_db_connection
from app.metrics.prometheus_metrics import observe_request

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    start_time = perf_counter()
    status_code = 200
    try:
        return {"status": "ok"}
    finally:
        observe_request(
            endpoint="/health",
            method="GET",
            status_code=status_code,
            duration_seconds=perf_counter() - start_time,
        )


@router.get("/health/db")
def db_health_check() -> JSONResponse:
    start_time = perf_counter()
    status_code = 200
    try:
        check_db_connection()
        return JSONResponse(status_code=200, content={"status": "ok", "database": "up"})
    except Exception:
        status_code = 503
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "down"},
        )
    finally:
        observe_request(
            endpoint="/health/db",
            method="GET",
            status_code=status_code,
            duration_seconds=perf_counter() - start_time,
        )
