"""
Inicjalizacja bazy danych - tworzenie tabel
"""
import logging

from app.core.database import engine, Base, check_database_connection, get_database_info
from app.models import User  # Import wszystkich modeli

logger = logging.getLogger(__name__)


def init_db():
    """
    Tworzy wszystkie tabele w bazie danych
    """
    logger.info("Sprawdzanie połączenia z bazą danych...")

    if not check_database_connection():
        logger.error("Nie można połączyć się z bazą danych!")
        return False

    logger.info("Tworzenie tabel w bazie danych...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tabele utworzone pomyślnie!")

    # Wyświetl informacje o bazie
    db_info = get_database_info()
    logger.info(f"SQLite version: {db_info.get('sqlite_version')}")
    logger.info(f"Tabele w bazie: {db_info.get('tables')}")

    return True


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
