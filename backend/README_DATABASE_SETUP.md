# TamteKlipy - Database Setup Guide

## 🚀 Quick Start (Hard Reset)

Jeśli jesteś na etapie developmentu i chcesz zacząć od czystej bazy:

```bash
# Krok 1: Hard reset bazy danych (usuwa wszystko!)
python hard_reset.py
# Wpisz 'TAK' aby potwierdzić

# Krok 2: Zaseeduj testowe dane
python seed_database.py --clear

# Krok 3: Sprawdź status
python db_status.py

# Krok 4: Uruchom serwer
uvicorn app.main:app --reload
```

## 📁 Dostępne Skrypty

### 1. `hard_reset.py` - Kompletny reset bazy

```bash
python hard_reset.py
```

- Usuwa wszystkie tabele
- Usuwa plik bazy danych
- Tworzy nową bazę od zera
- Inicjalizuje systemowe nagrody

**Kiedy używać:**

- ✅ Gdy zmieniasz strukturę bazy danych
- ✅ Gdy masz błędy migracji
- ✅ Podczas developmentu (dane nie są wartościowe)

### 2. `seed_database.py` - Dane testowe

```bash
python seed_database.py --clear
```

- Tworzy testowych użytkowników (4)
- Tworzy osobiste nagrody dla każdego usera
- Tworzy przykładowe custom nagrody
- Tworzy testowe klipy (4)
- Przyznaje losowe nagrody

**Opcje:**

- `--clear` - Usuwa dane przed seedowaniem

### 3. `db_status.py` - Sprawdź status bazy

```bash
python db_status.py
```

Wyświetla:

- ✅ Czy baza istnieje
- ✅ Czy schema jest aktualny (nowy z lucide icons)
- ✅ Statystyki (users, clips, awards)
- ✅ Listę wszystkich typów nagród
- ✅ Listę użytkowników z ich nagrodami

### 4. `run_migration.py` - Migracja (jeśli potrzebna)

```bash
# Sprawdź status migracji
python run_migration.py --check

# Uruchom migrację
python run_migration.py

# Cofnij migrację
python run_migration.py --down
```

**Uwaga:** Przy hard reset migracja NIE jest potrzebna!

### 5. `backup_restore.py` - Backup i restore

#### Utworzenie backupu:

```bash
python backup_restore.py backup
```

#### Lista backupów:

```bash
python backup_restore.py list
python backup_restore.py list --limit 5
```

#### Restore z backupu:

```bash
python backup_restore.py restore backups/tamteklipy_20250104_123456.db
```

#### Czyszczenie starych backupów:

```bash
python backup_restore.py cleanup --keep 10
```

## 📊 Co powstaje po fresh setup?

### Systemowe nagrody (5):

| Nazwa        | Icon    | Kolor   | Opis                         |
|--------------|---------|---------|------------------------------|
| Epic Clip    | `flame` | #FF4500 | Za epicki moment w grze      |
| Funny Moment | `laugh` | #FFD700 | Za zabawną sytuację          |
| Pro Play     | `star`  | #4169E1 | Za profesjonalną zagrywkę    |
| Clutch       | `zap`   | #32CD32 | Za clutch w trudnej sytuacji |
| WTF Moment   | `eye`   | #9370DB | Za nieoczekiwaną sytuację    |

### Testowi użytkownicy (4):

| Username | Email                   | Password   | Admin | Osobista nagroda      |
|----------|-------------------------|------------|-------|-----------------------|
| admin    | admin@tamteklipy.local  | Admin123!  | ✅     | Nagroda Administrator |
| gamer1   | gamer1@tamteklipy.local | Gamer1123! | ❌     | Nagroda Pro Gamer     |
| gamer2   | gamer2@tamteklipy.local | Gamer2123! | ❌     | Nagroda Casual Player |
| viewer   | viewer@tamteklipy.local | Viewer123! | ❌     | Nagroda Just Watching |

### Custom nagrody (przykłady):

- **MVP of the Match** (by gamer1) - publiczna, `crown` icon
- **Lucky Shot** (by gamer2) - publiczna, custom icon

## 🔑 System uprawnień

### Admin (`is_admin=True`)

```python
# Może przyznawać WSZYSTKIE nagrody
- ✅ Systemowe(Epic
Clip, Funny, etc.)
- ✅ Osobiste
innych
userów
- ✅ Custom
publiczne

# Może zarządzać nagrodami
- ✅ Tworzyć
nowe
typy
- ✅ Edytować
wszystkie(poza
systemowymi)
- ✅ Usuwać(poza
systemowymi)
```

### Zwykły user

```python
# Może przyznawać
- ✅ Systemowe(Epic
Clip, Funny, etc.)
- ✅ TYLKO
swoją
osobistą
nagrodę
- ✅ Custom
publiczne
- ❌ Osobiste
innych
userów

# Może zarządzać
- ✅ Tworzyć
własne
custom
nagrody
- ✅ Edytować
TYLKO
własne
- ✅ Usuwać
TYLKO
własne
```

### Przykład w kodzie:

```python
from app.models import User, AwardType

# Sprawdź czy user może przyznać nagrodę
can_give = user.can_give_award(award_type)

# Logika:
if user.is_admin:
    return True  # Admin może wszystko

if award_type.is_system_award:
    return True  # Systemowe dla wszystkich

if award_type.is_personal:
    return award_type.created_by_user_id == user.id  # Tylko twórca

return True  # Custom publiczne dla wszystkich
```

## 🗄️ Struktura bazy danych

### Tabela: `users`

```sql
id
INTEGER PRIMARY KEY
username            VARCHAR(50) UNIQUE
email               VARCHAR(100) UNIQUE
hashed_password     VARCHAR(255)
full_name           VARCHAR(100)
is_active           BOOLEAN DEFAULT TRUE
is_admin            BOOLEAN DEFAULT FALSE  -- NOWE!
award_scopes        JSON                   -- deprecated
```

### Tabela: `award_types`

```sql
id
INTEGER PRIMARY KEY
name                VARCHAR(100) UNIQUE
display_name        VARCHAR(100)
description         TEXT
lucide_icon         VARCHAR(100)           -- NOWE! np. "trophy", "star"
custom_icon_path    VARCHAR(500)           -- NOWE! ścieżka do custom ikony
color               VARCHAR(7)
created_by_user_id  INTEGER                -- NOWE! właściciel nagrody
is_system_award     BOOLEAN DEFAULT FALSE  -- NOWE! systemowa/usuwalna
is_personal         BOOLEAN DEFAULT FALSE  -- NOWE! tylko twórca może dawać
created_at          DATETIME               -- NOWE!
updated_at          DATETIME               -- NOWE!
```

### Tabela: `awards`

```sql
id
INTEGER PRIMARY KEY
clip_id             INTEGER FK -> clips.id
user_id             INTEGER FK -> users.id
award_name          VARCHAR(100)  -- np. "award:epic_clip"
awarded_at          DATETIME

UNIQUE(clip_id, user_id, award_name)
```

## 🔄 Workflow developmentu

### Pierwszy setup:

```bash
# 1. Sklonuj repo
git clone ...
cd tamteklipy

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup bazy
python hard_reset.py       # TAK
python seed_database.py --clear

# 4. Sprawdź
python db_status.py

# 5. Run
uvicorn app.main:app --reload
```

### Gdy zmieniasz strukturę bazy:

```bash
# 1. Backup (opcjonalnie)
python backup_restore.py backup

# 2. Hard reset
python hard_reset.py       # TAK

# 3. Reseed
python seed_database.py --clear

# 4. Verify
python db_status.py
```

### Gdy chcesz zachować dane:

```bash
# 1. Backup
python backup_restore.py backup

# 2. Edytuj modele w app/models/

# 3. Uruchom migrację
python run_migration.py

# 4. Verify
python db_status.py
```

## ✅ Checklist po setup

Po `hard_reset.py` + `seed_database.py` powinieneś mieć:

```bash
python db_status.py
```

Sprawdź:

- [x] ✅ Plik bazy: EXISTS
- [x] ✅ Schema award_types: NOWY (z lucide icons)
- [x] ✅ Schema users: NOWY (z is_admin)
- [x] ✅ Tabele: users, clips, awards, award_types
- [x] ✅ Users: 4 (1 admin)
- [x] ✅ Award types: ~10 (5 system + 4 personal + 1 custom)
- [x] ✅ Każdy użytkownik ma osobistą nagrodę
- [x] ✅ Clips: 4
- [x] ✅ Awards given: ~10-20 (losowe)

## 🆘 Troubleshooting

### Problem: "SQLAlchemy error: no such column"

```bash
# Schema jest stary, potrzebny hard reset
python hard_reset.py
python seed_database.py --clear
```

### Problem: "Personal award nie istnieje dla usera X"

```bash
# Seed ponownie - automatycznie utworzy brakujące
python seed_database.py --clear
```

### Problem: "Icon emoji zamiast lucide"

```bash
# Stary schema
python db_status.py  # sprawdź schema
python hard_reset.py # jeśli stary
```

### Problem: "Can't give award - permission denied"

```bash
# Sprawdź uprawnienia
python -c "
from app.core.database import SessionLocal
from app.models import User, AwardType

db = SessionLocal()
user = db.query(User).filter(User.username=='admin').first()
award = db.query(AwardType).first()

print(f'User: {user.username}, Admin: {user.is_admin}')
print(f'Award: {award.display_name}, Personal: {award.is_personal}')
print(f'Can give: {user.can_give_award(award)}')
"
```

### Problem: Database locked

```bash
# Zamknij wszystkie połączenia i spróbuj ponownie
pkill -f uvicorn
python hard_reset.py
```

## 📝 Notatki

- **SQLite limitation**: Nie można łatwo usunąć kolumny. Stara kolumna `icon` może pozostać ale nie jest używana.
- **Backupy**: Twórz backupy przed dużymi zmianami: `python backup_restore.py backup`
- **Seed script**: Zawsze aktualny, używaj go do testowania
- **Personal awards**: Tworzone automatycznie przy rejestracji nowego usera (TODO: dodać w auth router)

## 🔮 Przyszłe TODO

- [ ] Hook w auth router - twórz personal award przy rejestracji
- [ ] Endpoint do upload custom icon dla nagrody
- [ ] Endpoint do listowania dostępnych lucide icons
- [ ] Walidacja czy lucide icon istnieje
- [ ] Migracja danych z produkcji (jeśli będzie)