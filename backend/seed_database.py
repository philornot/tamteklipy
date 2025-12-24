"""
Seed database with test data for development
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.clip import Clip
from app.models.award import Award
from app.models.award_type import AwardType
from app.core.security import hash_password
from app.core.init_db import create_personal_award_for_user
from sqlalchemy import inspect
import logging
from app.core.logging_config import setup_logging

# Spójna konfiguracja logowania
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)


def check_database_exists():
    """Sprawdź czy baza i tabele istnieją"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    required_tables = ['users', 'clips', 'awards', 'award_types']
    missing_tables = [t for t in required_tables if t not in tables]

    if missing_tables:
        logger.warning(f"Brakujące tabele: {', '.join(missing_tables)}")
        logger.warning("\nRozwiązanie:")
        logger.warning("   python hard_reset.py")
        logger.warning("   python seed_database.py --clear")
        return False

    return True


def clear_database(db):
    """Usuwa wszystkie dane z bazy (opcjonalnie)"""
    logger.warning("Usuwanie wszystkich danych z bazy...")
    db.query(Award).delete()
    db.query(Clip).delete()
    db.query(AwardType).delete()
    db.query(User).delete()
    db.commit()
    logger.info("Baza danych wyczyszczona")


def seed_users(db):
    """Tworzy testowych użytkowników z osobistymi nagrodami"""
    logger.info("Tworzenie testowych użytkowników...")

    users_data = [
        {
            "username": "philornot",
            "email": None,
            "password": "HasloFilipa",
            "full_name": "Filip",
            "is_admin": True,
            "award_scopes": []
        }
    ]

    created_users = []
    for user_data in users_data:
        # Sprawdź czy użytkownik już istnieje
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if existing:
            logger.info(f"  Użytkownik {user_data['username']} już istnieje, pomijam")
            created_users.append(existing)

            # Upewnij się że ma osobistą nagrodę
            create_personal_award_for_user(
                db,
                existing.id,
                existing.username,
                existing.full_name or existing.username
            )
            continue

        user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            full_name=user_data["full_name"],
            is_active=True,
            is_admin=user_data["is_admin"],
            award_scopes=user_data["award_scopes"]
        )

        db.add(user)
        db.flush()  # Get user.id

        # Utwórz osobistą nagrodę dla użytkownika
        create_personal_award_for_user(
            db,
            user.id,
            user.username,
            user.full_name or user.username
        )

        created_users.append(user)
        logger.info(f"  {user_data['username']} (admin: {user_data['is_admin']}, personal award created)")

    db.commit()
    logger.info(f"Utworzono {len(created_users)} użytkowników z osobistymi nagrodami\n")

    return created_users


def print_summary(db):
    """Wyświetla podsumowanie seedowania"""
    logger.info("=" * 60)
    logger.info("PODSUMOWANIE BAZY DANYCH")
    logger.info("=" * 60)

    users_count = db.query(User).count()
    clips_count = db.query(Clip).count()
    awards_count = db.query(Award).count()
    award_types_count = db.query(AwardType).count()
    system_awards = db.query(AwardType).filter(AwardType.is_system_award == True).count()
    personal_awards = db.query(AwardType).filter(AwardType.is_personal == True).count()
    custom_awards = db.query(AwardType).filter(
        AwardType.is_system_award == False,
        AwardType.is_personal == False
    ).count()

    logger.info(f"Użytkownicy: {users_count}")
    logger.info(f"Klipy: {clips_count}")
    logger.info(f"Przyznane nagrody: {awards_count}")
    logger.info(f"Typy nagród (ogółem): {award_types_count}")
    logger.info(f"  - Systemowe: {system_awards}")
    logger.info(f"  - Osobiste: {personal_awards}")
    logger.info(f"  - Custom (publiczne): {custom_awards}")
    logger.info("")

    logger.info("Testowe konta:")
    users = db.query(User).all()
    for user in users:
        admin_badge = " [ADMIN]" if user.is_admin else ""
        personal_award = db.query(AwardType).filter(
            AwardType.created_by_user_id == user.id,
            AwardType.is_personal == True
        ).first()
        personal_name = personal_award.display_name if personal_award else "brak"
        logger.info(f"  {user.username:12} | {admin_badge}")
        logger.info(f"               | Osobista nagroda: {personal_name}")

    logger.info("")

    logger.info("Typy nagród:")
    award_types = db.query(AwardType).order_by(AwardType.is_system_award.desc(), AwardType.name).all()
    for at in award_types:
        type_label = "SYSTEM" if at.is_system_award else ("PERSONAL" if at.is_personal else "CUSTOM")
        icon_info = f"lucide:{at.lucide_icon}" if at.lucide_icon else f"custom:{at.custom_icon_path}"
        creator = db.query(User).filter(User.id == at.created_by_user_id).first()
        creator_name = f"by {creator.username}" if creator else ""
        logger.info(f"  [{type_label:8}] {at.display_name:25} | {icon_info:20} | {creator_name}")

    logger.info("")
    logger.info("=" * 60)


def main(clear_first=False):
    """Główna funkcja seedowania"""

    # Sprawdź czy baza istnieje
    if not check_database_exists():
        logger.warning("\nBaza danych nie istnieje lub jest niepełna!")
        return

    db = SessionLocal()

    try:
        logger.info("Rozpoczynam seedowanie bazy danych...\n")

        if clear_first:
            clear_database(db)

        users = seed_users(db)

        print_summary(db)

        logger.info("Seedowanie zakończone pomyślnie!")

    except Exception as e:
        logger.warning(f"Błąd podczas seedowania: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed database with test data")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all data before seeding"
    )

    args = parser.parse_args()

    main(clear_first=args.clear)
