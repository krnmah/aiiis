from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_database_url, get_settings

settings = get_settings()
DATABASE_URL = get_database_url(settings)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": settings.db_connect_timeout_seconds},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


def initialize_database() -> None:
    with engine.begin() as connection:
        # first thing: make sure pgvector extension exists in this database.
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    # create all SQLAlchemy tables (no-op if they already exist).
    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        # this keeps old databases compatible by adding the embedding column when missing.
        connection.execute(
            text(
                "ALTER TABLE logs "
                f"ADD COLUMN IF NOT EXISTS embedding vector({settings.embedding_dimension})"
            )
        )

        # this index helps similarity search once the table starts growing.
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS logs_embedding_ivfflat_idx "
                "ON logs USING ivfflat (embedding vector_cosine_ops)"
            )
        )
