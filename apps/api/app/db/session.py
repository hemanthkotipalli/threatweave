from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.db.base  # noqa: F401 - Ensure all ORM models are registered in mapper registry
from app.core.config import settings

# Create engine using the database connection URL from settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Proactively test connections before checking them out
)

# Configure the local sessionmaker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a SQLAlchemy session.
    Guarantees cleanup and session close in a finally block.

    Yields:
        Session: The local database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
