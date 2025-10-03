"""
Konfiguracja bazy danych SQLAlchemy
"""
import logging

from app.core.config import settings
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Tworzenie engine dla SQLite
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Wymagane dla SQLite
    pool_pre_ping=True,  # Sprawdza połączenie przed użyciem
    echo=False  # Ustaw True dla debugowania SQL queries
)


# Event listener - włącz foreign keys dla SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Włącza foreign key constraints dla SQLite"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Bazowa klasa dla modeli
Base = declarative_base()


def get_db():
    """
    Dependency do pobierania sesji bazy danych w endpointach

    Użycie:
        @app.get("/users")
        async def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users

    Yields:
        Session: Sesja bazy danych
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Sprawdza czy połączenie z bazą danych działa

    Returns:
        bool: True jeśli połączenie działa, False w przeciwnym razie
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection OK")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_database_info() -> dict:
    """
    Pobiera informacje o bazie danych

    Returns:
        dict: Informacje o bazie (wersja SQLite, rozmiar, liczba tabel)
    """
    try:
        db = SessionLocal()

        # Wersja SQLite
        version = db.execute(text("SELECT sqlite_version()")).scalar()

        # Lista tabel
        tables = db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        ).fetchall()

        db.close()

        return {
            "sqlite_version": version,
            "tables_count": len(tables),
            "tables": [table[0] for table in tables]
        }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {}
