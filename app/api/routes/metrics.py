from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def get_metrics() -> Response:
    # exposes default prometheus registry in text format for scraper pull.
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
