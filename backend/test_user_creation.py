"""
Test tworzenia użytkownika z hashowaniem hasła
"""
import sys
from pathlib import Path

# Dodaj backend do path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.core.security import hash_password, verify_password
from app.models.user import User


def test_user_creation():
    """Test tworzenia użytkownika i weryfikacji hasła"""
    db = SessionLocal()

    try:
        # Sprawdź czy użytkownik już istnieje
        existing_user = db.query(User).filter(User.username == "testuser").first()
        if existing_user:
            print(f"Użytkownik '{existing_user.username}' już istnieje, usuwam...")
            db.delete(existing_user)
            db.commit()

        # Utwórz nowego użytkownika
        print("\n=== Tworzenie użytkownika ===")
        plain_password = "SuperTajneHaslo123!"
        hashed = hash_password(plain_password)

        new_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hashed,
            full_name="Test User",
            is_active=True,
            award_scopes=["award:epic_clip", "award:funny"]
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"✅ Użytkownik utworzony: ID={new_user.id}, Username={new_user.username}")
        print(f"   Email: {new_user.email}")
        print(f"   Full name: {new_user.full_name}")
        print(f"   Award scopes: {new_user.award_scopes}")
        print(f"   Hashed password: {new_user.hashed_password[:50]}...")

        # Test weryfikacji hasła
        print("\n=== Test weryfikacji hasła ===")
        correct_password = verify_password(plain_password, new_user.hashed_password)
        wrong_password = verify_password("złe_hasło", new_user.hashed_password)

        print(f"✅ Weryfikacja poprawnego hasła: {correct_password}")
        print(f"❌ Weryfikacja złego hasła: {wrong_password}")

        # Test metody has_scope
        print("\n=== Test uprawnień (scopes) ===")
        print(f"Czy ma scope 'award:epic_clip'? {new_user.has_scope('award:epic_clip')}")
        print(f"Czy ma scope 'award:funny'? {new_user.has_scope('award:funny')}")
        print(f"Czy ma scope 'award:nonexistent'? {new_user.has_scope('award:nonexistent')}")

        # Pobierz użytkownika z bazy ponownie
        print("\n=== Test pobierania z bazy ===")
        fetched_user = db.query(User).filter(User.username == "testuser").first()
        print(f"✅ Użytkownik pobrany z bazy: {fetched_user}")
        print(
            f"   Weryfikacja hasła dla pobranego użytkownika: {verify_password(plain_password, fetched_user.hashed_password)}")

        print("\n✅ Wszystkie testy przeszły pomyślnie!")

    except Exception as e:
        print(f"\n❌ Błąd: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    test_user_creation()
