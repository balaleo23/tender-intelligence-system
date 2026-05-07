from contextlib import contextmanager

from sqlalchemy import create_engine ,text
from sqlalchemy.orm import sessionmaker

from ingestion_engine.config import settings
from ingestion_engine.utils.logger import get_logger

logger = get_logger(__name__)

engine = create_engine(str(settings.postgres_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist. Call once at startup."""
    from ingestion_engine.storage.models import Base  # avoid circular import

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialised")


def check_connection() -> None:
    """Verify the DB is reachable. Call at startup to fail fast."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Postgres connection OK")


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
