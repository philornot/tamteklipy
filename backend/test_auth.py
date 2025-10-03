"""
Test endpointów autoryzacji
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User


def setup_test_user():
    """Utwórz użytkownika testowego"""
    db = SessionLocal()

    try:
        # Usuń jeśli istnieje
        existing = db.query(User).filter(User.username == "testauth").first()
        if existing:
            db.delete(existing)
            db.commit()

        # Utwórz nowego
        user = User(
            username="testauth",
            email="testauth@example.com",
            hashed_password=hash_password("TestHaslo123"),
            full_name="Test Auth User",
            is_active=True,
            award_scopes=["award:epic_clip", "award:funny"]
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"✅ Użytkownik testowy utworzony: {user.username}")
        print(f"   Hasło: TestHaslo123")
        print(f"   Award scopes: {user.award_scopes}\n")

        return user

    finally:
        db.close()


if __name__ == "__main__":
    print("=== Setup użytkownika testowego ===\n")
    setup_test_user()
    print("\nTeraz możesz przetestować endpointy w Swagger UI:")
    print("1. http://localhost:8000/docs")
    print("2. POST /api/auth/login")
    print("   Username: testauth")
    print("   Password: TestHaslo123")
    print("3. Skopiuj access_token")
    print("4. Kliknij 'Authorize' i wklej token")
    print("5. Przetestuj GET /api/auth/me")
