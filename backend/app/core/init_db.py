"""
Inicjalizacja bazy danych — tworzenie tabel
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
    seed_system_awards()

    # Wyświetl informacje o bazie
    db_info = get_database_info()
    logger.info(f"SQLite version: {db_info.get('sqlite_version')}")
    logger.info(f"Tabele w bazie: {db_info.get('tables')}")

    return True


def seed_system_awards():
    """Seeduje systemowe typy nagród jeśli nie istnieją"""
    db = SessionLocal()
    try:
        existing_count = db.query(AwardType).filter(AwardType.is_system_award == True).count()
        if existing_count > 0:
            logger.info(f"Systemowe AwardTypes już istnieją ({existing_count}), pomijam seedowanie")
            return

        system_awards = [
            AwardType(
                name="award:epic_clip",
                display_name="Epic Clip",
                description="Za epicki moment w grze",
                lucide_icon="flame",
                color="#FF4500",
                is_system_award=True,
                is_personal=False
            ),
            AwardType(
                name="award:funny",
                display_name="Funny Moment",
                description="Za zabawną sytuację",
                lucide_icon="laugh",
                color="#FFD700",
                is_system_award=True,
                is_personal=False
            ),
            AwardType(
                name="award:pro_play",
                display_name="Pro Play",
                description="Za profesjonalną zagrywkę",
                lucide_icon="star",
                color="#4169E1",
                is_system_award=True,
                is_personal=False
            ),
            AwardType(
                name="award:clutch",
                display_name="Clutch",
                description="Za clutch w trudnej sytuacji",
                lucide_icon="zap",
                color="#32CD32",
                is_system_award=True,
                is_personal=False
            ),
            AwardType(
                name="award:wtf",
                display_name="WTF Moment",
                description="Za totalnie nieoczekiwaną sytuację",
                lucide_icon="eye",
                color="#9370DB",
                is_system_award=True,
                is_personal=False
            )
        ]

        for award_type in system_awards:
            db.add(award_type)
            logger.info(f"Created system AwardType: {award_type.name}")

        db.commit()
        logger.info(f"Seedowano {len(system_awards)} systemowych typów nagród")

    except Exception as e:
        db.rollback()
        logger.error(f"Błąd podczas seedowania AwardTypes: {e}")
    finally:
        db.close()


def create_personal_award_for_user(user_id: int, username: str, display_name: str = None) -> AwardType:
    """
    Tworzy osobistą nagrodę dla nowego użytkownika

    Args:
        user_id: ID użytkownika
        username: Username użytkownika
        display_name: Wyświetlana nazwa użytkownika

    Returns:
        AwardType: Utworzona nagroda
    """
    db = SessionLocal()
    try:
        # Sprawdź czy użytkownik już ma osobistą nagrodę
        existing = db.query(AwardType).filter(
            AwardType.created_by_user_id == user_id,
            AwardType.is_personal == True
        ).first()

        if existing:
            logger.info(f"User {username} already has personal award: {existing.name}")
            return existing

        # Utwórz osobistą nagrodę
        personal_award = AwardType(
            name=f"award:personal_{username}",
            display_name=f"Nagroda {display_name or username}",
            description=f"Osobista nagroda użytkownika {display_name or username}",
            lucide_icon="award",  # Default icon
            color="#FF6B9D",  # Pink color for personal awards
            created_by_user_id=user_id,
            is_system_award=False,
            is_personal=True
        )

        db.add(personal_award)
        db.commit()
        db.refresh(personal_award)

        logger.info(f"Created personal award for {username}: {personal_award.name}")

        return personal_award

    except Exception as e:
        db.rollback()
        logger.error(f"Błąd podczas tworzenia osobistej nagrody: {e}")
        raise
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
