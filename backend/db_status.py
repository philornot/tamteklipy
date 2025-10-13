"""
Sprawdza status bazy danych i wyświetla statystyki
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import logging
from app.core.database import SessionLocal, engine
from app.models import User, Clip, Award, AwardType
from sqlalchemy import inspect
from app.core.logging_config import setup_logging

# Spójna konfiguracja logowania
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)


def check_database_exists():
    """Sprawdza czy plik bazy istnieje"""
    db_file = Path("tamteklipy.db")
    return db_file.exists()


def check_tables_exist():
    """Sprawdza jakie tabele istnieją"""
    inspector = inspect(engine)
    return inspector.get_table_names()


def check_award_types_schema():
    """Sprawdza czy tabela award_types ma nowy schema"""
    inspector = inspect(engine)

    if 'award_types' not in inspector.get_table_names():
        return None

    columns = {col['name']: col['type'] for col in inspector.get_columns('award_types')}

    has_new_schema = all([
        'lucide_icon' in columns,
        'custom_icon_path' in columns,
        'is_personal' in columns,
        'is_system_award' in columns,
        'created_by_user_id' in columns
    ])

    return {
        'has_new_schema': has_new_schema,
        'columns': list(columns.keys())
    }


def get_statistics():
    """Pobiera statystyki z bazy"""
    db = SessionLocal()
    try:
        stats = {
            'users': db.query(User).count(),
            'clips': db.query(Clip).count(),
            'awards_given': db.query(Award).count(),
            'award_types_total': db.query(AwardType).count(),
            'system_awards': db.query(AwardType).filter(AwardType.is_system_award == True).count(),
            'personal_awards': db.query(AwardType).filter(AwardType.is_personal == True).count(),
            'custom_awards': db.query(AwardType).filter(
                AwardType.is_system_award == False,
                AwardType.is_personal == False
            ).count(),
            'admins': db.query(User).filter(User.is_admin == True).count()
        }
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return None
    finally:
        db.close()


def print_award_types():
    """Wyświetla wszystkie typy nagród"""
    db = SessionLocal()
    try:
        award_types = db.query(AwardType).order_by(
            AwardType.is_system_award.desc(),
            AwardType.is_personal.desc(),
            AwardType.name
        ).all()

        if not award_types:
            logger.info("  Brak typów nagród w bazie")
            return

        logger.info("\n  Typy nagród:")
        logger.info("  " + "=" * 80)

        for at in award_types:
            type_label = "SYSTEM" if at.is_system_award else ("PERSONAL" if at.is_personal else "CUSTOM")

            if at.lucide_icon:
                icon_info = f"lucide:{at.lucide_icon}"
            elif at.custom_icon_path:
                icon_info = f"custom:{Path(at.custom_icon_path).name}"
            else:
                icon_info = "NO ICON"

            creator = db.query(User).filter(User.id == at.created_by_user_id).first()
            creator_name = f"by {creator.username}" if creator else "system"

            logger.info(f"  [{type_label:8}] {at.display_name:25} | {icon_info:20} | {at.color} | {creator_name}")

        logger.info("  " + "=" * 80)

    except Exception as e:
        logger.error(f"Error listing award types: {e}")
    finally:
        db.close()


def print_users():
    """Wyświetla wszystkich użytkowników"""
    db = SessionLocal()
    try:
        users = db.query(User).all()

        if not users:
            logger.info("  Brak użytkowników w bazie")
            return

        logger.info("\n  Użytkownicy:")
        logger.info("  " + "=" * 80)

        for user in users:
            admin_badge = "[ADMIN]" if user.is_admin else ""
            personal_award = db.query(AwardType).filter(
                AwardType.created_by_user_id == user.id,
                AwardType.is_personal == True
            ).first()

            clips_count = db.query(Clip).filter(Clip.uploader_id == user.id).count()
            awards_given = db.query(Award).filter(Award.user_id == user.id).count()

            logger.info(f"  {user.username:15} | {user.email:30} | {admin_badge:8}")

            if personal_award:
                logger.info(f"                  | Osobista nagroda: {personal_award.display_name}")

            logger.info(f"                  | Klipy: {clips_count} | Przyznane nagrody: {awards_given}")
            logger.info("")

        logger.info("  " + "=" * 80)

    except Exception as e:
        logger.error(f"Error listing users: {e}")
    finally:
        db.close()


def main():
    """Główna funkcja sprawdzająca status"""

    logger.info("" + "=" * 80)
    logger.info("STATUS BAZY DANYCH TAMTEKLIPY")
    logger.info("" + "=" * 80)

    # 1. Sprawdź czy baza istnieje
    db_exists = check_database_exists()
    logger.info(f"Plik bazy danych: {'EXISTS' if db_exists else 'NOT FOUND'}")

    if not db_exists:
        logger.warning("\nBaza danych nie istnieje!")
        logger.info("Uruchom: python hard_reset.py")
        return

    # 2. Sprawdź tabele
    tables = check_tables_exist()
    logger.info(f"Tabele w bazie: {len(tables)}")
    logger.info(f"  {', '.join(tables)}")

    # 3. Sprawdź schema award_types
    if 'award_types' in tables:
        schema_info = check_award_types_schema()

        if schema_info:
            if schema_info['has_new_schema']:
                logger.info("\nSchema award_types: NOWY (z lucide icons)")
            else:
                logger.warning("\nSchema award_types: STARY (z emotkami)")
                logger.warning("Uruchom: python hard_reset.py")
                logger.info(f"Kolumny: {', '.join(schema_info['columns'])}")

    # 4. Sprawdź schema users
    if 'users' in tables:
        inspector = inspect(engine)
        user_columns = {col['name'] for col in inspector.get_columns('users')}

        if 'is_admin' in user_columns:
            logger.info("Schema users: NOWY (z is_admin)")
        else:
            logger.warning("Schema users: STARY (bez is_admin)")

    # 5. Statystyki
    stats = get_statistics()

    if stats:
        logger.info("\nSTATYSTYKI:")
        logger.info(f"  Użytkownicy: {stats['users']} (w tym {stats['admins']} adminów)")
        logger.info(f"  Klipy: {stats['clips']}")
        logger.info(f"  Przyznane nagrody: {stats['awards_given']}")
        logger.info(f"  Typy nagród: {stats['award_types_total']}")
        logger.info(f"    - Systemowe: {stats['system_awards']}")
        logger.info(f"    - Osobiste: {stats['personal_awards']}")
        logger.info(f"    - Custom: {stats['custom_awards']}")

        # Sprawdź czy każdy user ma osobistą nagrodę
        if stats['users'] > 0 and stats['personal_awards'] != stats['users']:
            logger.warning(f"\nProblem: {stats['users']} użytkowników, ale {stats['personal_awards']} osobistych nagród!")
            logger.warning("Powinno być: 1 osobista nagroda = 1 user")
        elif stats['users'] > 0:
            logger.info("\nKażdy użytkownik ma swoją osobistą nagrodę")

    # 6. Lista award types
    if stats and stats['award_types_total'] > 0:
        print_award_types()

    # 7. Lista użytkowników
    if stats and stats['users'] > 0:
        print_users()

    logger.info("" + "=" * 80)
    logger.info("Sprawdzanie zakończone")
    logger.info("" + "=" * 80)


if __name__ == "__main__":
    main()
