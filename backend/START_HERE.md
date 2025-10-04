# 🚀 START HERE - TamteKlipy Database Setup

## Jesteś na etapie developmentu i chcesz zacząć od zera?

Wykonaj te 4 komendy:

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

## ✅ Co otrzymasz?

### 4 Użytkowników:

- **admin** / Admin123! [ADMIN]
- **gamer1** / Gamer1123!
- **gamer2** / Gamer2123!
- **viewer** / Viewer123!

### 5 Systemowych nagród (wszyscy mogą dawać):

- 🔥 Epic Clip
- 😂 Funny Moment
- ⭐ Pro Play
- ⚡ Clutch
- 👁️ WTF Moment

### 4 Osobiste nagrody (tylko twórca może dawać):

- 🏆 Nagroda Administrator (admin)
- 🏆 Nagroda Pro Gamer (gamer1)
- 🏆 Nagroda Casual Player (gamer2)
- 🏆 Nagroda Just Watching (viewer)

### 2 Custom nagrody (wszyscy mogą dawać):

- 👑 MVP of the Match (utworzona przez gamer1)
- 🍀 Lucky Shot (utworzona przez gamer2, z custom ikoną)

### 4 Testowe klipy z nagrodami

## 🔍 Sprawdź co masz

```bash
# Status bazy danych
python db_status.py

# Kto może jakie nagrody dawać?
python test_permissions.py --all

# Szczegóły dla konkretnego usera
python test_permissions.py admin
```

## 📚 Dokumentacja

- **COMMANDS_CHEATSHEET.md** - Wszystkie dostępne komendy
- **README_DATABASE_SETUP.md** - Pełna dokumentacja
- **QUICK_START.md** - Szybki start

## 🆘 Coś nie działa?

```bash
# Spróbuj emergency reset
rm tamteklipy.db
python hard_reset.py
python seed_database.py --clear
```

## 🌐 API Docs

Po uruchomieniu serwera:

- http://localhost:8000/docs (Swagger)
- http://localhost:8000/redoc (ReDoc)

Zaloguj się jako **admin** / **Admin123!** i testuj!

---

**Następne kroki**: Zobacz COMMANDS_CHEATSHEET.md dla wszystkich dostępnych komend.