"""
Konfiguracja logowania - konsola i plik z rotacją
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_level: str = "INFO"):
    """
    Konfiguruje logowanie do konsoli i pliku

    Args:
        log_level: Poziom logowania (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Utwórz katalog na logi jeśli nie istnieje
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Format logów
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Konfiguracja root loggera
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Handler dla konsoli (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)

    # Handler dla pliku z rotacją (10MB, max 5 plików)
    file_handler = RotatingFileHandler(
        log_dir / "tamteklipy.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # W pliku logujemy wszystko
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)

    # Handler dla błędów - osobny plik
    error_file_handler = RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(file_formatter)

    # Dodaj handlery do root loggera
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_file_handler)

    # Wycisz zewnętrzne biblioteki (opcjonalnie)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logging.info("🔧 System logowania skonfigurowany")
    logging.info(f"📝 Logi zapisywane do: {log_dir.absolute()}")
