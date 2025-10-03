# TamteKlipy Backend

## Setup

```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Zastosuj migracje bazy danych
alembic upgrade head

# (Opcjonalnie) Seeduj bazę testowymi danymi
python seed_database.py
```

## Seedowanie bazy danych

### Podstawowe użycie

```bash
# Dodaj testowych użytkowników, klipy i nagrody
python seed_database.py
```

### Z wyczyszczeniem bazy

```bash
# UWAGA: Usuwa wszystkie dane i tworzy od nowa
python seed_database.py --clear
```

### Testowe konta

Po seedowaniu dostępne są następujące konta:

| Username | Hasło        | Uprawnienia       |
|----------|--------------|-------------------|
| `admin`  | `Admin123!`  | Wszystkie nagrody |
| `gamer1` | `Gamer123!`  | epic_clip, clutch |
| `gamer2` | `Gamer123!`  | funny, wtf        |
| `viewer` | `Viewer123!` | funny             |

### Co jest tworzone?

- **4 użytkowników** z różnymi uprawnieniami
- **4 klipy** (3 video + 1 screenshot) - bez rzeczywistych plików
- **Losowe nagrody** przyznane do klipów

## Migracje bazy danych

Zobacz [alembic/README_MIGRATIONS.md](alembic/README_MIGRATIONS.md)

## Development

```bash
# Uruchom serwer
python -m app.main

# Dokumentacja API
http://localhost:8000/docs
```

```

### Uruchom seed:

```bash
cd backend

# Zastosuj migracje najpierw
alembic upgrade head

# Seeduj bazę
python seed_database.py
```