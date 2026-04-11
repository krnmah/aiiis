from prometheus_client import Counter, Histogram

# counts every request processed by endpoint/method/status for quick traffic and error trends.
HTTP_REQUESTS_TOTAL = Counter(
    "aiiis_http_requests_total",
    "Total number of HTTP requests handled by endpoint/method/status.",
    ["endpoint", "method", "status"],
)

# tracks endpoint latency so we can see slow paths and build latency dashboards later.
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "aiiis_http_request_duration_seconds",
    "HTTP request latency in seconds by endpoint/method.",
    ["endpoint", "method"],
)


def observe_request(
    endpoint: str, method: str, status_code: int, duration_seconds: float
) -> None:
    HTTP_REQUESTS_TOTAL.labels(
        endpoint=endpoint,
        method=method,
        status=str(status_code),
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        endpoint=endpoint,
        method=method,
    ).observe(duration_seconds)
