from app.api.routes.metrics import get_metrics
from app.metrics.prometheus_metrics import observe_request


def test_metrics_endpoint_exposes_prometheus_payload() -> None:
    observe_request(
        endpoint="/unit/metrics",
        method="GET",
        status_code=200,
        duration_seconds=0.123,
    )

    response = get_metrics()
    payload = response.body.decode("utf-8")

    assert response.status_code == 200
    assert response.media_type is not None
    assert "aiiis_http_requests_total" in payload
    assert "aiiis_http_request_duration_seconds" in payload
    assert 'endpoint="/unit/metrics",method="GET",status="200"' in payload
