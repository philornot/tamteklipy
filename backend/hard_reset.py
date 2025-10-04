"""
Hard reset bazy danych - usuwa wszystko i tworzy od nowa
UWAGA: Usuwa WSZYSTKIE dane!
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import logging
from app.core.database import engine, Base
from app.core.init_db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def hard_reset():
    """
    Kompletny reset bazy danych:
    1. Usuwa wszystkie tabele
    2. Usuwa plik bazy danych
    3. Tworzy wszystko od nowa
    """

    logger.warning("=" * 60)
    logger.warning("⚠️  HARD RESET BAZY DANYCH")
    logger.warning("=" * 60)
    logger.warning("To usunie WSZYSTKIE dane!")
    logger.warning("")

    # Potwierdzenie
    response = input("Czy na pewno chcesz kontynuować? (wpisz 'TAK'): ")
    if response != "TAK":
        logger.info("Anulowano reset")
        return

    logger.info("")
    logger.info("Rozpoczynam hard reset...")

    try:
        # 1. Usuń plik bazy danych (nawet jeśli uszkodzony)
        db_file = Path("tamteklipy.db")
        if db_file.exists():
            logger.info("1. Usuwam plik bazy danych...")
            try:
                db_file.unlink()
                logger.info("   ✓ Plik bazy danych usunięty")
            except Exception as e:
                logger.warning(f"   Błąd przy usuwaniu: {e}")
                logger.info("   Próbuję wymusić usunięcie...")
                import os
                try:
                    os.remove(str(db_file))
                    logger.info("   ✓ Plik usunięty wymuszone")
                except Exception as e2:
                    logger.error(f"   ❌ Nie można usunąć pliku: {e2}")
                    logger.error("   Usuń plik ręcznie: del tamteklipy.db")
                    return
        else:
            logger.info("1. Plik bazy nie istnieje (OK)")

        # 2. Usuń wszystkie tabele (jeśli baza działała)
        try:
            logger.info("2. Czyszczę metadane...")
            Base.metadata.drop_all(bind=engine)
            logger.info("   ✓ Metadane wyczyszczone")
        except Exception as e:
            logger.warning(f"   Pominięto (baza była uszkodzona): {e}")

        # 3. Utwórz bazę od nowa
        logger.info("3. Tworzę nową bazę danych...")
        init_db()
        logger.info("   ✓ Nowa baza utworzona")

        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ HARD RESET ZAKOŃCZONY POMYŚLNIE!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Następne kroki:")
        logger.info("  1. python seed_database.py --clear")
        logger.info("     (utworzy testowych użytkowników i dane)")
        logger.info("")
        logger.info("  2. python -m uvicorn app.main:app --reload")
        logger.info("     (uruchomi serwer)")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Błąd podczas hard reset: {e}")
        raise


if __name__ == "__main__":
    hard_reset()
