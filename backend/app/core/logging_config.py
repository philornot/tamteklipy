"""
Konfiguracja logowania - konsola i plik z rotacją
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import re


# Prosty remover emoji i znaków wariacyjnych, zapewniający czysty, tekstowy log
_EMOJI_RE = re.compile(
    "["  # zakresy popularnych emoji/piktogramów + ZWJ/VS16
    "\U0001F600-\U0001F64F"  # emotikony
    "\U0001F300-\U0001F5FF"  # symbole i piktogramy
    "\U0001F680-\U0001F6FF"  # transport/mapa
    "\U0001F1E0-\U0001F1FF"  # flagi
    "\U0001F900-\U0001F9FF"  # dodatkowe symbole
    "\U0001FA70-\U0001FAFF"  # symbole rozszerz.
    "\u2600-\u26FF"          # różne symbole
    "\u2700-\u27BF"          # dingbats
    "\u200D"                  # zero-width joiner
    "\uFE0F"                  # variation selector-16
    "]+",
    flags=re.UNICODE,
)


class CleanFormatter(logging.Formatter):
    """Formatter, który usuwa emoji z końcowego tekstu logu, zachowując format."""

    def format(self, record: logging.LogRecord) -> str:
        output = super().format(record)
        # Usuwamy emoji z już sformatowanego tekstu (najprościej i najbezpieczniej)
        return _EMOJI_RE.sub("", output)


def setup_logging(log_level: str = "INFO"):
    """
    Konfiguruje logowanie do konsoli i pliku

    Args:
        log_level: Poziom logowania (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Pobierz root logger
    root_logger = logging.getLogger()

    # Jeśli handlery już istnieją, nie dodawaj ponownie (fix dla uvicorn reload)
    if root_logger.handlers:
        return

    # Utwórz katalog na logi jeśli nie istnieje
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Format logów
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Konfiguracja root loggera
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Wspólny formatter czyszczący emoji dla wszystkich handlerów
    formatter = CleanFormatter(log_format, date_format)

    # Handler dla konsoli (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Handler dla pliku z rotacją (10MB, max 5 plików)
    file_handler = RotatingFileHandler(
        log_dir / "tamteklipy.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # W pliku logujemy wszystko
    file_handler.setFormatter(formatter)

    # Handler dla błędów - osobny plik
    error_file_handler = RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)

    # Dodaj handlery do root loggera
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_file_handler)

    # Wycisz zewnętrzne biblioteki (opcjonalnie)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logging.info("System logowania skonfigurowany")
    logging.info(f"Logi zapisywane do: {log_dir.absolute()}")
