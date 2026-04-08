from uuid import uuid4

import pytest

from app.cache.redis_cache import get_cache_client


def _require_cache_client():
    client = get_cache_client()
    if client is None:
        pytest.skip("Redis cache is disabled by configuration")

    try:
        # ping ensures the integration test verifies a real Redis connection.
        client._client.ping()  # noqa: SLF001
    except Exception as exc:
        pytest.skip(f"Redis not reachable for integration test: {exc}")

    return client


def test_redis_set_get_json_round_trip() -> None:
    cache = _require_cache_client()

    key = f"it:redis:{uuid4().hex}"
    payload = {
        "query": "integration redis test",
        "total": 1,
        "results": [{"id": 99, "similarity_score": 0.9}],
    }

    cache.set_json(key=key, payload=payload, ttl_seconds=60)
    loaded = cache.get_json(key)

    assert loaded is not None
    assert loaded["query"] == "integration redis test"
    assert loaded["results"][0]["id"] == 99
