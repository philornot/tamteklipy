#!/bin/bash
# TamteKlipy - Uniwersalny Skrypt Deployment (Windows Git Bash + RPi)
# Version: 2.0
set -e

# Kolory dla outputu
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funkcje pomocnicze
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Wykryj środowisko - ulepszona detekcja dla PowerShell i Git Bash
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ -n "$WINDIR" ]] || [[ "$PWD" == *"Users"*"Windows"* ]] || [[ "$PWD" == *"C:"* ]] || [[ "$PWD" == "/c/"* ]] || [[ "$PWD" == "/mnt/c/"* ]]; then
    ENV="windows"
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    ENV="rpi"
    PROJECT_DIR=~/tamteklipy
fi

# Parsuj argumenty
DEPLOY_BACKEND=true
DEPLOY_FRONTEND=true
SKIP_LOCAL_COMMIT=false
DRY_RUN=false
SKIP_BACKUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--backend|--backend-only)
            DEPLOY_FRONTEND=false
            shift
            ;;
        -f|--frontend|--frontend-only)
            DEPLOY_BACKEND=false
            shift
            ;;
        -p|--pull-only)
            SKIP_LOCAL_COMMIT=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --no-backup)
            SKIP_BACKUP=true
            shift
            ;;
        -h|--help)
            echo "Użycie: $0 [OPCJE]"
            echo ""
            echo "Opcje:"
            echo "  (brak)           Pełny deployment (backend + frontend)"
            echo "  -b, --backend    Tylko backend"
            echo "  -f, --frontend   Tylko frontend"
            echo "  -p, --pull-only  Tylko pull na RPi (bez lokalnych commitów)"
            echo "  --dry-run        Pokaż co zostanie wykonane (bez zmian)"
            echo "  --no-backup      Pomiń backup bazy danych"
            echo "  -h, --help       Pokaż tę pomoc"
            exit 0
            ;;
        *)
            log_error "Nieznana opcja: $1"
            echo "Użyj '$0 --help' aby zobaczyć dostępne opcje"
            exit 1
            ;;
    esac
done

echo "╔═══════════════════════════════════════╗"
echo "║   TamteKlipy Deployment Script v2.0   ║"
echo "╚═══════════════════════════════════════╝"
echo ""
log_info "Środowisko: $ENV"

if [ "$DRY_RUN" = true ]; then
    log_warning "Tryb DRY RUN - żadne zmiany nie zostaną wykonane"
fi

if [ "$DEPLOY_BACKEND" = true ] && [ "$DEPLOY_FRONTEND" = true ]; then
    log_info "Tryb: Pełny deployment (backend + frontend)"
elif [ "$DEPLOY_BACKEND" = true ]; then
    log_info "Tryb: Tylko backend"
elif [ "$DEPLOY_FRONTEND" = true ]; then
    log_info "Tryb: Tylko frontend"
fi
echo ""

cd "$PROJECT_DIR"

# ============================================
# DEPLOYMENT NA WINDOWS
# ============================================
if [ "$ENV" = "windows" ]; then
    if [ "$SKIP_LOCAL_COMMIT" = true ]; then
        log_info "[1/4] Pomijanie lokalnego commita (tryb pull-only)..."
        echo ""
    else
        log_info "[1/4] Commitowanie i pushowanie zmian..."

        # Sprawdź czy są zmiany do commitowania
        if [[ -n $(git status -s) ]]; then
            if [ "$DRY_RUN" = true ]; then
                log_info "DRY RUN: Znaleziono zmiany, zostałyby zacommitowane"
                git status -s
            else
                read -p "💬 Wiadomość commita: " commit_msg
                git add .
                git commit -m "$commit_msg"
                git push
                log_success "Zmiany wypchnięte na GitHub"
            fi
        else
            log_info "Brak zmian do commitowania"
            if [ "$DRY_RUN" = false ]; then
                git push
            fi
        fi
        echo ""
    fi

    # Build i przesłanie frontendu
    if [ "$DEPLOY_FRONTEND" = true ]; then
        log_info "[2/4] Budowanie frontendu..."
        cd frontend

        if [ "$DRY_RUN" = true ]; then
            log_info "DRY RUN: Frontend zostałby zbudowany"
        else
            # Sprawdź czy pnpm jest dostępny
            if command -v pnpm &> /dev/null; then
                pnpm install
                pnpm run build
            else
                npm install
                npm run build
            fi

            # Weryfikuj czy build się powiódł
            if [ ! -d "dist" ] || [ -z "$(ls -A dist 2>/dev/null)" ]; then
                log_error "Frontend build failed - dist/ jest pusty!"
                exit 1
            fi

            log_success "Frontend zbudowany"
        fi
        echo ""

        log_info "[3/4] Przesyłanie frontendu na RPi..."

        if [ "$DRY_RUN" = true ]; then
            log_info "DRY RUN: Frontend zostałby przesłany przez SCP"
        else
            # Sprawdź połączenie SSH
            if ! ssh -o ConnectTimeout=5 frpi "echo 'Connection OK'" &> /dev/null; then
                log_error "Nie można połączyć się z RPi przez SSH!"
                log_warning "Sprawdź czy:"
                echo "  - RPi jest włączony"
                echo "  - SSH działa (ssh frpi)"
                echo "  - Klucz SSH jest skonfigurowany"
                exit 1
            fi

            # Utwórz katalog dist na RPi jeśli nie istnieje
            ssh frpi "mkdir -p ~/tamteklipy/frontend/dist"

            # Prześlij zawartość dist
            scp -r dist/* frpi:~/tamteklipy/frontend/dist/

            log_success "Frontend przesłany"
        fi
        echo ""

        cd ..
    else
        log_warning "[2/4] Pomijanie budowania frontendu..."
        log_warning "[3/4] Pomijanie przesyłania frontendu..."
        echo ""
    fi

    # Deployment na RPi
    log_info "[4/4] Uruchamianie deploymentu na RPi..."

    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Deployment na RPi zostałby uruchomiony z flagami:"
        if [ "$DEPLOY_BACKEND" = true ] && [ "$DEPLOY_FRONTEND" = true ]; then
            echo "  bash deploy.sh"
        elif [ "$DEPLOY_BACKEND" = true ]; then
            echo "  bash deploy.sh -b"
        elif [ "$DEPLOY_FRONTEND" = true ]; then
            echo "  bash deploy.sh -f"
        fi
    else
        if [ "$DEPLOY_BACKEND" = true ] && [ "$DEPLOY_FRONTEND" = true ]; then
            ssh frpi "cd ~/tamteklipy && bash deploy.sh"
        elif [ "$DEPLOY_BACKEND" = true ]; then
            ssh frpi "cd ~/tamteklipy && bash deploy.sh -b"
        elif [ "$DEPLOY_FRONTEND" = true ]; then
            ssh frpi "cd ~/tamteklipy && bash deploy.sh -f"
        fi
    fi

    echo ""
    echo "╔═══════════════════════════════════════╗"
    echo "║   Deployment Zakończony! 🚀           ║"
    echo "╚═══════════════════════════════════════╝"
    echo ""
    log_success "Twoja aplikacja: https://www.tamteklipy.pl"
    echo ""

# ============================================
# DEPLOYMENT NA RPI
# ============================================
else
    # Safety checks przed deploymentem
    log_info "Sprawdzanie wymagań..."

    # Check 1: Sprawdź czy pendrive jest zamontowany
    if [ ! -d "/mnt/tamteklipy" ]; then
        log_error "Pendrive nie jest zamontowany w /mnt/tamteklipy!"
        log_warning "Uruchom: sudo mount /dev/sda1 /mnt/tamteklipy"
        exit 1
    fi

    # Check 2: Sprawdź czy jest miejsce na dysku
    AVAILABLE_MB=$(df /mnt/tamteklipy | tail -1 | awk '{print int($4/1024)}')
    if [ "$AVAILABLE_MB" -lt 1000 ]; then
        log_warning "Mało miejsca na pendrive: ${AVAILABLE_MB}MB"
        log_warning "Zalecane minimum: 1000MB"
    else
        log_success "Dostępne miejsce: ${AVAILABLE_MB}MB"
    fi

    # Check 3: Backup bazy danych (opcjonalny)
    if [ "$SKIP_BACKUP" = false ] && [ -f "backend/tamteklipy.db" ]; then
        log_info "Tworzenie backupu bazy danych..."

        if [ "$DRY_RUN" = true ]; then
            log_info "DRY RUN: Backup zostałby utworzony"
        else
            mkdir -p backend/backups
            BACKUP_FILE="backend/backups/tamteklipy_$(date +%Y%m%d_%H%M%S).db"
            cp backend/tamteklipy.db "$BACKUP_FILE"
            log_success "Backup: $BACKUP_FILE"

            # Usuń backupy starsze niż 7 dni
            find backend/backups -name "*.db" -type f -mtime +7 -delete 2>/dev/null || true
        fi
    fi

    echo ""

    # Git pull - zawsze, niezależnie od trybu
    log_info "[1/6] Pobieranie najnowszego kodu..."

    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: git pull zostałby wykonany"
        git fetch --dry-run
    else
        # Sprawdź czy są zmiany do pobrania
        git fetch
        LOCAL=$(git rev-parse @)
        REMOTE=$(git rev-parse @{u})

        if [ "$LOCAL" = "$REMOTE" ]; then
            log_info "Kod jest aktualny (brak zmian)"
        else
            git pull
            log_success "Kod zaktualizowany"
        fi
    fi
    echo ""

    # Deployment backendu
    if [ "$DEPLOY_BACKEND" = true ]; then
        log_info "[2/6] Sprawdzanie konfiguracji backendu..."
        cd backend

        if [ "$DRY_RUN" = true ]; then
            log_info "DRY RUN: Sprawdzanie .env, instalacja pakietów, restart serwisu"
            cd ..
        else
            if [ ! -f .env ]; then
                log_warning "backend/.env NIE ZNALEZIONY!"
                echo ""
                log_info "Tworzenie z szablonu..."

                cat > .env << 'EOF'
ENVIRONMENT=production
DATABASE_URL=sqlite:///./tamteklipy.db
SECRET_KEY=CHANGE_ME_$(openssl rand -hex 16)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
STORAGE_PATH=/mnt/tamteklipy
CLIPS_PATH=/mnt/tamteklipy/clips
SCREENSHOTS_PATH=/mnt/tamteklipy/screenshots
THUMBNAILS_PATH=/mnt/tamteklipy/thumbnails
METADATA_PATH=/mnt/tamteklipy/metadata
AWARD_ICONS_PATH=/mnt/tamteklipy/award_icons
ALLOWED_ORIGINS=https://www.tamteklipy.pl,https://tamteklipy.pl
MAX_VIDEO_SIZE_MB=500
MAX_IMAGE_SIZE_MB=10
EOF

                # Wygeneruj SECRET_KEY automatycznie
                NEW_SECRET=$(openssl rand -hex 32)
                sed -i "s/CHANGE_ME_.*/$(echo $NEW_SECRET)/" .env

                log_success ".env utworzony z automatycznie wygenerowanym SECRET_KEY"
            else
                # Sprawdź czy SECRET_KEY nie jest domyślny
                if grep -q "dev-secret-key\|CHANGE_ME\|TEMPORARY" .env; then
                    log_warning "OSTRZEŻENIE: Używany jest niebezpieczny SECRET_KEY!"
                    log_info "Generowanie nowego..."
                    NEW_SECRET=$(openssl rand -hex 32)
                    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env
                    log_success "SECRET_KEY zaktualizowany"
                else
                    log_success ".env istnieje i wygląda dobrze"
                fi
            fi
            echo ""

            log_info "[3/6] Aktualizacja backendu..."
            source venv/bin/activate
            pip install -q -r requirements.txt

            # Sprawdzenie/inicjalizacja bazy danych
            if [ ! -f tamteklipy.db ]; then
                log_info "Tworzenie bazy danych..."
                python -c "from app.core.init_db import init_db; init_db()"

                echo ""
                log_info "Nie znaleziono użytkowników. Tworzenie admina..."
                python seed_database.py --clear
                echo ""
                log_success "Admin utworzony: philornot / HasloFilipa"
            else
                # Sprawdź czy są jacyś użytkownicy
                USER_COUNT=$(python -c "from app.core.database import SessionLocal; from app.models.user import User; db = SessionLocal(); count = db.query(User).count(); db.close(); print(count)" 2>/dev/null || echo "0")

                if [ "$USER_COUNT" -eq "0" ]; then
                    log_info "Baza istnieje ale jest pusta. Tworzenie admina..."
                    python seed_database.py --clear
                    log_success "Admin utworzony: philornot / HasloFilipa"
                else
                    log_success "Baza OK ($USER_COUNT użytkowników)"
                fi
            fi

            # === SETUP SYSTEMD SERVICES (jeśli nie istnieją) ===
            if ! systemctl list-unit-files | grep -q tamteklipy-backend.service; then
                log_info "Tworzenie serwisu tamteklipy-backend..."

                sudo tee /etc/systemd/system/tamteklipy-backend.service > /dev/null <<EOF
[Unit]
Description=TamteKlipy Backend API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/tamteklipy/backend
Environment="PATH=$HOME/tamteklipy/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$HOME/tamteklipy/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

                sudo systemctl daemon-reload
                sudo systemctl enable tamteklipy-backend
                log_success "Serwis backend utworzony i włączony"
            fi

            if ! systemctl list-unit-files | grep -q tamteklipy-frontend.service; then
                log_info "Tworzenie serwisu tamteklipy-frontend..."

                sudo tee /etc/systemd/system/tamteklipy-frontend.service > /dev/null <<EOF
[Unit]
Description=TamteKlipy Frontend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/tamteklipy/frontend
ExecStart=/usr/bin/python3 -m http.server 3000 --directory dist
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

                sudo systemctl daemon-reload
                sudo systemctl enable tamteklipy-frontend
                log_success "Serwis frontend utworzony i włączony"
            fi
            # === END SYSTEMD SETUP ===

            # Restart serwisu
            log_info "Restartowanie backendu..."

            # Restart serwisu
            log_info "Restartowanie backendu..."
            if sudo systemctl restart tamteklipy-backend; then
                log_success "Backend zrestartowany"

                # Sprawdź czy startuje poprawnie
                sleep 2
                if systemctl is-active --quiet tamteklipy-backend; then
                    log_success "Backend działa poprawnie"
                else
                    log_error "Backend nie uruchomił się poprawnie!"
                    log_warning "Sprawdź logi: sudo journalctl -u tamteklipy-backend -n 50"
                fi
            else
                log_error "Nie udało się zrestartować backendu!"
                exit 1
            fi
            echo ""

            cd ..
        fi
    else
        log_warning "[2/6] Pomijanie konfiguracji backendu..."
        log_warning "[3/6] Pomijanie aktualizacji backendu..."
        echo ""
    fi

    # Deployment frontendu
    if [ "$DEPLOY_FRONTEND" = true ]; then
        log_info "[4/6] Sprawdzanie konfiguracji frontendu..."
        cd frontend

        if [ "$DRY_RUN" = true ]; then
            log_info "DRY RUN: Sprawdzanie .env.production i dist/"
            cd ..
        else
            if [ ! -f .env.production ]; then
                log_info "Tworzenie frontend/.env.production..."
                echo "VITE_API_URL=https://www.tamteklipy.pl" > .env.production
                log_success ".env.production utworzony"
            else
                log_success ".env.production istnieje"
            fi

            # Sprawdź czy dist istnieje (powinien być przesłany z Windows)
            if [ ! -d "dist" ] || [ -z "$(ls -A dist 2>/dev/null)" ]; then
                log_error "OSTRZEŻENIE: dist/ jest pusty lub nie istnieje!"
                log_warning "Frontend powinien być zbudowany na Windows i przesłany przez SCP"
            else
                log_success "dist/ istnieje i zawiera pliki"
            fi
            echo ""

            cd ..
        fi
    else
        log_warning "[4/6] Pomijanie konfiguracji frontendu..."
        echo ""
    fi

    # Restart serwisu frontendu
    if [ "$DEPLOY_FRONTEND" = true ]; then
        log_info "[5/6] Restartowanie serwisu frontendu..."

        if [ "$DRY_RUN" = true ]; then
            log_info "DRY RUN: Serwis frontendu zostałby zrestartowany"
        else
            if sudo systemctl restart tamteklipy-frontend; then
                log_success "Frontend zrestartowany"

                # Sprawdź czy startuje poprawnie
                sleep 1
                if systemctl is-active --quiet tamteklipy-frontend; then
                    log_success "Frontend działa poprawnie"
                else
                    log_error "Frontend nie uruchomił się poprawnie!"
                    log_warning "Sprawdź logi: sudo journalctl -u tamteklipy-frontend -n 50"
                fi
            else
                log_error "Nie udało się zrestartować frontendu!"
            fi
        fi
        echo ""
    else
        log_warning "[5/6] Pomijanie restartu frontendu..."
        echo ""
    fi

    # Sprawdzenie zdrowia systemu
    log_info "[6/6] Sprawdzanie zdrowia systemu..."

    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Health check zostałby wykonany"
    else
        sleep 2  # Daj serwisom czas na start

        if [ "$DEPLOY_BACKEND" = true ]; then
            if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                log_success "Backend odpowiada na /health"
            else
                log_warning "Backend jeszcze nie odpowiada (może potrzebować chwili)"
            fi
        fi

        if [ "$DEPLOY_FRONTEND" = true ]; then
            if [ -d "frontend/dist" ] && [ "$(ls -A frontend/dist)" ]; then
                log_success "Frontend dist istnieje"
            else
                log_error "Frontend dist jest pusty!"
            fi
        fi
    fi

    echo ""
    echo "╔═══════════════════════════════════════╗"
    echo "║   Deployment Zakończony! 🚀           ║"
    echo "╚═══════════════════════════════════════╝"
    echo ""
    log_success "Twoja aplikacja: https://www.tamteklipy.pl"
    log_info "Health check: https://www.tamteklipy.pl/health"
    echo ""
    log_info "Domyślne logowanie: philornot / HasloFilipa"
    echo ""
    log_info "Przydatne komendy:"
    echo "   sudo systemctl status tamteklipy-backend"
    echo "   sudo systemctl status tamteklipy-frontend"
    echo "   tail -f backend/logs/tamteklipy.log"
    echo ""
fi