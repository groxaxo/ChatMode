"""
Database connection and session management.
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base, create_all_tables

# Database URL from environment, defaulting to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/chatmode.db")

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("SQL_ECHO", "").lower() == "true",
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL/MySQL settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=os.getenv("SQL_ECHO", "").lower() == "true",
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency for FastAPI to get database session.

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database session.

    Usage:
        with get_db_context() as db:
            db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Create all tables
    create_all_tables(engine)
    _apply_sqlite_migrations()
    print(f"Database initialized: {DATABASE_URL}")


def _apply_sqlite_migrations() -> None:
    """Apply lightweight SQLite migrations for new columns."""
    if not DATABASE_URL.startswith("sqlite"):
        return

    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(agents)"))
        columns = {row[1] for row in result.fetchall()}
        if "sleep_seconds" not in columns:
            conn.execute(text("ALTER TABLE agents ADD COLUMN sleep_seconds FLOAT"))
            conn.commit()

        # Migrate agent_permissions table
        result = conn.execute(text("PRAGMA table_info(agent_permissions)"))
        columns = {row[1] for row in result.fetchall()}
        if "filter_enabled" not in columns:
            conn.execute(
                text("ALTER TABLE agent_permissions ADD COLUMN filter_enabled BOOLEAN")
            )
            conn.commit()
        if "blocked_words" not in columns:
            conn.execute(
                text("ALTER TABLE agent_permissions ADD COLUMN blocked_words JSON")
            )
            conn.commit()
        if "filter_action" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE agent_permissions ADD COLUMN filter_action VARCHAR(20)"
                )
            )
            conn.commit()
        if "filter_message" not in columns:
            conn.execute(
                text("ALTER TABLE agent_permissions ADD COLUMN filter_message TEXT")
            )
            conn.commit()


def test_connection():
    """Test database connection."""
    try:
        with get_db_context() as db:
            db.execute("SELECT 1")
        print("Database connection successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


# Auto-initialize on import (for simple deployments)
if os.getenv("AUTO_INIT_DB", "true").lower() == "true":
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Auto database init failed: {e}")
