"""
Test permissions — sprawdza kto może przyznać jakie nagrody
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import logging
from app.core.database import SessionLocal
from app.models import User, AwardType
from app.core.logging_config import setup_logging

# Spójna konfiguracja logowania
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)


def test_user_permissions(username: str):
    """Test permissions dla konkretnego użytkownika"""
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            logger.error(f"Użytkownik '{username}' nie istnieje")
            return

        logger.info(f"\n{'=' * 80}")
        logger.info(f"UPRAWNIENIA UŻYTKOWNIKA: {user.username}")
        logger.info(f"{'=' * 80}")
        logger.info(f"Email: {user.email}")
        logger.info(f"Full name: {user.full_name}")
        logger.info(f"Admin: {'TAK' if user.is_admin else 'NIE'}")
        logger.info(f"Active: {'TAK' if user.is_active else 'NIE'}")

        # Pobierz wszystkie typy nagród
        award_types = db.query(AwardType).order_by(
            AwardType.is_system_award.desc(),
            AwardType.is_personal.desc(),
            AwardType.name
        ).all()

        can_give = []
        cannot_give = []

        for award in award_types:
            if user.can_give_award(award):
                can_give.append(award)
            else:
                cannot_give.append(award)

        # Wyświetl nagrody które MOŻE przyznać
        logger.info(f"\nMOŻE PRZYZNAĆ ({len(can_give)} nagród):")
        logger.info("-" * 80)

        for award in can_give:
            type_label = "SYSTEM" if award.is_system_award else ("PERSONAL" if award.is_personal else "CUSTOM")
            icon_info = f"lucide:{award.lucide_icon}" if award.lucide_icon else "custom"

            creator = db.query(User).filter(User.id == award.created_by_user_id).first()
            creator_info = f"by {creator.username}" if creator else "system"

            reason = ""
            if user.is_admin:
                reason = "[ADMIN]"
            elif award.is_system_award:
                reason = "[SYSTEM]"
            elif award.is_personal and award.created_by_user_id == user.id:
                reason = "[OWN PERSONAL]"
            elif not award.is_personal:
                reason = "[PUBLIC CUSTOM]"

            logger.info(f"  [{type_label:8}] {award.display_name:25} | {icon_info:20} | {creator_info:15} {reason}")

        # Wyświetl nagrody których NIE MOŻE przyznać
        if cannot_give:
            logger.info(f"\nNIE MOŻE PRZYZNAĆ ({len(cannot_give)} nagród):")
            logger.info("-" * 80)

            for award in cannot_give:
                type_label = "PERSONAL"  # Tylko personal może być zabronione
                icon_info = f"lucide:{award.lucide_icon}" if award.lucide_icon else "custom"

                creator = db.query(User).filter(User.id == award.created_by_user_id).first()
                creator_info = f"by {creator.username}" if creator else "system"

                logger.info(
                    f"  [{type_label:8}] {award.display_name:25} | {icon_info:20} | {creator_info:15} [OTHER'S PERSONAL]")

        logger.info(f"\n{'=' * 80}\n")

    except Exception as e:
        logger.error(f"Błąd: {e}")
    finally:
        db.close()


def test_all_permissions():
    """Test permissions dla wszystkich użytkowników"""
    db = SessionLocal()

    try:
        users = db.query(User).all()

        if not users:
            logger.error("Brak użytkowników w bazie")
            return

        logger.info(f"\n{'=' * 80}")
        logger.info(f"PODSUMOWANIE UPRAWNIEŃ WSZYSTKICH UŻYTKOWNIKÓW")
        logger.info(f"{'=' * 80}\n")

        # Pobierz typy nagród
        system_awards = db.query(AwardType).filter(AwardType.is_system_award == True).count()
        personal_awards = db.query(AwardType).filter(AwardType.is_personal == True).count()
        custom_awards = db.query(AwardType).filter(
            AwardType.is_system_award == False,
            AwardType.is_personal == False
        ).count()

        logger.info(f"Nagrody w systemie:")
        logger.info(f"  - Systemowe: {system_awards}")
        logger.info(f"  - Osobiste: {personal_awards}")
        logger.info(f"  - Custom publiczne: {custom_awards}")
        logger.info(f"  - RAZEM: {system_awards + personal_awards + custom_awards}")
        logger.info("")

        # Dla każdego użytkownika
        for user in users:
            admin_badge = "[ADMIN]" if user.is_admin else ""

            award_types = db.query(AwardType).all()
            can_give_count = sum(1 for award in award_types if user.can_give_award(award))

            logger.info(
                f"{user.username:15} {admin_badge:8} | Może przyznać: {can_give_count}/{len(award_types)} nagród")

            # Jakie konkretnie
            own_personal = db.query(AwardType).filter(
                AwardType.created_by_user_id == user.id,
                AwardType.is_personal == True
            ).first()

            if own_personal:
                logger.info(f"{'':24} | Osobista: {own_personal.display_name}")

            if user.is_admin:
                logger.info(f"{'':24} | Może przyznać WSZYSTKIE (admin)")
            else:
                logger.info(f"{'':24} | Może: systemowe + własna osobista + custom publiczne")

            logger.info("")

        logger.info(f"{'=' * 80}\n")
        logger.info("Aby zobaczyć szczegóły dla konkretnego usera:")
        logger.info(f"  python test_permissions.py <username>")
        logger.info("")

    except Exception as e:
        logger.error(f"Błąd: {e}")
    finally:
        db.close()


def test_award_accessibility(award_name: str):
    """Test który użytkownicy mogą przyznać daną nagrodę"""
    db = SessionLocal()

    try:
        award = db.query(AwardType).filter(AwardType.name == award_name).first()

        if not award:
            logger.error(f"Nagroda '{award_name}' nie istnieje")

            # Pokaż dostępne
            logger.info("\nDostępne nagrody:")
            awards = db.query(AwardType).all()
            for a in awards:
                logger.info(f"  - {a.name}")
            return

        logger.info(f"\n{'=' * 80}")
        logger.info(f"DOSTĘPNOŚĆ NAGRODY: {award.display_name}")
        logger.info(f"{'=' * 80}")
        logger.info(f"Name: {award.name}")
        logger.info(f"Icon: lucide:{award.lucide_icon}" if award.lucide_icon else "custom")
        logger.info(f"Color: {award.color}")
        logger.info(f"System: {'TAK' if award.is_system_award else 'NIE'}")
        logger.info(f"Personal: {'TAK' if award.is_personal else 'NIE'}")

        creator = db.query(User).filter(User.id == award.created_by_user_id).first()
        if creator:
            logger.info(f"Twórca: {creator.username}")

        # Sprawdź kto może przyznać
        users = db.query(User).all()

        can_give = []
        cannot_give = []

        for user in users:
            if user.can_give_award(award):
                can_give.append(user)
            else:
                cannot_give.append(user)

        logger.info(f"\nMOGĄ PRZYZNAĆ ({len(can_give)} użytkowników):")
        logger.info("-" * 80)
        for user in can_give:
            admin_badge = "[ADMIN]" if user.is_admin else ""
            reason = ""

            if user.is_admin:
                reason = "admin może wszystko"
            elif award.is_system_award:
                reason = "nagroda systemowa"
            elif award.is_personal and award.created_by_user_id == user.id:
                reason = "własna osobista"
            elif not award.is_personal:
                reason = "custom publiczna"

            logger.info(f"  {user.username:15} {admin_badge:8} | {reason}")

        if cannot_give:
            logger.info(f"\nNIE MOGĄ PRZYZNAĆ ({len(cannot_give)} użytkowników):")
            logger.info("-" * 80)
            for user in cannot_give:
                logger.info(f"  {user.username:15} | osobista nagroda innego usera")

        logger.info(f"\n{'=' * 80}\n")

    except Exception as e:
        logger.error(f"Błąd: {e}")
    finally:
        db.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test award permissions")
    parser.add_argument(
        'username',
        nargs='?',
        help='Username to test (optional)'
    )
    parser.add_argument(
        '--award',
        help='Test specific award accessibility'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Show summary for all users'
    )

    args = parser.parse_args()

    if args.award:
        test_award_accessibility(args.award)
    elif args.username:
        test_user_permissions(args.username)
    elif args.all:
        test_all_permissions()
    else:
        test_all_permissions()


if __name__ == "__main__":
    main()
