from pathlib import Path

from app.core.exceptions import ValidationError


def validate_absolute_path(path: str, field_name: str = "path") -> str:
    """
    Waliduje, że ścieżka jest absolutna

    Args:
        path: Ścieżka do zwalidowania
        field_name: Nazwa pola (do error message)

    Returns:
        str: Zwalidowana ścieżka

    Raises:
        ValidationError: Jeśli ścieżka nie jest absolutna
    """
    if not path:
        return path

    path_obj = Path(path)

    if not path_obj.is_absolute():
        raise ValidationError(
            message=f"{field_name} musi być ścieżką absolutną",
            field=field_name,
            details={
                "received": path,
                "is_absolute": False
            }
        )

    return path


def ensure_absolute_path(path: str, base_dir: Path) -> str:
    """
    Zapewnia, że ścieżka jest absolutna, jeśli nie — dołącza base_dir

    Args:
        path: Ścieżka (względna lub absolutna)
        base_dir: Katalog bazowy dla ścieżek względnych

    Returns:
        str: Absolutna ścieżka
    """
    path_obj = Path(path)

    if path_obj.is_absolute():
        return str(path_obj)

    return str(base_dir / path_obj)
