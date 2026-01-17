"""
Database configuration with proper session management for production.

Critical fixes for Oracle Cloud deployment:
- Proper connection pooling with timeouts
- Explicit session cleanup
- WAL mode for SQLite (prevents locks)
- Connection pool pre-ping (detects stale connections)
"""
import logging
import time
from contextlib import contextmanager

from app.core.config import settings
from sqlalchemy import create_engine, pool
from sqlalchemy import event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

# ============================================================================
# SQLite Configuration for Production
# ============================================================================

# Connection string with optimizations
if settings.environment == "production":
    # Production: use database_url directly
    # It should be absolute path in .env: DATABASE_URL=sqlite:////absolute/path/to/db.db
    SQLALCHEMY_DATABASE_URL = settings.database_url

    # Engine with production settings
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,

        # Connection pooling (important for concurrent requests)
        poolclass=pool.StaticPool,  # Single connection pool for SQLite

        # Timeouts
        connect_args={
            "check_same_thread": False,  # Allow multi-threading
            "timeout": 30.0,  # 30s timeout for locks
        },

        # Pool settings
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1h

        # Logging
        echo=False,  # Set to True for SQL query debugging
    )

else:
    # Development: relative path
    SQLALCHEMY_DATABASE_URL = "sqlite:///./tamteklipy.db"

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        echo=False,
    )


# ============================================================================
# Enable SQLite WAL Mode (Write-Ahead Logging)
# ============================================================================
# WAL mode significantly improves concurrency by allowing:
# - Multiple readers + 1 writer simultaneously
# - No database locks on reads
#
# This is CRITICAL for production with multiple workers!

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Configure SQLite for better concurrency and performance.

    Executed automatically on each new connection.
    """
    cursor = dbapi_conn.cursor()

    # Enable WAL mode (Write-Ahead Logging)
    cursor.execute("PRAGMA journal_mode=WAL")

    # Set busy timeout (wait 30s before raising "database is locked")
    cursor.execute("PRAGMA busy_timeout=30000")

    # Synchronous mode (balance between safety and speed)
    cursor.execute("PRAGMA synchronous=NORMAL")

    # Cache size (negative = KB, 64MB cache)
    cursor.execute("PRAGMA cache_size=-64000")

    # Foreign keys enforcement
    cursor.execute("PRAGMA foreign_keys=ON")

    cursor.close()

    logger.debug("SQLite optimizations applied")


# ============================================================================
# Session Factory
# ============================================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Don't expire objects after commit
)

Base = declarative_base()


# ============================================================================
# Dependency for FastAPI Routes
# ============================================================================

def get_db() -> Session:
    """
    FastAPI dependency that provides DB session.

    Usage in routes:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()

    Features:
    - Automatic session cleanup (even if exception occurs)
    - Proper rollback on errors
    - Connection returned to pool after request
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # Rollback on any error
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        # ALWAYS close the session (returns connection to pool)
        db.close()


# ============================================================================
# Context Manager for Manual Session Usage
# ============================================================================

@contextmanager
def get_db_context():
    """
    Context manager for using DB outside of FastAPI routes.

    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
            # ... do work ...
            db.commit()

    Benefits:
    - Automatic cleanup (even on exceptions)
    - Explicit commit required
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database context error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries (> 100ms)"""
    conn.info.setdefault('query_start_time', []).append(time.time())


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries"""
    total = time.time() - conn.info['query_start_time'].pop(-1)

    if total > 0.1:  # Log queries > 100ms
        logger.warning(
            f"Slow query ({total:.2f}s): {statement[:200]}"
        )


# ============================================================================
# Health Check
# ============================================================================

def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection OK, False otherwise

    Usage in health endpoint:
        if not check_db_connection():
            return {"status": "unhealthy", "database": "error"}
    """
    try:
        from sqlalchemy import text
        with get_db_context() as db:
            db.execute(text("SELECT 1"))
        logger.info("Database connection OK")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
