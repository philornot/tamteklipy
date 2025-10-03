# TamteKlipy Backend

## Setup
```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Zastosuj migracje bazy danych
alembic upgrade head

# Uruchom serwer
python -m app.main
```

## Migracje bazy danych
Zobacz szczegółową dokumentację w alembic/README_MIGRATIONS.md.

### Podstawowe komendy
```bash
# Utwórz migrację po zmianach w modelach
alembic revision --autogenerate -m "Opis zmian"

# Zastosuj migracje
alembic upgrade head

# Sprawdź status
alembic current
```
