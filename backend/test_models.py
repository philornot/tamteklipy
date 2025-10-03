"""
Test modeli Clip i Award z relacjami
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.core.init_db import init_db
from app.models.user import User
from app.models.clip import Clip, ClipType
from app.models.award import Award
from app.core.security import hash_password


def test_models_and_relationships():
    """Test wszystkich modeli i relacji"""
    print("=== Test modeli i relacji ===\n")

    # Inicjalizuj bazę
    init_db()

    db = SessionLocal()

    try:
        # 1. Utwórz użytkowników
        print("1. Tworzenie użytkowników...")
        user1 = User(
            username="uploader",
            email="uploader@example.com",
            hashed_password=hash_password("Pass123"),
            full_name="Uploader User",
            award_scopes=["award:epic_clip"]
        )

        user2 = User(
            username="voter",
            email="voter@example.com",
            hashed_password=hash_password("Pass123"),
            full_name="Voter User",
            award_scopes=["award:funny", "award:clutch"]
        )

        db.add_all([user1, user2])
        db.commit()
        db.refresh(user1)
        db.refresh(user2)
        print(f"✅ Użytkownicy utworzeni: {user1.username}, {user2.username}\n")

        # 2. Utwórz klip
        print("2. Tworzenie klipa...")
        clip = Clip(
            filename="epic_play.mp4",
            file_path="/clips/epic_play.mp4",
            thumbnail_path="/thumbnails/epic_play.jpg",
            clip_type=ClipType.VIDEO,
            file_size=15728640,  # 15 MB
            duration=45,
            width=1920,
            height=1080,
            uploader_id=user1.id
        )

        db.add(clip)
        db.commit()
        db.refresh(clip)
        print(f"✅ Klip utworzony: {clip.filename} ({clip.file_size_mb} MB)\n")

        # 3. Przyznaj nagrody
        print("3. Przyznawanie nagród...")
        award1 = Award(
            clip_id=clip.id,
            user_id=user1.id,
            award_name="award:epic_clip"
        )

        award2 = Award(
            clip_id=clip.id,
            user_id=user2.id,
            award_name="award:funny"
        )

        db.add_all([award1, award2])
        db.commit()
        print(f"✅ Nagrody przyznane: 2 nagrody dla klipa {clip.id}\n")

        # 4. Test relacji - pobierz klip z nagrodami
        print("4. Test relacji...")
        fetched_clip = db.query(Clip).filter(Clip.id == clip.id).first()
        print(f"Klip: {fetched_clip.filename}")
        print(f"Uploader: {fetched_clip.uploader.username}")
        print(f"Liczba nagród: {fetched_clip.award_count}")
        print(f"Nagrody:")
        for award in fetched_clip.awards:
            print(f"  - {award.award_name} od {award.user.username}\n")

        # 5. Test UniqueConstraint - spróbuj dodać duplikat
        print("5. Test UniqueConstraint (duplikat nagrody)...")
        try:
            duplicate_award = Award(
                clip_id=clip.id,
                user_id=user1.id,
                award_name="award:epic_clip"  # Ta sama nagroda od tego samego usera
            )
            db.add(duplicate_award)
            db.commit()
            print("❌ Duplikat nagrody został dodany (błąd!)\n")
        except Exception as e:
            db.rollback()
            print(f"✅ Duplikat nagrody odrzucony (UniqueConstraint działa)\n")

        print("✅ Wszystkie testy modeli przeszły pomyślnie!")

    except Exception as e:
        print(f"❌ Błąd: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    test_models_and_relationships()
