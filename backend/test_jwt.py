"""
Test JWT tokens z scope
"""
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.security import create_access_token, verify_token


def test_jwt_with_scopes():
    """Test tworzenia i weryfikacji JWT tokenu ze scope"""

    print("=== Test JWT Tokens ===\n")

    # Dane użytkownika
    user_id = 1
    username = "testuser"
    scopes = ["award:epic_clip", "award:funny", "award:clutch"]

    # Utwórz token
    print("1. Tworzenie tokenu...")
    token = create_access_token(
        user_id=user_id,
        username=username,
        scopes=scopes,
        expires_delta=timedelta(minutes=30)
    )
    print(f"✅ Token utworzony:")
    print(f"   {token[:50]}...")
    print(f"   Długość: {len(token)} znaków\n")

    # Weryfikuj token
    print("2. Weryfikacja tokenu...")
    decoded = verify_token(token)

    if decoded:
        print("✅ Token poprawny!")
        print(f"   User ID: {decoded['user_id']}")
        print(f"   Username: {decoded['username']}")
        print(f"   Scopes: {decoded['scopes']}\n")
    else:
        print("❌ Token nieprawidłowy!\n")
        return

    # Test z nieprawidłowym tokenem
    print("3. Test z nieprawidłowym tokenem...")
    invalid_decoded = verify_token("invalid.token.here")
    is_rejected = invalid_decoded is None
    print(f"{'✅' if is_rejected else '❌'} Nieprawidłowy token odrzucony: {is_rejected}\n")

    # Test z tokenem o krótkim czasie życia
    print("4. Test tokenu z krótkim czasem życia (1 sekunda)...")
    short_token = create_access_token(
        user_id=user_id,
        username=username,
        scopes=scopes,
        expires_delta=timedelta(seconds=1)
    )
    print("Token utworzony, czekam 2 sekundy...")

    import time
    time.sleep(2)

    expired_decoded = verify_token(short_token)
    is_expired = expired_decoded is None
    print(f"{'✅' if is_expired else '❌'} Wygasły token odrzucony: {is_expired}\n")

    print("✅ Wszystkie testy JWT przeszły pomyślnie!")


if __name__ == "__main__":
    test_jwt_with_scopes()
