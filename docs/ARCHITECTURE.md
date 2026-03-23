# AI Incident Investigation System — Architecture

## High-Level System Architecture

```mermaid
flowchart TD

A["Application Services
(Payment, Auth, Orders)"] --> B[Log Ingestion API
FastAPI]

B --> C[PostgreSQL
Raw Log Storage]

C --> D[Embedding Generator
Sentence Transformers]

D --> E[Vector Store
pgvector]

F[User Incident Query] --> G[Retrieval Engine]

G --> E

E --> H[Relevant Logs]

H --> I[LLM Provider Layer]

I --> J[Incident Analyzer]

J --> K[Incident Report Generator]

K --> L[Investigation API / Dashboard]
```

---

## LLM Provider Layer (Abstraction)

```mermaid
flowchart LR

A[LLM Interface]

A --> B[Ollama\nLocal Models]
A --> C[HuggingFace API]
A --> D[OpenAI API]
```

---

## CI/CD Architecture

```mermaid
flowchart TD

A[Developer Push Code\nGitHub Repository]

A --> B[GitHub Actions Pipeline]

B --> C[Run Unit Tests]
B --> D[Run Lint & Format Check]
B --> E[Build Docker Image]
B --> F[Basic Health Check]

A --> G[Jenkins Pipeline]

G --> H["Run Integration Tests\n(PostgreSQL + Redis)"]
G --> I[Advanced Validation\nEnd-to-End Flow]
G --> J[Docker Container Execution Test]

E --> K[Docker Image Ready]

K --> L[Deployment Ready Artifact]
```

---

## CI/CD Responsibility Separation

### GitHub Actions (Fast Feedback)

- Triggered on every push / PR
- Runs:
  - Unit tests
  - Lint checks (flake8, black)
  - Docker build
  - Basic health checks

Purpose:

- Quick validation
- Developer feedback
- Prevent broken commits

---

### Jenkins (Deeper Validation)

- Triggered via webhook or manually
- Runs:
  - Integration tests (DB + Redis)
  - End-to-end system tests
  - Container runtime validation

Purpose:

- Simulate production environment
- Validate system reliability
- Advanced pipeline control

---

## Observability Layer

```mermaid
flowchart TD

A[FastAPI Application] --> B[Prometheus Metrics]

B --> C[Grafana Dashboards]
```

Metrics Collected:

- Log ingestion rate
- Query latency
- LLM response time
- Error rates

---

## Data Flow Summary

```text
Logs → Ingestion API → PostgreSQL → Embeddings → pgvector
→ Retrieval → LLM → Incident Analysis → Report Generation
```

---

## CI/CD Flow Summary

```text
Code Push → GitHub Actions (fast checks)
         → Jenkins (deep validation)
         → Docker Image → Deployment Ready
```

---

## Key Engineering Highlights

- Distributed log processing pipeline
- AI-powered root cause analysis
- Vector similarity search using pgvector
- LLM abstraction supporting multiple providers
- Dual CI/CD pipelines (GitHub Actions + Jenkins)
- Observability with Prometheus and Grafana
