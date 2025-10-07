# TamteKlipy Deployment Guide

## 🚀 Normalny deployment (99% przypadków)

### Windows (Git Bash):

```bash
# W katalogu projektu
bash deploy.sh
```

Skrypt automatycznie:
- ✅ Commitujesz i pushujesz zmiany do GitHuba
- ✅ Budujesz frontend lokalnie
- ✅ Przesyłasz pliki na RPi przez SSH
- ✅ Uruchamia deployment na RPi zdalnie

### Na RPi:

```bash
cd ~/tamteklipy
bash deploy.sh
```

**To wszystko!** Skrypt automatycznie:

- ✅ Ściąga kod z git
- ✅ Tworzy .env jeśli nie istnieje
- ✅ Generuje bezpieczny SECRET_KEY
- ✅ Inicjalizuje bazę danych
- ✅ Tworzy admina jeśli baza pusta
- ✅ Restartuje backend i frontend
- ✅ Sprawdza czy wszystko działa

---

## 🔧 Opcje deploymentu

Możesz deployować tylko część aplikacji:

```bash
# Tylko backend
bash deploy.sh -b
# lub
bash deploy.sh --backend

# Tylko frontend
bash deploy.sh -f
# lub
bash deploy.sh --frontend

# Pomoc
bash deploy.sh -h
# lub
bash deploy.sh --help
```

---

## 🔧 Workflow development → production

### Na Windows (PyCharm/Git Bash):

Wystarczy uruchomić:
```bash
bash deploy.sh
```

Skrypt:
1. Pyta o commit message (jeśli są zmiany)
2. Commituje i pushujesz zmiany
3. Buduje frontend
4. Przesyła pliki na RPi
5. Uruchamia deployment na RPi

### Ręczny workflow (jeśli wolisz):

1. Kodujesz
2. `git add .`
3. `git commit -m "opis zmian"`
4. `git push`

### Na RPi:

```bash
cd ~/tamteklipy
bash deploy.sh
```

**Gotowe!** 🎉

---

## 🆘 Troubleshooting

### Problem: Hasło nie działa

```bash
cd ~/tamteklipy/backend
source venv/bin/activate
python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

db = SessionLocal()
user = db.query(User).filter(User.username == 'philornot').first()
if user:
    user.hashed_password = hash_password('NoweHaslo123')
    db.commit()
    print('✅ Hasło zmienione: philornot / NoweHaslo123')
else:
    print('❌ User nie istnieje, uruchom: python seed_database.py --clear')
db.close()
"
```

### Problem: Baza się zepsuła

```bash
cd ~/tamteklipy/backend
rm tamteklipy.db
cd ..
bash deploy.sh  # Automatycznie odtworzy
```

### Problem: Backend nie startuje

```bash
# Zobacz co jest nie tak
sudo systemctl status tamteklipy-backend
tail -f ~/tamteklipy/backend/logs/tamteklipy.log

# Restart ręczny
sudo systemctl restart tamteklipy-backend
```

### Problem: Frontend pokazuje stare dane

```bash
cd ~/tamteklipy/frontend
rm -rf dist node_modules .pnpm-store
cd ..
bash deploy.sh  # Rebuild wszystkiego
```

---

## 📁 Ważne pliki i katalogi

### Konfiguracja (nie w git):

- `backend/.env` - konfiguracja produkcyjna backendu
  - Zawiera: SECRET_KEY, ścieżki do plików, limity wielkości plików, itp.
- `backend/tamteklipy.db` - baza danych SQLite
- `frontend/.env.production` - URL backendu (w git ✅)

### Logi:

- `backend/logs/tamteklipy.log` - wszystkie logi
- `backend/logs/errors.log` - tylko błędy

### Ścieżki plików:

- `/mnt/tamteklipy/clips` - przesłane klipy wideo
- `/mnt/tamteklipy/screenshots` - zrzuty ekranu
- `/mnt/tamteklipy/thumbnails` - miniatury
- `/mnt/tamteklipy/metadata` - metadane plików
- `/mnt/tamteklipy/award_icons` - ikony odznaczeń

### Frontend:

- `frontend/dist/` - zbudowana aplikacja

---

## 🔐 Domyślne dane logowania

Po `bash deploy.sh` na pustej bazie:

**Username:** `philornot`  
**Password:** `HasloFilipa`

(Admin z wszystkimi uprawnieniami)

---

## 🎯 Quick commands

```bash
# Deploy
bash deploy.sh

# Zobacz logi na żywo
tail -f backend/logs/tamteklipy.log

# Sprawdź status backendu
sudo systemctl status tamteklipy-backend

# Sprawdź status frontendu
sudo systemctl status tamteklipy-frontend

# Restart backendu
sudo systemctl restart tamteklipy-backend

# Restart frontendu
sudo systemctl restart tamteklipy-frontend

# Sprawdź czy API działa
curl http://localhost:8000/health

# Zobacz użytkowników w bazie
cd backend
source venv/bin/activate
python -c "
from app.core.database import SessionLocal
from app.models.user import User
db = SessionLocal()
for u in db.query(User).all():
    print(f'{u.username} (admin: {u.is_admin})')
db.close()
"
```

---

## ⚠️ Nigdy nie commituj do git:
(wszystko to jest w `.gitignore`)
- `backend/.env` (zawiera SECRET_KEY)
- `backend/tamteklipy.db` (baza danych)
- `backend/logs/` (logi)
- `frontend/dist/` (build)
- `backend/venv/` (virtual environment)
