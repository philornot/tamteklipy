# 📑 Index Skryptów i Dokumentacji - TamteKlipy

## 🚀 Skrypty Wykonywalne

### Główne skrypty zarządzania bazą:

| Skrypt                  | Przeznaczenie                       | Użycie                             |
|-------------------------|-------------------------------------|------------------------------------|
| **hard_reset.py**       | Kompletny reset bazy danych         | `python hard_reset.py`             |
| **seed_database.py**    | Dodanie testowych danych            | `python seed_database.py --clear`  |
| **db_status.py**        | Sprawdzenie statusu bazy            | `python db_status.py`              |
| **test_permissions.py** | Test uprawnień użytkowników         | `python test_permissions.py --all` |
| **backup_restore.py**   | Backup i restore bazy               | `python backup_restore.py backup`  |
| **run_migration.py**    | Migracje bazy (Alembic alternative) | `python run_migration.py --check`  |

### Szczegóły skryptów:

#### 1. **hard_reset.py** ⚠️

Usuwa całą bazę danych i tworzy ją od nowa z nową strukturą.

**Kiedy używać:**

- ✅ Development - zmiany w strukturze bazy
- ✅ Naprawienie błędów migracji
- ✅ Fresh start projektu
- ❌ NIGDY w produkcji!

**Przykład:**

```bash
python hard_reset.py
# Wpisz: TAK
```

#### 2. **seed_database.py** 🌱

Wypełnia bazę testowymi danymi.

**Co tworzy:**

- 4 użytkowników (1 admin)
- 5 systemowych nagród
- 4 osobiste nagrody
- 2 custom nagrody
- 4 testowe klipy
- 10-20 losowych przyznanych nagród

**Opcje:**

```bash
python seed_database.py          # Dodaj dane (nie usuwa istniejących)
python seed_database.py --clear  # Usuń wszystko i dodaj od nowa (zalecane)
```

#### 3. **db_status.py** 📊

Pokazuje pełny status bazy danych.

**Co sprawdza:**

- ✅ Czy plik bazy istnieje
- ✅ Czy schema jest aktualny
- ✅ Statystyki (users, clips, awards)
- ✅ Lista wszystkich typów nagród
- ✅ Lista użytkowników z ich nagrodami
- ✅ Czy każdy user ma osobistą nagrodę

**Przykład:**

```bash
python db_status.py
```

#### 4. **test_permissions.py** 🔐

Testuje system uprawnień.

**Tryby:**

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

#### 5. **backup_restore.py** 💾

Zarządzanie backupami bazy.

**Komendy:**

```bash
# Utwórz backup
python backup_restore.py backup

# Lista backupów
python backup_restore.py list
python backup_restore.py list --limit 5

# Restore z backupu
python backup_restore.py restore backups/tamteklipy_20250104_123456.db

# Usuń stare backupy (zostaw 10 najnowszych)
python backup_restore.py cleanup --keep 10
```

#### 6. **run_migration.py** 🔄

Alternatywa dla Alembic - ręczne migracje.

**Komendy:**

```bash
# Sprawdź status migracji
python run_migration.py --check

# Uruchom migrację
python run_migration.py

# Cofnij migrację
python run_migration.py --down
```

**Uwaga:** Przy hard reset migracja NIE jest potrzebna!

## 📚 Dokumentacja

### Przewodniki i dokumenty:

| Dokument                     | Opis                                        |
|------------------------------|---------------------------------------------|
| **START_HERE.txt**           | 👈 Zacznij tutaj! Quick start w 4 komendach |
| **COMMANDS_CHEATSHEET.md**   | 📋 Ściągawka ze wszystkimi komendami        |
| **README_DATABASE_SETUP.md** | 📖 Pełna dokumentacja setup'u               |
| **QUICK_START.md**           | ⚡ Szybki przewodnik dla developerów         |
| **MIGRATION_GUIDE.md**       | 🔄 Szczegóły migracji (dla Alembic)         |
| **INDEX_SKRYPTÓW.md**        | 📑 Ten plik - index wszystkiego             |

### Co znajdziesz w każdym:

#### **START_HERE.txt** ⭐

**Dla kogo:** Nowi developerzy, pierwszy setup
**Co zawiera:**

- 4 komendy do quick start
- Co otrzymasz po setup
- Podstawowe informacje o userach i nagrodach

#### **COMMANDS_CHEATSHEET.md** 📋

**Dla kogo:** Wszyscy - trzymaj pod ręką!
**Co zawiera:**

- Wszystkie dostępne komendy
- Typowe scenariusze użycia
- Troubleshooting
- One-liners
- Pro tips z aliasami

#### **README_DATABASE_SETUP.md** 📖

**Dla kogo:** Full reference
**Co zawiera:**

- Pełna dokumentacja struktury bazy
- Szczegóły wszystkich skryptów
- System uprawnień (kto może co)
- Workflow developmentu
- Szczegółowy troubleshooting
- Checklist po setup

#### **QUICK_START.md** ⚡

**Dla kogo:** Quick reference
**Co zawiera:**

- Fast setup w developmencie
- Co powstaje domyślnie
- Logika uprawnień
- Design principles nagród

#### **MIGRATION_GUIDE.md** 🔄

**Dla kogo:** Gdy używasz Alembic
**Co zawiera:**

- Zmiany w strukturze bazy
- Jak uruchomić migrację
- Co robi migracja
- Rollback instructions
- Przykładowe zapytania

## 🗂️ Struktura Projektu (Database Management)

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
├── 📚 Dokumentacja
│   ├── START_HERE.txt              ⭐ Zacznij tutaj
│   ├── COMMANDS_CHEATSHEET.md      📋 Wszystkie komendy
│   ├── README_DATABASE_SETUP.md    📖 Full docs
│   ├── QUICK_START.md              ⚡ Quick reference
│   ├── MIGRATION_GUIDE.md          🔄 Migracje
│   └── INDEX_SKRYPTÓW.md           📑 Ten plik
│
├── 🗄️ Aplikacja
│   └── app/
│       ├── core/
│       │   ├── config.py
│       │   ├── database.py
│       │   ├── init_db.py          (funkcja create_personal_award_for_user)
│       │   └── security.py
│       └── models/
│           ├── user.py             (+ is_admin, can_give_award())
│           ├── award_type.py       (nowy schema z lucide icons)
│           ├── award.py
│           └── clip.py
│
├── 💾 Dane
│   ├── tamteklipy.db               (SQLite database)
│   └── backups/                    (automatyczne backupy)
│       └── tamteklipy_TIMESTAMP.db
│
└── 📝 Config
    ├── alembic.ini
    └── .env
```

## 🎯 Typowe Przepływy Pracy

### 1️⃣ Pierwszy Setup

```
START_HERE.txt → hard_reset.py → seed_database.py → db_status.py → run server
```

### 2️⃣ Codzienny Development

```
COMMANDS_CHEATSHEET.md (reference) → edit code → test → commit
```

### 3️⃣ Zmiana Struktury Bazy

```
backup_restore.py backup → edit models → hard_reset.py → seed_database.py
```

### 4️⃣ Debugging Uprawnień

```
test_permissions.py --all → test_permissions.py <username> → fix → test again
```

### 5️⃣ Przed Deploy

```
README_DATABASE_SETUP.md (checklist) → backup_restore.py backup → test production
```

## 🔍 Jak Znaleźć Co Potrzebujesz?

### "Jak zacząć projekt?"

→ **START_HERE.txt**

### "Jakie komendy są dostępne?"

→ **COMMANDS_CHEATSHEET.md**

### "Jak działa system uprawnień?"

→ **README_DATABASE_SETUP.md** (sekcja "System uprawnień")

### "Jak przetestować uprawnienia?"

→ `python test_permissions.py --all`

### "Coś się zepsuło, co robić?"

→ **COMMANDS_CHEATSHEET.md** (sekcja "Troubleshooting")

### "Jak zrobić backup?"

→ `python backup_restore.py backup`

### "Jak zmienić strukturę bazy?"

→ **README_DATABASE_SETUP.md** (sekcja "Workflow developmentu")

### "Jak działa migracja?"

→ **MIGRATION_GUIDE.md**

## 📞 Quick Reference

```bash
# Quick Start
python hard_reset.py && python seed_database.py --clear

# Check Status
python db_status.py

# Test Permissions
python test_permissions.py --all

# Backup
python backup_restore.py backup

# Run Server
uvicorn app.main:app --reload
```

---

**💡 Pro Tip:** Dodaj ten folder do zakładek i trzymaj COMMANDS_CHEATSHEET.md zawsze pod ręką!