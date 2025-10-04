# TamteKlipy - Commands Cheatsheet 🚀

Szybki ściągawka z wszystkimi komendami do zarządzania bazą danych.

## 🔥 Quick Start (Fresh Setup)

```bash
# Kompletny reset i setup
python hard_reset.py && python seed_database.py --clear && python db_status.py
```

## 📋 Podstawowe Komendy

### Hard Reset (Usuwa wszystko!)
```bash
python hard_reset.py
# Wpisz: TAK
```

### Seed z danymi testowymi
```bash
python seed_database.py --clear
```

### Sprawdź status bazy
```bash
python db_status.py
```

### Test uprawnień
```bash
# Podsumowanie wszystkich
python test_permissions.py --all

# Konkretny user
python test_permissions.py admin
python test_permissions.py gamer1

# Konkretna nagroda
python test_permissions.py --award award:epic_clip
python test_permissions.py --award award:personal_admin
```

## 💾 Backup & Restore

### Utwórz backup
```bash
python backup_restore.py backup
```

### Lista backupów
```bash
python backup_restore.py list
python backup_restore.py list --limit 5
```

### Restore z backupu
```bash
python backup_restore.py restore backups/tamteklipy_20250104_123456.db
# Wpisz: TAK
```

### Wyczyść stare backupy (zostaw 10 najnowszych)
```bash
python backup_restore.py cleanup --keep 10
```

## 🔧 Migracje (jeśli używasz Alembic)

### Sprawdź status migracji
```bash
python run_migration.py --check
```

### Uruchom migrację
```bash
python run_migration.py
```

### Cofnij migrację
```bash
python run_migration.py --down
```

## 🚀 Uruchomienie Serwera

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
    - Custom: 1-2 (przykłady)

✅ Każdy użytkownik ma swoją osobistą nagrodę
```

## 🐛 Troubleshooting

### Problem: `no such column: award_types.lucide_icon`
**Rozwiązanie:**
```bash
python hard_reset.py    # TAK
python seed_database.py --clear
```

### Problem: `no such column: users.is_admin`
**Rozwiązanie:**
```bash
python hard_reset.py    # TAK
python seed_database.py --clear
```

### Problem: Brakuje osobistych nagród
**Rozwiązanie:**
```bash
python seed_database.py --clear
# Seed automatycznie utworzy brakujące
```

### Problem: Database is locked
**Rozwiązanie:**
```bash
# Zamknij wszystkie połączenia
pkill -f uvicorn
pkill -f python

# Spróbuj ponownie
python hard_reset.py
```

### Problem: Import errors
**Rozwiązanie:**
```bash
# Upewnij się że jesteś w katalogu backend/
cd backend

# Sprawdź czy wszystkie modele są zaimportowane
python -c "from app.models import User, AwardType, Clip, Award"
```

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

### ✅ Dokumentuj własne custom nagrody
```bash
# Dodaj do dokumentacji jakie custom nagrody utworzyłeś
# i kto może je przyznawać
```

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

## 📚 Więcej Informacji

- **Full setup guide**: `README_DATABASE_SETUP.md`
- **Migration guide**: `MIGRATION_GUIDE.md`
- **Quick start**: `QUICK_START.md`

## 🎯 One-Liners

```bash
# Full reset in one line
python hard_reset.py && echo "TAK" | python hard_reset.py && python seed_database.py --clear && python db_status.py

# Check everything
python db_status.py && python test_permissions.py --all

# Backup and reset
python backup_restore.py backup && python hard_reset.py && python seed_database.py --clear

# Reset and run
python hard_reset.py && python seed_database.py --clear && uvicorn app.main:app --reload
```

---

💡 **Pro Tip**: Dodaj alias do `.bashrc` lub `.zshrc`:

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