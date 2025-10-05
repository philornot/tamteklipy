"""
Reset hasła użytkownika - przydatne gdy zapomnisz hasła
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import logging
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_password(username: str, new_password: str):
    """
    Resetuje hasło użytkownika

    Args:
        username: Nazwa użytkownika
        new_password: Nowe hasło (plain text)
    """
    db = SessionLocal()

    try:
        # Znajdź użytkownika
        user = db.query(User).filter(User.username == username).first()

        if not user:
            logger.error(f"❌ Użytkownik '{username}' nie istnieje!")
            logger.info("\nDostępni użytkownicy:")
            all_users = db.query(User).all()
            for u in all_users:
                admin_badge = " [ADMIN]" if u.is_admin else ""
                logger.info(f"  - {u.username}{admin_badge}")
            return False

        # Zahashuj nowe hasło
        user.hashed_password = hash_password(new_password)
        db.commit()

        admin_info = " [ADMIN]" if user.is_admin else ""
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"✅ Hasło zmienione pomyślnie!")
        logger.info("=" * 60)
        logger.info(f"Użytkownik: {username}{admin_info}")
        logger.info(f"Nowe hasło: {new_password}")
        logger.info("")
        logger.info("Możesz się teraz zalogować w aplikacji.")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ Błąd podczas resetowania hasła: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    if len(sys.argv) != 3:
        print("Użycie: python reset_password.py <username> <new_password>")
        print("")
        print("Przykład:")
        print("  python reset_password.py philornot NoweHaslo123!")
        print("")
        sys.exit(1)

    username = sys.argv[1]
    new_password = sys.argv[2]

    success = reset_password(username, new_password)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
