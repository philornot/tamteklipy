"""
Pomocnicze funkcje dla plików
"""
import hashlib

from app.models.clip import Clip
from app.models.user import User


def calculate_file_hash(file_content: bytes) -> str:
    """Oblicza SHA256 hash pliku"""
    return hashlib.sha256(file_content).hexdigest()


def can_access_clip(clip: Clip, user: User) -> bool:
    """
    Sprawdza czy użytkownik ma dostęp do klipa

    Returns:
        bool: True jeśli ma dostęp
    """
    # 1. Właściciel zawsze ma dostęp
    if clip.uploader_id == user.id:
        return True

    # 2. Wszyscy zalogowani mają dostęp
    return True


def format_file_size(size_bytes: int) -> str:
    """Formatuje rozmiar pliku do czytelnej formy"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
