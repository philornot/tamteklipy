"""
Inicjalizacja bazy danych - tworzenie tabel
"""
import logging

from app.core.database import engine, Base
from app.models import User  # Import wszystkich modeli

logger = logging.getLogger(__name__)


def init_db():
    """
    Tworzy wszystkie tabele w bazie danych
    """
    logger.info("Tworzenie tabel w bazie danych...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tabele utworzone pomyślnie!")


def drop_db():
    """
    Usuwa wszystkie tabele z bazy danych (OSTROŻNIE!)
    """
    logger.warning("UWAGA: Usuwanie wszystkich tabel z bazy danych!")
    Base.metadata.drop_all(bind=engine)
    logger.info("Tabele usunięte")


if __name__ == "__main__":
    # Możesz uruchomić ten skrypt bezpośrednio
    logging.basicConfig(level=logging.INFO)
    init_db()
