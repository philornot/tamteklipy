# Quick Start - Development Setup

## 🔄 Hard Reset (Clean Slate)

Jeśli chcesz zacząć od zera z nową strukturą bazy:

```bash
# 1. Hard reset bazy danych
python hard_reset.py
# Wpisz 'TAK' żeby potwierdzić

# 2. Zaseeduj testowe dane
python seed_database.py --clear

# 3. Sprawdź status
python db_status.py

# 4. Uruchom serwer
python -m uvicorn app.main:app --reload
```

## ✅ Co powstaje po hard reset?

### Systemowe nagrody (dostępne dla wszystkich):

- 🔥 **Epic Clip** (`flame` icon)
- 😂 **Funny Moment** (`laugh` icon)
- ⭐ **Pro Play** (`star` icon)
- ⚡ **Clutch** (`zap` icon)
- 👁️ **WTF Moment** (`eye` icon)

### Testowi użytkownicy (po seed):

```
admin    | admin@tamteklipy.local    | Admin123!    | [ADMIN]
gamer1   | gamer1@tamteklipy.local   | Gamer1123!   | 
gamer2   | gamer2@tamteklipy.local   | Gamer2123!   | 
viewer   | viewer@tamteklipy.local   | Viewer123!   | 
```

### Osobiste nagrody (automatycznie tworzone):

- 🏆 **Nagroda Administrator** (tylko admin może przyznać)
- 🏆 **Nagroda Pro Gamer** (tylko gamer1 może przyznać)
- 🏆 **Nagroda Casual Player** (tylko gamer2 może przyznać)
- 🏆 **Nagroda Just Watching** (tylko viewer może przyznać)

### Dodatkowe custom nagrody (przykłady):

- 👑 **MVP of the Match** by gamer1 (publiczna)
- 🍀 **Lucky Shot** by gamer2 (publiczna, custom icon)

## 📋 Komendy pomocnicze

```bash
# Sprawdź status bazy
python db_status.py

# Reset i reseed
python hard_reset.py && python seed_database.py --clear

# Tylko reseed (bez resetowania)
python seed_database.py --clear

# Sprawdź czy migracja jest aktualna (jeśli używasz Alembic)
python run_migration.py --check
```

## 🗂️ Struktura po seedzie

```
Users: 4 (1 admin)
├── admin (ADMIN)
│   ├── Osobista nagroda: "Nagroda Administrator"
│   ├── Może dawać: WSZYSTKIE nagrody
│   └── Może tworzyć: nowe nagrody
│
├── gamer1
│   ├── Osobista nagroda: "Nagroda Pro Gamer"
│   ├── Custom nagroda: "MVP of the Match"
│   ├── Może dawać: systemowe + własne
│   └── Uploaded clips: 1
│
├── gamer2
│   ├── Osobista nagroda: "Nagroda Casual Player"
│   ├── Custom nagroda: "Lucky Shot" (custom icon)
│   ├── Może dawać: systemowe + własne
│   └── Uploaded clips: 1
│
└── viewer
    ├── Osobista nagroda: "Nagroda Just Watching"
    ├── Może dawać: systemowe + własną
    └── Uploaded clips: 1

Award Types: 10
├── System awards: 5
├── Personal awards: 4
└── Custom awards: 1

Clips: 4
├── epic_pentakill.mp4 (admin)
├── funny_fail.mp4 (gamer1)
├── clutch_1v5.mp4 (gamer2)
└── beautiful_screenshot.png (viewer)
```

## 🎯 Logika uprawnień

### Admin może:

- ✅ Przyznawać WSZYSTKIE nagrody (systemowe, osobiste, custom)
- ✅ Tworzyć nowe typy nagród
- ✅ Edytować/usuwać nagrody (poza systemowymi)
- ✅ Zarządzać użytkownikami

### Zwykły user może:

- ✅ Przyznawać nagrody systemowe (Epic Clip, Funny, etc.)
- ✅ Przyznawać TYLKO swoją osobistą nagrodę
- ✅ Przyznawać custom nagrody (publiczne)
- ❌ Przyznawać osobiste nagrody innych userów
- ✅ Tworzyć własne custom nagrody
- ✅ Edytować/usuwać TYLKO własne nagrody

## 🔍 Weryfikacja

Po hard reset sprawdź:

```bash
# 1. Status bazy
python db_status.py

# Powinno pokazać:
# ✅ Plik bazy: EXISTS
# ✅ Schema award_types: NOWY (z lucide icons)
# ✅ Schema users: NOWY (z is_admin)
# ✅ Każdy użytkownik ma swoją osobistą nagrodę
```

## 🚀 Ready to go!

Teraz możesz:

1. Uruchomić backend: `uvicorn app.main:app --reload`
2. Odwiedzić docs: http://localhost:8000/docs
3. Zalogować się jako `admin` / `Admin123!`
4. Testować nowy system nagród!

## 🆘 Troubleshooting

### Problem: Baza ma stary schema

```bash
python hard_reset.py
python seed_database.py --clear
```

### Problem: Brakuje osobistych nagród

```bash
python seed_database.py --clear
# (seed automatycznie utworzy brakujące osobiste nagrody)
```

### Problem: Token errors

```bash
# Usuń stare tokeny i zaloguj się ponownie
```

### Problem: SQLite errors

```bash
# Kompletny reset
rm tamteklipy.db
python hard_reset.py
python seed_database.py --clear
```