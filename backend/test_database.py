"""
Test połączenia i operacji na bazie danych
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, check_database_connection, get_database_info
from app.core.init_db import init_db
from app.models.user import User
from app.core.security import hash_password


def test_database_connection():
    """Test podstawowego połączenia"""
    print("=== Test połączenia z bazą danych ===\n")

    is_connected = check_database_connection()
    print(f"{'✅' if is_connected else '❌'} Połączenie z bazą: {'OK' if is_connected else 'FAILED'}\n")

    return is_connected


def test_database_info():
    """Test pobierania informacji o bazie"""
    print("=== Informacje o bazie danych ===\n")

    db_info = get_database_info()
    print(f"SQLite version: {db_info.get('sqlite_version')}")
    print(f"Liczba tabel: {db_info.get('tables_count')}")
    print(f"Tabele: {', '.join(db_info.get('tables', []))}\n")


def test_crud_operations():
    """Test operacji CRUD"""
    print("=== Test operacji CRUD ===\n")

    db = SessionLocal()

    try:
        # CREATE
        print("1. CREATE - Tworzenie użytkownika...")
        test_user = User(
            username="dbtest",
            email="dbtest@example.com",
            hashed_password=hash_password("TestPass123"),
            full_name="Database Test User",
            is_active=True,
            award_scopes=["award:test"]
        )

        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Użytkownik utworzony: ID={test_user.id}\n")

        # READ
        print("2. READ - Pobieranie użytkownika...")
        fetched_user = db.query(User).filter(User.username == "dbtest").first()
        print(f"✅ Użytkownik pobrany: {fetched_user.username} ({fetched_user.email})\n")

        # UPDATE
        print("3. UPDATE - Aktualizacja użytkownika...")
        fetched_user.full_name = "Updated Test User"
        db.commit()
        db.refresh(fetched_user)
        print(f"✅ Użytkownik zaktualizowany: {fetched_user.full_name}\n")

        # Query z filtrowaniem
        print("4. QUERY - Wyszukiwanie użytkowników...")
        active_users = db.query(User).filter(User.is_active == True).all()
        print(f"✅ Znaleziono {len(active_users)} aktywnych użytkowników\n")

        # DELETE
        print("5. DELETE - Usuwanie użytkownika...")
        db.delete(fetched_user)
        db.commit()
        print(f"✅ Użytkownik usunięty\n")

        # Sprawdź czy usunięty
        deleted_check = db.query(User).filter(User.username == "dbtest").first()
        print(f"{'✅' if deleted_check is None else '❌'} Weryfikacja usunięcia: {deleted_check is None}\n")

        print("✅ Wszystkie operacje CRUD przeszły pomyślnie!")

    except Exception as e:
        print(f"❌ Błąd podczas testów CRUD: {e}")
        db.rollback()
    finally:
        db.close()


def test_transactions():
    """Test transakcji i rollback"""
    print("\n=== Test transakcji i rollback ===\n")

    db = SessionLocal()

    try:
        print("1. Tworzenie użytkownika w transakcji...")
        user = User(
            username="transaction_test",
            email="transaction@example.com",
            hashed_password=hash_password("Pass123"),
            full_name="Transaction Test"
        )
        db.add(user)
        db.flush()  # Zapisz do bazy ale nie commituj
        print(f"✅ Użytkownik w transakcji: ID={user.id}")

        print("2. Rollback transakcji...")
        db.rollback()

        print("3. Sprawdzanie czy użytkownik został cofnięty...")
        check = db.query(User).filter(User.username == "transaction_test").first()
        print(f"{'✅' if check is None else '❌'} Rollback działa: {check is None}\n")

    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("TEST BAZY DANYCH SQLite + SQLAlchemy")
    print("=" * 50 + "\n")

    # Inicjalizuj bazę
    init_db()
    print()

    # Testy
    if test_database_connection():
        test_database_info()
        test_crud_operations()
        test_transactions()
    else:
        print("❌ Nie można kontynuować testów - brak połączenia z bazą")

    print("\n" + "=" * 50)
    print("TESTY ZAKOŃCZONE")
    print("=" * 50)
