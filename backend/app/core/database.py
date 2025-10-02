"""
Konfiguracja bazy danych SQLAlchemy
"""
from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Tworzenie engine dla SQLite
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # Wymagane dla SQLite
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Bazowa klasa dla modeli
Base = declarative_base()


def get_db():
    """
    Dependency do pobierania sesji bazy danych w endpointach

    Yields:
        Session: Sesja bazy danych
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
