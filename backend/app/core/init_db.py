"""
Inicjalizacja bazy danych - tworzenie tabel
"""
import logging

from app.core.database import engine, Base, check_database_connection, get_database_info, SessionLocal
from app.models import User, Clip, Award
from app.models.award_type import AwardType

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

    # Seeduj podstawowe AwardTypes
    seed_award_types()

    # Wyświetl informacje o bazie
    db_info = get_database_info()
    logger.info(f"SQLite version: {db_info.get('sqlite_version')}")
    logger.info(f"Tabele w bazie: {db_info.get('tables')}")

    return True


def seed_award_types():
    """Seeduje podstawowe typy nagród jeśli nie istnieją"""
    db = SessionLocal()
    try:
        existing_count = db.query(AwardType).count()
        if existing_count > 0:
            logger.info(f"AwardTypes już istnieją ({existing_count}), pomijam seedowanie")
            return

        award_types = [
            AwardType(
                name="award:epic_clip",
                display_name="Epic Clip",
                description="Za epicki moment w grze",
                icon="🔥",
                color="#FF4500"
            ),
            AwardType(
                name="award:funny",
                display_name="Funny Moment",
                description="Za zabawną sytuację",
                icon="😂",
                color="#FFD700"
            ),
            AwardType(
                name="award:pro_play",
                display_name="Pro Play",
                description="Za profesjonalną zagrywkę",
                icon="⭐",
                color="#4169E1"
            ),
            AwardType(
                name="award:clutch",
                display_name="Clutch",
                description="Za clutch w trudnej sytuacji",
                icon="💪",
                color="#32CD32"
            ),
            AwardType(
                name="award:wtf",
                display_name="WTF Moment",
                description="Za totalnie nieoczekiwaną sytuację",
                icon="🤯",
                color="#9370DB"
            )
        ]

        for award_type in award_types:
            db.add(award_type)
            logger.debug(f"Created AwardType: {award_type.name}")

        db.commit()
        logger.debug(f"Seedowano {len(award_types)} typów nagród")

    except Exception as e:
        db.rollback()
        logger.error(f"Błąd podczas seedowania AwardTypes: {e}")
    finally:
        db.close()


def drop_db():
    """
    Usuwa wszystkie tabele z bazy danych (OSTROŻNIE!)
    """
    logger.warning("UWAGA: Usuwanie wszystkich tabel z bazy danych!")
    Base.metadata.drop_all(bind=engine)
    logger.info("Tabele usunięte")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
