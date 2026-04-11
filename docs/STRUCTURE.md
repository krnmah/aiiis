# Project Folder Structure

This document explains how the repository is organized and why each area exists.

## Top-Level Layout

```text
aiiis/
├── app/                 # Application source code
├── scripts/             # Utility scripts (checks, simulators)
├── tests/               # Unit + integration tests
├── docker/              # Container and observability stack configs
├── ci/                  # Jenkins pipeline definition
├── docs/                # Architecture and reference documentation
├── .github/workflows/   # GitHub Actions pipeline
├── .env.example         # Environment variable template
├── requirements.txt     # Python dependencies
├── Makefile             # Common dev/ops commands
└── README.md            # Project overview and quick start
```

## Source Code Structure (`app/`)

```text
app/
├── api/
│   ├── routes/          # FastAPI route handlers (health, logs, llm, incidents, metrics)
│   └── schemas/         # Pydantic request/response models
├── cache/               # Redis cache integration
├── core/                # App config + logging setup
├── db/                  # DB engine/session and models
├── embeddings/          # Embedding model + vector generation
├── llm/                 # Provider abstraction + concrete providers
├── metrics/             # Prometheus metrics definitions/helpers
├── services/            # Business logic for ingestion, retrieval, analysis
├── vector_store/        # Vector search data access helpers
└── main.py              # FastAPI entrypoint
```

## Interactive Component Guide

<details>
<summary><strong>API Layer</strong></summary>

- purpose: expose stable HTTP contracts
- key files: `app/api/routes`, `app/api/schemas`
- notable endpoints: `/logs`, `/logs/similar`, `/incidents`, `/llm/test`, `/llm/compare`

</details>

<details>
<summary><strong>Services Layer</strong></summary>

- purpose: keep business logic independent from transport layer
- responsibilities: log ingestion, retrieval orchestration, incident analysis, provider orchestration

</details>

<details>
<summary><strong>LLM Layer</strong></summary>

- purpose: provider abstraction and swap flexibility
- providers: Ollama, Hugging Face, OpenAI
- resilience: retry/backoff for transient failures

</details>

<details>
<summary><strong>Ops and Quality</strong></summary>

- CI: GitHub Actions + Jenkins
- observability: Prometheus + Grafana under `docker/`
- tests: `tests/unit` and `tests/integration`

</details>

## Why This Structure Works

- separation of concerns: routes, services, providers, and infrastructure are isolated
- provider extensibility: adding new LLMs does not require rewriting route logic
- testability: business logic is test-friendly and mock-friendly
- production readiness: includes caching, metrics, CI/CD, and container orchestration