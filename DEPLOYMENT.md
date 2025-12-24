# TamteKlipy Deployment Guide

## 🚀 Normalny deployment (99% przypadków)

### Windows (Git Bash):

```bash
# W katalogu projektu
bash deploy.sh
```

Skrypt automatycznie:

- ✅ Commituje i pushuje zmiany do GitHuba
- ✅ Buduje frontend lokalnie
- ✅ Przesyła pliki na RPi przez SSH
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

# Pull bez commita (użyteczne gdy ktoś inny wrzucił zmiany)
bash deploy.sh -p
# lub
bash deploy.sh --pull-only

# Dry run (pokaż co zostanie zrobione bez wykonywania)
bash deploy.sh --dry-run

# Pomiń backup bazy danych
bash deploy.sh --no-backup

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
2. Commituje i pushuje zmiany
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
python reset_password.py philornot NoweHaslo123
```

Lub ręcznie:

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

# Backup (na wszelki wypadek)
cp tamteklipy.db tamteklipy.db.backup

# Usuń i odtwórz
rm tamteklipy.db
cd ..
bash deploy.sh  # Automatycznie odtworzy
```

### Problem: Backend nie startuje

```bash
# Zobacz co jest nie tak
sudo systemctl status tamteklipy-backend
sudo journalctl -u tamteklipy-backend -n 50

# Sprawdź logi aplikacji
tail -f ~/tamteklipy/backend/logs/tamteklipy.log

# Restart ręczny
sudo systemctl restart tamteklipy-backend
```

### Problem: Frontend pokazuje stare dane

```bash
# Na Windows: przebuduj i wyślij
cd ~/tamteklipy/frontend
rm -rf dist node_modules .pnpm-store
cd ..
bash deploy.sh  # Rebuild wszystkiego
```

### Problem: Pendrive nie jest zamontowany

```bash
# Sprawdź czy pendrive jest podłączony
lsblk

# Zamontuj
sudo mount /dev/sda1 /mnt/tamteklipy

# Jeśli nie działa, sprawdź czy katalog istnieje
sudo mkdir -p /mnt/tamteklipy
sudo mount /dev/sda1 /mnt/tamteklipy

# Dodaj do /etc/fstab aby montował się automatycznie
echo "/dev/sda1 /mnt/tamteklipy ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
```

### Problem: Brak miejsca na dysku

```bash
# Sprawdź dostępne miejsce
df -h /mnt/tamteklipy

# Usuń stare backupy (starsze niż 30 dni)
find ~/tamteklipy/backend/backups -name "*.db" -type f -mtime +30 -delete

# Wyczyść logi starsze niż 7 dni
find ~/tamteklipy/backend/logs -name "*.log" -type f -mtime +7 -delete
```

### Problem: SSH nie działa z Windows

```bash
# Sprawdź połączenie
ssh frpi

# Jeśli nie działa, sprawdź konfigurację w ~/.ssh/config
cat ~/.ssh/config

# Powinno być coś takiego:
# Host frpi
#   HostName 192.168.x.x
#   User filip
#   IdentityFile ~/.ssh/id_rsa

# Jeśli nie masz klucza SSH, wygeneruj:
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Skopiuj na RPi:
ssh-copy-id frpi
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

### Ścieżki plików (na pendrive):

- `/mnt/tamteklipy/clips` - przesłane klipy wideo
- `/mnt/tamteklipy/screenshots` - zrzuty ekranu
- `/mnt/tamteklipy/thumbnails` - miniatury
- `/mnt/tamteklipy/metadata` - metadane plików
- `/mnt/tamteklipy/award_icons` - ikony odznaczeń

### Frontend:

- `frontend/dist/` - zbudowana aplikacja

### Backupy:

- `backend/backups/` - automatyczne backupy bazy danych (max 7 dni)

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

# Deploy tylko backend
bash deploy.sh -b

# Deploy tylko frontend
bash deploy.sh -f

# Dry run (test bez zmian)
bash deploy.sh --dry-run

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

# Sprawdź status bazy danych
cd backend
python db_status.py

# Utwórz backup ręcznie
cd backend
python backup_restore.py backup

# Lista backupów
cd backend
python backup_restore.py list
```

---

## ⚠️ Nigdy nie commituj do git:

(wszystko to jest w `.gitignore`)

- `backend/.env` (zawiera SECRET_KEY)
- `backend/tamteklipy.db` (baza danych)
- `backend/logs/` (logi)
- `frontend/dist/` (build)
- `backend/venv/` (virtual environment)
- `backend/backups/` (backupy bazy danych)

---

## 🔍 Diagnostyka

### Sprawdź czy wszystko działa:

```bash
# 1. Backend
curl http://localhost:8000/health

# 2. Frontend (powinien zwrócić HTML)
curl http://localhost:3000

# 3. Logi backend
tail -n 50 ~/tamteklipy/backend/logs/tamteklipy.log

# 4. Status serwisów
sudo systemctl status tamteklipy-backend
sudo systemctl status tamteklipy-frontend

# 5. Sprawdź czy pendrive jest zamontowany
df -h /mnt/tamteklipy

# 6. Sprawdź czy baza jest OK
cd ~/tamteklipy/backend
python db_status.py
```

### Restart kompletny (nuclear option):

```bash
cd ~/tamteklipy

# Stop wszystko
sudo systemctl stop tamteklipy-backend
sudo systemctl stop tamteklipy-frontend

# Wyczyść logi
> backend/logs/tamteklipy.log
> backend/logs/errors.log

# Start wszystko
sudo systemctl start tamteklipy-backend
sudo systemctl start tamteklipy-frontend

# Sprawdź status
sleep 2
sudo systemctl status tamteklipy-backend
sudo systemctl status tamteklipy-frontend
```

---

## 📊 Monitorowanie

### Sprawdzanie logów w czasie rzeczywistym:

```bash
# Backend logs
tail -f ~/tamteklipy/backend/logs/tamteklipy.log

# Tylko błędy
tail -f ~/tamteklipy/backend/logs/errors.log

# Systemd logs (backend)
sudo journalctl -u tamteklipy-backend -f

# Systemd logs (frontend)
sudo journalctl -u tamteklipy-frontend -f
```

### Sprawdzanie zasobów:

```bash
# Wykorzystanie dysku
df -h /mnt/tamteklipy

# Wykorzystanie RAM/CPU
htop

# Procesy Python
ps aux | grep python

# Procesy Node (frontend)
ps aux | grep node
```

---

## 🏗️ Pierwsze uruchomienie na nowym RPi

Jeśli stawiasz projekt od zera na nowym RPi:

```bash
# 1. Zainstaluj zależności systemu
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git ffmpeg nginx

# 2. Sklonuj projekt
cd ~
git clone https://github.com/twoj-repo/tamteklipy.git
cd tamteklipy

# 3. Przygotuj pendrive
sudo mkdir -p /mnt/tamteklipy
sudo mount /dev/sda1 /mnt/tamteklipy
sudo chown -R $USER:$USER /mnt/tamteklipy

# 4. Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Utwórz katalogi na pendrive
mkdir -p /mnt/tamteklipy/{clips,screenshots,thumbnails,metadata,award_icons}

# 6. Uruchom deployment
cd ~/tamteklipy
bash deploy.sh

# 7. Skonfiguruj systemd (jeśli jeszcze nie ma)
# (pliki .service powinny być w repo w katalogu systemd/)
sudo cp systemd/tamteklipy-backend.service /etc/systemd/system/
sudo cp systemd/tamteklipy-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tamteklipy-backend
sudo systemctl enable tamteklipy-frontend
sudo systemctl start tamteklipy-backend
sudo systemctl start tamteklipy-frontend
```

---

## 🔒 Bezpieczeństwo

### Sprawdź SECRET_KEY:

```bash
cd ~/tamteklipy/backend
grep SECRET_KEY .env

# Powinien być długi losowy string (64+ znaków)
# Jeśli widzisz "CHANGE_ME" lub "dev-secret-key" - to źle!
```

### Regeneruj SECRET_KEY:

```bash
cd ~/tamteklipy/backend

# Backup .env
cp .env .env.backup

# Wygeneruj nowy
NEW_SECRET=$(openssl rand -hex 32)
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env

# Restart backend
sudo systemctl restart tamteklipy-backend

# Uwaga: wszyscy użytkownicy będą musieli się zalogować ponownie!
```