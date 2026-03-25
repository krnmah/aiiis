from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db.database import check_db_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
def db_health_check() -> JSONResponse:
    try:
        check_db_connection()
        return JSONResponse(status_code=200, content={"status": "ok", "database": "up"})
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "down"},
        )
