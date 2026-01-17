"""
Przetwarzanie plików — zapis, thumbnail, metadata
"""
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.exceptions import StorageError, FileUploadError
from app.models.clip import Clip, ClipType
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_storage_directory(clip_type: ClipType) -> Path:
    """
    Zwraca katalog dla danego typu pliku.

    Args:
        clip_type: Typ klipa (VIDEO lub SCREENSHOT)

    Returns:
        Path: Ścieżka do katalogu storage
    """
    if clip_type == ClipType.VIDEO:
        storage_dir = Path(settings.clips_path)
    else:
        storage_dir = Path(settings.screenshots_path)

    if settings.environment == "development":
        subdir = "clips" if clip_type == ClipType.VIDEO else "screenshots"
        storage_dir = (Path.cwd() / "uploads" / subdir).resolve()

    return storage_dir


def check_storage_health(storage_dir: Path) -> dict:
    """
    Check storage health and return detailed error info.

    Returns:
        dict: {
            "ok": bool,
            "error_type": str | None,  # permission_denied, disk_full, path_not_exists, etc.
            "details": {
                "path": str,
                "message": str,
                "hints": List[str],
                "free_mb": float,
                ...
            }
        }
    """
    result = {
        "ok": True,
        "error_type": None,
        "details": {}
    }

    # Check 1: Path exists
    if not storage_dir.exists():
        result["ok"] = False
        result["error_type"] = "path_not_exists"
        result["details"] = {
            "path": str(storage_dir),
            "message": "Katalog storage nie istnieje",
            "hints": [
                "Sprawdź czy pendrive jest podłączony",
                f"Sprawdź czy katalog {storage_dir} istnieje",
                "Na produkcji: sudo mount /dev/sda1 /mnt/tamteklipy"
            ]
        }
        return result

    # Check 2: Is directory
    if not storage_dir.is_dir():
        result["ok"] = False
        result["error_type"] = "not_a_directory"
        result["details"] = {
            "path": str(storage_dir),
            "message": f"Ścieżka {storage_dir} istnieje ale nie jest katalogiem"
        }
        return result

    # Check 3: Write permissions (test file)
    test_file = storage_dir / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
    except PermissionError as e:
        result["ok"] = False
        result["error_type"] = "permission_denied"
        result["details"] = {
            "path": str(storage_dir),
            "message": "Brak uprawnień do zapisu w katalogu",
            "system_error": str(e),
            "hints": [
                f"Sprawdź uprawnienia: ls -la {storage_dir.parent}",
                f"Napraw uprawnienia: sudo chown -R $USER:$USER {storage_dir}",
                f"Lub: sudo chmod -R 755 {storage_dir}",
                "Skontaktuj się z administratorem (Filip)"
            ]
        }
        return result
    except OSError as e:
        result["ok"] = False
        result["error_type"] = "write_failed"
        result["details"] = {
            "path": str(storage_dir),
            "message": "Nie można zapisać pliku testowego",
            "system_error": str(e)
        }
        return result

    # Check 4: Disk space (min 100MB)
    try:
        import shutil
        stat = shutil.disk_usage(storage_dir)
        free_mb = stat.free / (1024 * 1024)

        if free_mb < 100:
            result["ok"] = False
            result["error_type"] = "disk_full"
            result["details"] = {
                "path": str(storage_dir),
                "free_mb": round(free_mb, 2),
                "total_mb": round(stat.total / (1024 * 1024), 2),
                "used_mb": round(stat.used / (1024 * 1024), 2),
                "message": f"Mało miejsca na dysku: {free_mb:.0f}MB",
                "hints": [
                    "Usuń stare pliki z serwera",
                    "Zwiększ rozmiar pendrive'a",
                    "Skontaktuj się z adminem (Filip)"
                ]
            }
            return result

        result["details"]["free_mb"] = round(free_mb, 2)

    except OSError as e:
        logger.warning(f"Could not check disk space: {e}")

    return result


async def save_file_to_disk(
        file_content: bytes,
        unique_filename: str,
        clip_type: ClipType
) -> Path:
    """
    Save file to disk with error handling.

    Raises:
        StorageError: With specific error_type and status_code:
            - permission_denied (500)
            - disk_full (507)
            - path_not_exists (503)
    """
    storage_dir = get_storage_directory(clip_type)

    # Pre-check: Health check before attempting write
    health = check_storage_health(storage_dir)

    if not health["ok"]:
        error_type = health["error_type"]
        details = health["details"]

        # Map error type to HTTP status code
        status_code_map = {
            "permission_denied": 500,  # Server misconfiguration
            "disk_full": 507,  # Insufficient Storage
            "path_not_exists": 503,  # Service Unavailable
            "not_a_directory": 503,
            "write_failed": 500
        }

        status_code = status_code_map.get(error_type, 500)

        raise StorageError(
            message=details.get("message", "Błąd dostępu do storage"),
            path=details.get("path"),
            status_code=status_code,
            details={
                "error_type": error_type,
                "hints": details.get("hints"),
                "system_error": details.get("system_error"),
                "free_mb": details.get("free_mb")
            }
        )

    # Ensure directory exists (redundant but safe)
    try:
        storage_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise StorageError(
            message=f"Brak uprawnień do utworzenia katalogu: {storage_dir}",
            path=str(storage_dir),
            status_code=500,
            details={
                "error_type": "permission_denied",
                "system_error": str(e),
                "hints": [
                    f"sudo chown -R $USER:$USER {storage_dir}",
                    "Skontaktuj się z administratorem (Filip)"
                ]
            }
        )
    except OSError as e:
        raise StorageError(
            message=f"Nie można utworzyć katalogu: {e}",
            path=str(storage_dir),
            status_code=500,
            details={"system_error": str(e)}
        )

    file_path = storage_dir / unique_filename
    tmp_path = None
    moved = False

    try:
        # Atomic write: temp file -> rename
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, dir=str(storage_dir)) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(file_content)
            tmp.flush()
            os.fsync(tmp.fileno())

        # Atomic move
        os.replace(str(tmp_path), str(file_path))
        moved = True

        logger.info(f"File saved: {file_path} ({len(file_content)} bytes)")
        return file_path

    except PermissionError as e:
        raise StorageError(
            message="Brak uprawnień do zapisu pliku",
            path=str(file_path),
            status_code=500,
            details={
                "error_type": "permission_denied",
                "system_error": str(e),
                "hints": [
                    f"sudo chown -R $USER:$USER {storage_dir}",
                    f"sudo chmod -R 755 {storage_dir}",
                    "Skontaktuj się z administratorem (Filip)"
                ]
            }
        )
    except OSError as e:
        # Disk full during write
        if "No space left" in str(e) or e.errno == 28:  # ENOSPC
            import shutil
            stat = shutil.disk_usage(storage_dir)
            raise StorageError(
                message="Brak miejsca na dysku",
                path=str(storage_dir),
                status_code=507,
                details={
                    "error_type": "disk_full",
                    "free_mb": round(stat.free / (1024 * 1024), 2),
                    "required_mb": round(len(file_content) / (1024 * 1024), 2),
                    "hints": [
                        "Usuń stare pliki z serwera",
                        "Zwiększ rozmiar pendrive'a"
                    ]
                }
            )

        raise StorageError(
            message=f"Błąd zapisu pliku: {e}",
            path=str(file_path),
            status_code=500,
            details={"system_error": str(e)}
        )

    finally:
        # Cleanup temp file if not moved
        if tmp_path and tmp_path.exists() and not moved:
            try:
                tmp_path.unlink()
            except OSError:
                pass


async def create_clip_record(
        db: Session,
        filename: str,
        file_path: Path,
        file_size: int,
        clip_type: ClipType,
        uploader_id: int,
        thumbnail_path: Optional[str] = None,
        thumbnail_webp_path: Optional[str] = None,
        metadata: Optional[dict] = None
) -> Clip:
    """
    Tworzy rekord klipa w bazie.

    Args:
        db: SQLAlchemy session
        filename: Oryginalna nazwa pliku
        file_path: Ścieżka do zapisanego pliku
        file_size: Rozmiar w bajtach
        clip_type: Typ klipa
        uploader_id: ID użytkownika
        thumbnail_path: Ścieżka do thumbnail (opcjonalna)
        thumbnail_webp_path: Ścieżka do WebP thumbnail (opcjonalna)
        metadata: Metadane video/image (opcjonalne)

    Returns:
        Clip: Utworzony obiekt

    Raises:
        DatabaseError: Gdy nie można zapisać do bazy
    """
    from sqlalchemy.exc import SQLAlchemyError
    from app.core.exceptions import DatabaseError

    new_clip = Clip(
        filename=filename,
        file_path=str(file_path.resolve()),
        thumbnail_path=thumbnail_path,
        thumbnail_webp_path=thumbnail_webp_path,
        clip_type=clip_type,
        file_size=file_size,
        duration=metadata.get("duration") if metadata else None,
        width=metadata.get("width") if metadata else None,
        height=metadata.get("height") if metadata else None,
        uploader_id=uploader_id
    )

    try:
        db.add(new_clip)
        db.commit()
        db.refresh(new_clip)
        logger.info(f"Clip created: ID={new_clip.id}")
        return new_clip

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()

        # Cleanup plików przy błędzie bazy
        try:
            file_path.unlink()
            if thumbnail_path:
                Path(thumbnail_path).unlink()
            if thumbnail_webp_path:
                Path(thumbnail_webp_path).unlink()
        except OSError:
            pass

        raise DatabaseError(
            message="Nie można zapisać do bazy danych",
            operation="create_clip"
        )
