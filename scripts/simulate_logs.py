import argparse
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx


@dataclass(frozen=True)
class LogTemplate:
    service_name: str
    level: str
    message: str


PAYMENT_TIMEOUT_TEMPLATES = [
    LogTemplate("checkout", "INFO", "checkout request started for cart {cart_id}"),
    LogTemplate("payments", "WARNING", "retry attempt {retry} for payment authorization"),
    LogTemplate("payments", "ERROR", "upstream timeout from payment gateway after {latency_ms}ms"),
    LogTemplate("orders", "ERROR", "order confirmation delayed waiting on payment trace"),
    LogTemplate("gateway", "CRITICAL", "error rate spike detected on /payments/authorize"),
]

AUTH_OUTAGE_TEMPLATES = [
    LogTemplate("auth", "INFO", "token validation request received for user {user_id}"),
    LogTemplate("auth", "WARNING", "jwt signature verification slow path triggered"),
    LogTemplate("auth", "ERROR", "jwks fetch timeout from identity provider"),
    LogTemplate("gateway", "ERROR", "401 surge detected for authenticated routes"),
    LogTemplate("checkout", "WARNING", "user session refresh failed due to auth dependency"),
]

DB_SATURATION_TEMPLATES = [
    LogTemplate("orders", "INFO", "persist order transaction started"),
    LogTemplate("orders", "WARNING", "connection pool usage high: {pool_usage}%"),
    LogTemplate("orders", "ERROR", "database timeout while committing transaction"),
    LogTemplate("inventory", "ERROR", "read replica lag exceeded {replica_lag_ms}ms"),
    LogTemplate("payments", "WARNING", "idempotency check delayed by database wait"),
]


def _render_message(template: str) -> str:
    return template.format(
        cart_id=random.randint(1000, 9999),
        retry=random.randint(1, 4),
        latency_ms=random.randint(800, 3500),
        user_id=random.randint(10000, 99999),
        pool_usage=random.randint(78, 99),
        replica_lag_ms=random.randint(120, 1200),
    )


def _pick_templates(scenario: str) -> list[LogTemplate]:
    if scenario == "payment-timeout":
        return PAYMENT_TIMEOUT_TEMPLATES
    if scenario == "auth-outage":
        return AUTH_OUTAGE_TEMPLATES
    if scenario == "db-saturation":
        return DB_SATURATION_TEMPLATES

    return PAYMENT_TIMEOUT_TEMPLATES + AUTH_OUTAGE_TEMPLATES + DB_SATURATION_TEMPLATES


def build_log_payloads(count: int, scenario: str) -> list[dict[str, str]]:
    templates = _pick_templates(scenario)
    now = datetime.now(timezone.utc)

    payloads: list[dict[str, str]] = []
    for idx in range(count):
        template = random.choice(templates)
        trace_id = f"sim-{uuid4().hex[:12]}"
        timestamp = now - timedelta(seconds=(count - idx))
        payloads.append(
            {
                "service_name": template.service_name,
                "level": template.level,
                "message": _render_message(template.message),
                "trace_id": trace_id,
                "timestamp": timestamp.isoformat(),
            }
        )

    return payloads


def run_simulation(
    base_url: str,
    count: int,
    scenario: str,
    delay_ms: int,
    timeout_seconds: int,
) -> int:
    payloads = build_log_payloads(count=count, scenario=scenario)
    endpoint = f"{base_url.rstrip('/')}/logs"

    success = 0
    with httpx.Client(timeout=timeout_seconds) as client:
        for payload in payloads:
            try:
                response = client.post(endpoint, json=payload)
                response.raise_for_status()
                success += 1
            except httpx.HTTPError as exc:
                print(f"log ingestion failed for trace_id={payload['trace_id']}: {exc}")

            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

    failed = count - success
    print(
        "simulation_complete "
        f"scenario={scenario} total={count} succeeded={success} failed={failed}"
    )
    return 0 if failed == 0 else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate realistic logs through /logs API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--count", type=int, default=50, help="Number of logs to generate")
    parser.add_argument(
        "--scenario",
        choices=["payment-timeout", "auth-outage", "db-saturation", "mixed"],
        default="mixed",
        help="Simulation scenario",
    )
    parser.add_argument("--delay-ms", type=int, default=0, help="Delay between requests")
    parser.add_argument("--timeout-seconds", type=int, default=15, help="HTTP timeout")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for repeatability")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    random.seed(args.seed)

    if args.count < 1:
        print("count must be >= 1")
        return 1

    return run_simulation(
        base_url=args.base_url,
        count=args.count,
        scenario=args.scenario,
        delay_ms=max(0, args.delay_ms),
        timeout_seconds=max(1, args.timeout_seconds),
    )


if __name__ == "__main__":
    raise SystemExit(main())
