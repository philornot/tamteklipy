"""
Seed database with test data for development
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.user import User
from app.models.clip import Clip, ClipType
from app.models.award import Award
from app.core.security import hash_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_database(db):
    """Usuwa wszystkie dane z bazy (opcjonalnie)"""
    logger.warning("Usuwanie wszystkich danych z bazy...")
    db.query(Award).delete()
    db.query(Clip).delete()
    db.query(User).delete()
    db.commit()
    logger.info("Baza danych wyczyszczona")


def seed_users(db):
    """Tworzy testowych użytkowników"""
    logger.info("Tworzenie testowych użytkowników...")

    users_data = [
        {
            "username": "admin",
            "email": "admin@tamteklipy.local",
            "password": "Admin123!",
            "full_name": "Administrator",
            "award_scopes": ["award:epic_clip", "award:funny", "award:clutch", "award:wtf"]
        },
        {
            "username": "gamer1",
            "email": "gamer1@tamteklipy.local",
            "password": "Gamer123!",
            "full_name": "Pro Gamer",
            "award_scopes": ["award:epic_clip", "award:clutch"]
        },
        {
            "username": "gamer2",
            "email": "gamer2@tamteklipy.local",
            "password": "Gamer123!",
            "full_name": "Casual Player",
            "award_scopes": ["award:funny", "award:wtf"]
        },
        {
            "username": "viewer",
            "email": "viewer@tamteklipy.local",
            "password": "Viewer123!",
            "full_name": "Just Watching",
            "award_scopes": ["award:funny"]
        }
    ]

    created_users = []
    for user_data in users_data:
        # Sprawdź czy użytkownik już istnieje
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if existing:
            logger.info(f"  Użytkownik {user_data['username']} już istnieje, pomijam")
            created_users.append(existing)
            continue

        user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            full_name=user_data["full_name"],
            is_active=True,
            award_scopes=user_data["award_scopes"]
        )

        db.add(user)
        created_users.append(user)
        logger.info(f"  ✓ {user_data['username']} (scopes: {len(user_data['award_scopes'])})")

    db.commit()
    logger.info(f"Utworzono {len(created_users)} użytkowników\n")

    return created_users


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
        uploader = users[idx % len(users)]

        clip = Clip(
            filename=clip_data["filename"],
            file_path=f"/clips/{clip_data['filename']}",
            thumbnail_path=f"/thumbnails/{clip_data['filename']}.jpg" if clip_data[
                                                                             "clip_type"] == ClipType.VIDEO else None,
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
        logger.info(f"  ✓ {clip_data['filename']} (uploader: {uploader.username})")

    db.commit()
    logger.info(f"Utworzono {len(created_clips)} klipów\n")

    return created_clips


def seed_awards(db, users, clips):
    """Tworzy testowe nagrody"""
    logger.info("Przyznawanie testowych nagród...")

    awards_count = 0

    # Każdy użytkownik przyzna losowe nagrody do klipów
    for user in users:
        for clip in clips:
            # Użytkownik nie może przyznać nagrody do swojego klipa
            if clip.uploader_id == user.id:
                continue

            # Losowo przyzna nagrodę (50% szans)
            import random
            if random.random() > 0.5:
                continue

            # Wybierz losową nagrodę którą użytkownik ma
            if not user.award_scopes:
                continue

            award_name = random.choice(user.award_scopes)

            # Sprawdź czy już nie przyznał takiej nagrody
            existing = db.query(Award).filter(
                Award.clip_id == clip.id,
                Award.user_id == user.id,
                Award.award_name == award_name
            ).first()

            if existing:
                continue

            award = Award(
                clip_id=clip.id,
                user_id=user.id,
                award_name=award_name
            )

            db.add(award)
            awards_count += 1

    db.commit()
    logger.info(f"Przyznano {awards_count} nagród\n")


def print_summary(db):
    """Wyświetla podsumowanie seedowania"""
    logger.info("=" * 50)
    logger.info("PODSUMOWANIE BAZY DANYCH")
    logger.info("=" * 50)

    users_count = db.query(User).count()
    clips_count = db.query(Clip).count()
    awards_count = db.query(Award).count()

    logger.info(f"Użytkownicy: {users_count}")
    logger.info(f"Klipy: {clips_count}")
    logger.info(f"Nagrody: {awards_count}")
    logger.info("")

    logger.info("Testowe konta:")
    users = db.query(User).all()
    for user in users:
        logger.info(f"  {user.username:12} | Hasło: <username>123! | Scopes: {len(user.award_scopes)}")

    logger.info("")
    logger.info("=" * 50)


def main(clear_first=False):
    """Główna funkcja seedowania"""
    db = SessionLocal()

    try:
        logger.info("Rozpoczynam seedowanie bazy danych...\n")

        if clear_first:
            clear_database(db)

        users = seed_users(db)
        clips = seed_clips(db, users)
        seed_awards(db, users, clips)

        print_summary(db)

        logger.info("Seedowanie zakończone pomyślnie!")

    except Exception as e:
        logger.error(f"Błąd podczas seedowania: {e}")
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
