# Project Folder Structure

aiiis
│
├── app/
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── logs.py                # Log ingestion endpoints
│   │       ├── incidents.py           # Incident query endpoints
│   │       └── health.py              # Health check endpoint
│   │
│   ├── services/
│   │   ├── ingestion_service.py       # Handles log ingestion
│   │   ├── retrieval_service.py       # Vector search logic
│   │   ├── incident_analyzer.py       # LLM-based analysis
│   │   └── report_generator.py        # Structured incident reports
│   │
│   ├── llm/
│   │   ├── base_provider.py           # Abstract LLM interface
│   │   ├── ollama_provider.py         # Local LLM (Ollama)
│   │   ├── huggingface_provider.py    # HF API integration
│   │   └── openai_provider.py         # OpenAI integration
│   │
│   ├── embeddings/
│   │   └── embedding_service.py       # Sentence-transformer embeddings
│   │
│   ├── vector_store/
│   │   └── pgvector_store.py          # Vector DB queries (pgvector)
│   │
│   ├── db/
│   │   ├── models.py                  # SQLAlchemy models
│   │   └── database.py                # DB connection/session
│   │
│   ├── core/
│   │   ├── config.py                  # Environment variables
│   │   └── logging_config.py          # Structured logging setup
│   │
│   ├── metrics/
│   │   └── prometheus.py              # Prometheus metrics
│   │
│   └── main.py                        # FastAPI app entry point
│
├── scripts/
│   ├── simulate_logs.py               # Generate fake logs
│   └── seed_data.py                   # Optional test data
│
├── tests/
│   ├── unit/
│   │   ├── test_services.py
│   │   ├── test_llm.py
│   │   └── test_embeddings.py
│   │
│   ├── integration/
│   │   ├── test_api.py
│   │   ├── test_db.py
│   │   └── test_pipeline.py
│   │
│   └── conftest.py
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml             # API + DB + Redis + Prometheus + Grafana
│   ├── docker-compose-test.yml        # Isolated test environment
│   │
│   ├── prometheus/
│   │   └── prometheus.yml
│   │
│   └── grafana/
│       └── dashboards.json
│
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions pipeline
│
├── ci/
│   └── Jenkinsfile                    # Jenkins pipeline
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── SETUP.md
│
├── .env.example
├── requirements.txt
├── README.md
└── alembic.ini