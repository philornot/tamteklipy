# TamteKlipy - Backend Database Management

TamteKlipy to prywatna platforma webowa do zarządzania klipami z gier oraz zrzutami ekranu, przeznaczona wyłącznie dla
zamkniętej grupy znajomych.

## 🚀 Quick Start

### Pierwszy setup projektu

```bash
# 1. Hard reset bazy (usuwa wszystko i tworzy nową strukturę)
python hard_reset.py
# Potwierdź wpisując: TAK

# 2. Zaseeduj testowe dane (użytkownicy, nagrody, klipy)
python seed_database.py --clear

# 3. Sprawdź czy wszystko OK
python db_status.py

# 4. Uruchom serwer
uvicorn app.main:app --reload
```

### Co otrzymasz po setup?

**4 Użytkowników:**

- **admin** / Admin123! [ADMIN]
- **gamer1** / Gamer1123!
- **gamer2** / Gamer2123!
- **viewer** / Viewer123!

**5 Systemowych nagród** (wszyscy mogą dawać):

- 🔥 Epic Clip (`flame` icon)
- 😂 Funny Moment (`laugh` icon)
- ⭐ Pro Play (`star` icon)
- ⚡ Clutch (`zap` icon)
- 👁️ WTF Moment (`eye` icon)

**4 Osobiste nagrody** (tylko twórca może dawać):

- 🏆 Nagroda Administrator (admin)
- 🏆 Nagroda Pro Gamer (gamer1)
- 🏆 Nagroda Casual Player (gamer2)
- 🏆 Nagroda Just Watching (viewer)

**2 Custom nagrody** (wszyscy mogą dawać):

- 👑 MVP of the Match (utworzona przez gamer1)
- 🍀 Lucky Shot (utworzona przez gamer2, z custom ikoną)

**4 Testowe klipy z losowymi nagrodami**

---

## 📋 Dostępne Skrypty

### `hard_reset.py` - Kompletny reset bazy ⚠️

Usuwa całą bazę danych i tworzy ją od nowa z nową strukturą.

```bash
python hard_reset.py
# Wpisz: TAK
```

**Kiedy używać:**

- ✅ Development - zmiany w strukturze bazy
- ✅ Naprawienie błędów migracji
- ✅ Fresh start projektu
- ❌ NIGDY w produkcji!

### `seed_database.py` - Dane testowe 🌱

Wypełnia bazę testowymi danymi.

**Co tworzy:**

- 4 użytkowników (1 admin)
- 5 systemowych nagród
- 4 osobiste nagrody (po 1 dla każdego usera)
- 2 custom nagrody
- 4 testowe klipy
- 10-20 losowych przyznanych nagród

```bash
# Dodaj dane (nie usuwa istniejących)
python seed_database.py

# Usuń wszystko i dodaj od nowa (zalecane)
python seed_database.py --clear
```

### `db_status.py` - Status bazy 📊

Pokazuje pełny status bazy danych.

```bash
python db_status.py
```

**Co sprawdza:**

- ✅ Czy plik bazy istnieje
- ✅ Czy schema jest aktualny
- ✅ Statystyki (users, clips, awards)
- ✅ Lista wszystkich typów nagród
- ✅ Lista użytkowników z ich nagrodami
- ✅ Czy każdy user ma osobistą nagrodę

### `test_permissions.py` - Test uprawnień 🔐

Testuje system uprawnień.

```bash
# Podsumowanie dla wszystkich
python test_permissions.py --all

# Szczegóły dla konkretnego usera
python test_permissions.py admin
python test_permissions.py gamer1

# Sprawdź kto może przyznać konkretną nagrodę
python test_permissions.py --award award:epic_clip
python test_permissions.py --award award:personal_gamer1
```

### `backup_restore.py` - Backup i restore 💾

Zarządzanie backupami bazy.

```bash
# Utwórz backup
python backup_restore.py backup

# Lista backupów
python backup_restore.py list
python backup_restore.py list --limit 5

# Restore z backupu
python backup_restore.py restore backups/tamteklipy_20250104_123456.db
# Wpisz: TAK

# Usuń stare backupy (zostaw 10 najnowszych)
python backup_restore.py cleanup --keep 10
```

### `run_migration.py` - Migracje 🔄

Alternatywa dla Alembic - ręczne migracje.

```bash
# Sprawdź status migracji
python run_migration.py --check

# Uruchom migrację
python run_migration.py

# Cofnij migrację
python run_migration.py --down
```

**Uwaga:** Przy hard reset migracja NIE jest potrzebna!

---

## 🗄️ Struktura Bazy Danych

### Tabela: `users`

```sql
id
INTEGER PRIMARY KEY
username            VARCHAR(50) UNIQUE
email               VARCHAR(100) UNIQUE
hashed_password     VARCHAR(255)
full_name           VARCHAR(100)
is_active           BOOLEAN DEFAULT TRUE
is_admin            BOOLEAN DEFAULT FALSE
award_scopes        JSON (deprecated)
```

### Tabela: `award_types`

```sql
id
INTEGER PRIMARY KEY
name                VARCHAR(100) UNIQUE
display_name        VARCHAR(100)
description         TEXT
lucide_icon         VARCHAR(100)        -- np. "trophy", "star"
custom_icon_path    VARCHAR(500)        -- ścieżka do custom ikony
color               VARCHAR(7)
created_by_user_id  INTEGER             -- właściciel nagrody
is_system_award     BOOLEAN DEFAULT FALSE
is_personal         BOOLEAN DEFAULT FALSE
created_at          DATETIME
updated_at          DATETIME
```

### Tabela: `awards`

```sql
id
INTEGER PRIMARY KEY
clip_id             INTEGER FK -> clips.id
user_id             INTEGER FK -> users.id
award_name          VARCHAR(100)
awarded_at          DATETIME

UNIQUE(clip_id, user_id, award_name)
```

### Tabela: `clips`

```sql
id
INTEGER PRIMARY KEY
filename            VARCHAR(255)
file_path           VARCHAR(500)
thumbnail_path      VARCHAR(500)
clip_type           VARCHAR(20)
file_size           INTEGER
duration            INTEGER
width               INTEGER
height              INTEGER
uploader_id         INTEGER FK -> users.id
created_at          DATETIME
```

---

## 🔑 System Uprawnień

### Admin (`is_admin=True`)

**Może przyznawać:**

- ✅ WSZYSTKIE nagrody (systemowe, osobiste innych userów, custom)
- ✅ Tworzyć nowe typy nagród
- ✅ Edytować/usuwać nagrody (poza systemowymi)
- ✅ Zarządzać użytkownikami

### Zwykły user

**Może przyznawać:**

- ✅ Nagrody systemowe (Epic Clip, Funny, etc.)
- ✅ TYLKO swoją osobistą nagrodę
- ✅ Custom nagrody (publiczne)
- ❌ Osobiste nagrody innych userów

**Może zarządzać:**

- ✅ Tworzyć własne custom nagrody
- ✅ Edytować/usuwać TYLKO własne

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

---

## 🎯 Typowe Scenariusze

### Scenariusz 1: Pierwszy setup projektu

```bash
cd backend
python hard_reset.py                    # TAK
python seed_database.py --clear
python db_status.py
uvicorn app.main:app --reload
```

### Scenariusz 2: Zmiana struktury bazy (development)

```bash
python backup_restore.py backup         # Safety first
python hard_reset.py                    # TAK
python seed_database.py --clear
python db_status.py
```

### Scenariusz 3: Coś się zepsuło, wracam do punktu wyjścia

```bash
rm tamteklipy.db
python hard_reset.py                    # TAK
python seed_database.py --clear
```

### Scenariusz 4: Testowanie uprawnień

```bash
python test_permissions.py --all
python test_permissions.py admin
python test_permissions.py gamer1
python test_permissions.py --award award:personal_gamer1
```

### Scenariusz 5: Przed deploy (backup)

```bash
python backup_restore.py backup
python backup_restore.py list
# Skopiuj backup w bezpieczne miejsce
```

### Scenariusz 6: Po deploy (restore jeśli coś poszło nie tak)

```bash
python backup_restore.py list
python backup_restore.py restore backups/tamteklipy_YYYYMMDD_HHMMSS.db
```

---

## 🆘 Troubleshooting

### Problem: `file is not a database`

**Najczęstszy błąd!** Plik bazy jest uszkodzony.

**Rozwiązanie:**

```bash
# Windows
del tamteklipy.db

# Linux/Mac
rm tamteklipy.db

# Teraz hard reset
python hard_reset.py
python seed_database.py --clear
```

Lub w PowerShell (Windows):

```powershell
Remove-Item -Force tamteklipy.db
python hard_reset.py
python seed_database.py --clear
```

### Problem: `no such column: award_types.lucide_icon`

```bash
python hard_reset.py    # TAK
python seed_database.py --clear
```

### Problem: `no such column: users.is_admin`

```bash
python hard_reset.py    # TAK
python seed_database.py --clear
```

### Problem: Brakuje osobistych nagród

```bash
python seed_database.py --clear
# Seed automatycznie utworzy brakujące
```

### Problem: Database is locked

```bash
# Zamknij wszystkie połączenia
pkill -f uvicorn
pkill -f python

# Spróbuj ponownie
python hard_reset.py
```

### Problem: Import errors

```bash
# Upewnij się że jesteś w katalogu backend/
cd backend

# Sprawdź czy wszystkie modele są zaimportowane
python -c "from app.models import User, AwardType, Clip, Award"
```

---

## 📊 Oczekiwane Wartości Po Fresh Setup

Po `hard_reset.py` + `seed_database.py --clear`:

```
✅ Plik bazy: EXISTS
✅ Schema award_types: NOWY (z lucide icons)
✅ Schema users: NOWY (z is_admin)
✅ Tabele: users, clips, awards, award_types (4 tabele)

📈 Statystyki:
  Users: 4 (1 admin)
  Clips: 4
  Przyznane nagrody: ~10-20 (losowe)
  Typy nagród: ~10
    - Systemowe: 5 (Epic Clip, Funny, Pro Play, Clutch, WTF)
    - Osobiste: 4 (po 1 dla każdego usera)
    - Custom: 2 (przykłady)

✅ Każdy użytkownik ma swoją osobistą nagrodę
```

---

## 🔗 Przydatne Endpointy API

Po uruchomieniu serwera:

- **Docs**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc
- **Health**: http://localhost:8000/health
- **Root**: http://localhost:8000/

### Quick API Test

```bash
# Health check
curl http://localhost:8000/health

# Login (get token)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123!"}'

# Get available awards (with token)
curl http://localhost:8000/api/my-awards \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🚨 Emergency Reset

Jeśli wszystko się zepsuło i nic nie działa:

```bash
# Nuclear option - usuwa wszystko
rm -f tamteklipy.db
rm -rf __pycache__
rm -rf app/__pycache__
rm -rf app/*/__pycache__

# Fresh start
python hard_reset.py              # TAK
python seed_database.py --clear
python db_status.py

# Should show all green checkmarks ✅
```

---

## 🎓 Dobre Praktyki

### ✅ Zawsze rób backup przed zmianami

```bash
python backup_restore.py backup
```

### ✅ Sprawdzaj status po każdej zmianie

```bash
python db_status.py
```

### ✅ Testuj uprawnienia po dodaniu nowych nagród

```bash
python test_permissions.py --all
```

### ✅ W development używaj --clear

```bash
python seed_database.py --clear
# Gwarantuje czysty stan
```

---

## 🔧 Uruchomienie Serwera

### Development mode

```bash
uvicorn app.main:app --reload
```

### Określ host i port

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production mode (bez reload)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📝 Kolejność Wykonywania (Best Practice)

```bash
# 1. Backup (jeśli masz wartościowe dane)
python backup_restore.py backup

# 2. Reset
python hard_reset.py

# 3. Seed
python seed_database.py --clear

# 4. Verify
python db_status.py

# 5. Test permissions
python test_permissions.py --all

# 6. Run server
uvicorn app.main:app --reload

# 7. Test API
curl http://localhost:8000/health
```

---

## 🎯 One-Liners

```bash
# Full reset in one line
python hard_reset.py && python seed_database.py --clear && python db_status.py

# Check everything
python db_status.py && python test_permissions.py --all

# Backup and reset
python backup_restore.py backup && python hard_reset.py && python seed_database.py --clear

# Reset and run
python hard_reset.py && python seed_database.py --clear && uvicorn app.main:app --reload
```

---

## 💡 Pro Tips

### Dodaj aliasy do `.bashrc` lub `.zshrc`:

```bash
alias tk-reset="python hard_reset.py && python seed_database.py --clear && python db_status.py"
alias tk-status="python db_status.py"
alias tk-perms="python test_permissions.py --all"
alias tk-backup="python backup_restore.py backup"
alias tk-run="uvicorn app.main:app --reload"
```

Wtedy możesz używać:

```bash
tk-reset    # Full reset
tk-status   # Check status
tk-perms    # Check permissions
tk-backup   # Create backup
tk-run      # Run server
```

---

## 🗂️ Struktura Projektu

```
backend/
├── 🚀 Skrypty wykonywalne
│   ├── hard_reset.py
│   ├── seed_database.py
│   ├── db_status.py
│   ├── test_permissions.py
│   ├── backup_restore.py
│   └── run_migration.py
│
├── 🗄️ Aplikacja
│   └── app/
│       ├── core/
│       │   ├── config.py
│       │   ├── database.py
│       │   ├── init_db.py
│       │   └── security.py
│       └── models/
│           ├── user.py
│           ├── award_type.py
│           ├── award.py
│           └── clip.py
│
├── 💾 Dane
│   ├── tamteklipy.db
│   └── backups/
│       └── tamteklipy_TIMESTAMP.db
│
└── 📝 Config
    ├── alembic.ini
    ├── requirements.txt
    └── .env
```

---

## 🔍 Debugging & Diagnostyka

### Python REPL - quick check

```bash
python -c "
from app.core.database import SessionLocal
from app.models import User, AwardType

db = SessionLocal()
print(f'Users: {db.query(User).count()}')
print(f'Awards: {db.query(AwardType).count()}')
print(f'Admins: {db.query(User).filter(User.is_admin==True).count()}')
"
```

### Sprawdź konkretnego usera

```bash
python -c "
from app.core.database import SessionLocal
from app.models import User

db = SessionLocal()
user = db.query(User).filter(User.username=='admin').first()
print(f'Username: {user.username}')
print(f'Email: {user.email}')
print(f'Admin: {user.is_admin}')
print(f'Active: {user.is_active}')
"
```

### Sprawdź nagrody

```bash
python -c "
from app.core.database import SessionLocal
from app.models import AwardType

db = SessionLocal()
awards = db.query(AwardType).all()
for a in awards:
    print(f'{a.name:30} | {a.display_name:25} | System: {a.is_system_award} | Personal: {a.is_personal}')
"
```

---

## 📚 Informacje o Projekcie

### Najważniejsze funkcje

- **Bezpieczne uwierzytelnianie** – logowanie z użyciem JWT, hasła hashowane bcryptem
- **Wgrywanie i przechowywanie klipów oraz screenshotów** – pliki przechowywane lokalnie na serwerze
- **Automatyczne generowanie miniatur** – szybki podgląd zawartości
- **Przeglądanie w formie siatki** – wygodny widok galerii z miniaturami
- **Odtwarzacz wideo w modalu** – szybkie oglądanie klipów bez opuszczania strony
- **System nagród** – uprawnienia i dostęp do dodatkowych funkcji dla aktywnych użytkowników
- **Prywatność** – dostęp tylko dla zaproszonych osób, brak indeksowania przez wyszukiwarki

### Wymagania sprzętowe i wdrożenie

- Projekt działa na Raspberry Pi Zero 2 W z dyskiem USB (ext4)
- Dostęp przez HTTPS zapewnia Cloudflare Tunnel
- Usługi uruchamiane jako systemd

### Bezpieczeństwo

- Hasła: hashowanie bcrypt
- Autoryzacja: tokeny JWT z TTL i uprawnieniami
- Transport: HTTPS
- Walidacja danych wejściowych i limitowanie zapytań

### Licencja

Projekt prywatny – Wszelkie prawa zastrzeżone