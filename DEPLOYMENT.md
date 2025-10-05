# TamteKlipy Deployment Guide

## 🚀 Normalny deployment (99% przypadków)

Na RPi uruchom:

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
- ✅ Buduje frontend
- ✅ Restartuje backend
- ✅ Sprawdza czy wszystko działa

---

## 🔧 Workflow development → production

### Na Windows (PyCharm):

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

## 📁 Ważne pliki

### Konfiguracja (nie w git):

- `backend/.env` - konfiguracja produkcyjna backendu
- `backend/tamteklipy.db` - baza danych SQLite

### Logi:

- `backend/logs/tamteklipy.log` - wszystkie logi
- `backend/logs/errors.log` - tylko błędy

### Frontend:

- `frontend/.env.production` - URL backendu (w git ✅)
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

# Restart backendu
sudo systemctl restart tamteklipy-backend

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

