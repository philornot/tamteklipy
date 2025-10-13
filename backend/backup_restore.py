"""
Backup i restore bazy danych
"""
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import logging
import argparse
from app.core.logging_config import setup_logging

# Spójna konfiguracja logowania
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)


def backup_database(backup_dir: str = "backups"):
    """
    Tworzy backup bazy danych

    Args:
        backup_dir: Katalog gdzie zapisać backup
    """

    db_file = Path("tamteklipy.db")

    if not db_file.exists():
        logger.error("Plik bazy danych nie istnieje!")
        return False

    # Utwórz katalog backupów
    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)

    # Nazwa backupu z timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path / f"tamteklipy_{timestamp}.db"

    try:
        logger.info(f"Tworzę backup: {backup_file}")
        shutil.copy2(db_file, backup_file)

        file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
        logger.info("Backup utworzony pomyślnie!")
        logger.info(f"   Plik: {backup_file}")
        logger.info(f"   Rozmiar: {file_size:.2f} MB")

        # Pokaż ostatnie 5 backupów
        list_backups(backup_dir, limit=5)

        return True

    except Exception as e:
        logger.error(f"Błąd podczas tworzenia backupu: {e}")
        return False


def restore_database(backup_file: str):
    """
    Przywraca bazę danych z backupu

    Args:
        backup_file: ścieżka do pliku backupu
    """

    backup_path = Path(backup_file)

    if not backup_path.exists():
        logger.error(f"Plik backupu nie istnieje: {backup_file}")
        return False

    db_file = Path("tamteklipy.db")

    # Ostrzeżenie
    logger.warning("=" * 60)
    logger.warning("UWAGA: RESTORE BAZY DANYCH")
    logger.warning("=" * 60)

    if db_file.exists():
        logger.warning("To nadpisze istniejącą bazę danych!")
        logger.warning(f"Aktualna baza: {db_file}")

    logger.warning(f"Restore z: {backup_path}")
    logger.warning("")

    response = input("Czy na pewno chcesz kontynuować? (wpisz 'TAK'): ")
    if response != "TAK":
        logger.info("Anulowano restore")
        return False

    try:
        # Backup aktualnej bazy (jeśli istnieje)
        if db_file.exists():
            logger.info("Tworzę backup aktualnej bazy przed restore...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety_backup = Path("backups") / f"before_restore_{timestamp}.db"
            safety_backup.parent.mkdir(exist_ok=True)
            shutil.copy2(db_file, safety_backup)
            logger.info(f"   Safety backup: {safety_backup}")

        # Restore
        logger.info(f"Przywracam bazę z: {backup_path}")
        shutil.copy2(backup_path, db_file)

        logger.info("")
        logger.info("Restore zakończony pomyślnie!")
        logger.info(f"   Przywrócono: {db_file}")

        # Sprawdź status
        logger.info("")
        logger.info("Uruchom 'python db_status.py' aby sprawdzić bazę")

        return True

    except Exception as e:
        logger.error(f"Błąd podczas restore: {e}")
        return False


def list_backups(backup_dir: str = "backups", limit: int = None):
    """
    Wyświetla listę backupów

    Args:
        backup_dir: Katalog z backupami
        limit: Maksymalna liczba backupów do wyświetlenia
    """

    backup_path = Path(backup_dir)

    if not backup_path.exists():
        logger.info("Brak katalogu z backupami")
        return

    # Znajdź wszystkie backupy
    backups = sorted(
        backup_path.glob("tamteklipy_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not backups:
        logger.info("Brak backupów")
        return

    logger.info("")
    logger.info(f"Dostępne backupy ({len(backups)}):")
    logger.info("=" * 80)

    for i, backup in enumerate(backups):
        if limit and i >= limit:
            break

        stat = backup.stat()
        size_mb = stat.st_size / (1024 * 1024)
        modified = datetime.fromtimestamp(stat.st_mtime)

        logger.info(f"{i + 1}. {backup.name}")
        logger.info(f"   Data: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"   Rozmiar: {size_mb:.2f} MB")
        logger.info("")

    if limit and len(backups) > limit:
        logger.info(f"... i {len(backups) - limit} więcej")
        logger.info("")

    logger.info("=" * 80)


def cleanup_old_backups(backup_dir: str = "backups", keep: int = 10):
    """
    Usuwa stare backupy, zostawiając tylko N najnowszych

    Args:
        backup_dir: Katalog z backupami
        keep: Ile najnowszych backupów zachować
    """

    backup_path = Path(backup_dir)

    if not backup_path.exists():
        logger.info("Brak katalogu z backupami")
        return

    # Znajdź wszystkie backupy
    backups = sorted(
        backup_path.glob("tamteklipy_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if len(backups) <= keep:
        logger.info(f"Backupów: {len(backups)}, limit: {keep} - nic do usunięcia")
        return

    # Usuń stare
    to_remove = backups[keep:]

    logger.info(f"Usuwam {len(to_remove)} starych backupów...")

    for backup in to_remove:
        try:
            backup.unlink()
            logger.info(f"  Usunięto: {backup.name}")
        except Exception as e:
            logger.error(f"  Błąd usuwania {backup.name}: {e}")

    logger.info(f"Zostało {keep} najnowszych backupów")


def main():
    parser = argparse.ArgumentParser(description="Backup and restore database")

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Backup
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument(
        '--dir',
        default='backups',
        help='Backup directory (default: backups)'
    )

    # Restore
    restore_parser = subparsers.add_parser('restore', help='Restore database from backup')
    restore_parser.add_argument(
        'backup_file',
        help='Path to backup file'
    )

    # List
    list_parser = subparsers.add_parser('list', help='List available backups')
    list_parser.add_argument(
        '--dir',
        default='backups',
        help='Backup directory (default: backups)'
    )
    list_parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of backups to show'
    )

    # Cleanup
    cleanup_parser = subparsers.add_parser('cleanup', help='Remove old backups')
    cleanup_parser.add_argument(
        '--dir',
        default='backups',
        help='Backup directory (default: backups)'
    )
    cleanup_parser.add_argument(
        '--keep',
        type=int,
        default=10,
        help='Number of backups to keep (default: 10)'
    )

    args = parser.parse_args()

    if args.command == 'backup':
        backup_database(args.dir)
    elif args.command == 'restore':
        restore_database(args.backup_file)
    elif args.command == 'list':
        list_backups(args.dir, args.limit)
    elif args.command == 'cleanup':
        cleanup_old_backups(args.dir, args.keep)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
