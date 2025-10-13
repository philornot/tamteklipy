"""
Seed database with test data for development
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.clip import Clip, ClipType
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
            "password": "",
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


def seed_custom_awards(db, users):
    """Tworzy dodatkowe custom nagrody dla niektórych użytkowników"""
    logger.info("Tworzenie dodatkowych custom nagród...")

    # gamer1 tworzy swoją custom nagrodę
    gamer1 = next((u for u in users if u.username == "gamer1"), None)
    if gamer1:
        # Sprawdź czy nie istnieje
        existing = db.query(AwardType).filter(
            AwardType.name == "award:custom_gamer1_mvp"
        ).first()

        if not existing:
            custom_award = AwardType(
                name="award:custom_gamer1_mvp",
                display_name="MVP of the Match",
                description="Za bycie najlepszym graczem w meczu",
                lucide_icon="crown",
                color="#FFD700",
                created_by_user_id=gamer1.id,
                is_system_award=False,
                is_personal=False
            )
            db.add(custom_award)
            logger.info(f"  Created custom award by gamer1: {custom_award.display_name}")
        else:
            logger.info(f"  Custom award by gamer1 already exists, skipping")

    # gamer2 tworzy swoją custom nagrodę z custom ikoną
    gamer2 = next((u for u in users if u.username == "gamer2"), None)
    if gamer2:
        existing = db.query(AwardType).filter(
            AwardType.name == "award:custom_gamer2_lucky"
        ).first()

        if not existing:
            custom_award = AwardType(
                name="award:custom_gamer2_lucky",
                display_name="Lucky Shot",
                description="Za szczęśliwy strzał",
                custom_icon_path="/uploads/award_icons/lucky_shot.png",
                color="#4CAF50",
                created_by_user_id=gamer2.id,
                is_system_award=False,
                is_personal=False
            )
            db.add(custom_award)
            logger.info(f"  Created custom award by gamer2: {custom_award.display_name} (custom icon)")
        else:
            logger.info(f"  Custom award by gamer2 already exists, skipping")

    db.commit()
    logger.info("Dodatkowe custom nagrody utworzone\n")


def seed_clips(db, users):
    """Tworzy testowe klipy (opcjonalnie - bez rzeczywistych plików)"""
    logger.info("Tworzenie testowych klipów...")

    clips_data = [
        {
            "filename": "epic_pentakill.mp4",
            "clip_type": ClipType.VIDEO,
            "duration": 45,
            "file_size": 15_728_640,  # 15 MB
            "width": 1920,
            "height": 1080
        },
        {
            "filename": "funny_fail.mp4",
            "clip_type": ClipType.VIDEO,
            "duration": 12,
            "file_size": 5_242_880,  # 5 MB
            "width": 1920,
            "height": 1080
        },
        {
            "filename": "clutch_1v5.mp4",
            "clip_type": ClipType.VIDEO,
            "duration": 67,
            "file_size": 20_971_520,  # 20 MB
            "width": 2560,
            "height": 1440
        },
        {
            "filename": "beautiful_screenshot.png",
            "clip_type": ClipType.SCREENSHOT,
            "duration": None,
            "file_size": 2_097_152,  # 2 MB
            "width": 3840,
            "height": 2160
        }
    ]

    created_clips = []
    base_time = datetime.utcnow() - timedelta(days=7)

    for idx, clip_data in enumerate(clips_data):
        # Sprawdź czy clip już istnieje
        existing = db.query(Clip).filter(Clip.filename == clip_data["filename"]).first()
        if existing:
            logger.info(f"  Klip {clip_data['filename']} już istnieje, pomijam")
            created_clips.append(existing)
            continue

        uploader = users[idx % len(users)]

        # absolutna ścieżka z settings (TK-504)
        if settings.environment == "development":
            clips_dir = Path("uploads/clips")
        else:
            clips_dir = Path(settings.clips_path)

        file_path = str(clips_dir / "video.mp4")

        # absolutna ścieżka z settings (TK-499)
        if settings.environment == "development":
            thumbnails_dir = Path("uploads/thumbnails")
        else:
            thumbnails_dir = Path(settings.thumbnails_path)

        thumbnail_path = str(thumbnails_dir / "thumb.jpg")

        clip = Clip(
            filename=clip_data["filename"],
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            clip_type=clip_data["clip_type"],
            file_size=clip_data["file_size"],
            duration=clip_data["duration"],
            width=clip_data["width"],
            height=clip_data["height"],
            uploader_id=uploader.id,
            created_at=base_time + timedelta(days=idx)
        )

        db.add(clip)
        created_clips.append(clip)
        logger.info(f"  {clip_data['filename']} (uploader: {uploader.username})")

    db.commit()
    logger.info(f"Utworzono {len(created_clips)} klipów\n")

    return created_clips


def seed_awards(db, users, clips):
    """Tworzy testowe nagrody"""
    logger.info("Przyznawanie testowych nagród...")

    awards_count = 0

    # Pobierz wszystkie dostępne nagrody
    all_awards = db.query(AwardType).all()

    # Każdy użytkownik przyzna losowe nagrody do klipów
    for user in users:
        for clip in clips:
            # Użytkownik nie może przyznać nagrody do swojego klipa
            if clip.uploader_id == user.id:
                continue

            import random

            # 60% szans na przyznanie nagrody
            if random.random() > 0.6:
                continue

            # Wybierz dostępne nagrody dla użytkownika
            available_awards = [
                award for award in all_awards
                if user.can_give_award(award)
            ]

            if not available_awards:
                continue

            # Wybierz losową nagrodę
            award_type = random.choice(available_awards)

            # Sprawdź czy już nie przyznał takiej nagrody
            existing = db.query(Award).filter(
                Award.clip_id == clip.id,
                Award.user_id == user.id,
                Award.award_name == award_type.name
            ).first()

            if existing:
                continue

            award = Award(
                clip_id=clip.id,
                user_id=user.id,
                award_name=award_type.name
            )

            db.add(award)
            awards_count += 1

    db.commit()
    logger.info(f"Przyznano {awards_count} nagród\n")


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
        # seed_custom_awards(db, users)
        # clips = seed_clips(db, users)
        # seed_awards(db, users, clips)

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
