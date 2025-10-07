#!/bin/bash
# TamteKlipy - Uniwersalny Skrypt Deployment (Windows Git Bash + RPi)
set -e

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
        -h|--help)
            echo "Użycie: $0 [OPCJE]"
            echo ""
            echo "Opcje:"
            echo "  (brak)           Pełny deployment (backend + frontend)"
            echo "  -b, --backend    Tylko backend"
            echo "  -f, --frontend   Tylko frontend"
            echo "  -p, --pull-only  Tylko pull na RPi (bez lokalnych commitów)"
            echo "  -h, --help       Pokaż tę pomoc"
            exit 0
            ;;
        *)
            echo "Nieznana opcja: $1"
            echo "Użyj '$0 --help' aby zobaczyć dostępne opcje"
            exit 1
            ;;
    esac
done

echo "╔═══════════════════════════════════════╗"
echo "║   TamteKlipy Deployment Script        ║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "🖥️  Środowisko: $ENV"

if [ "$DEPLOY_BACKEND" = true ] && [ "$DEPLOY_FRONTEND" = true ]; then
    echo "🚀 Tryb: Pełny deployment (backend + frontend)"
elif [ "$DEPLOY_BACKEND" = true ]; then
    echo "🔧 Tryb: Tylko backend"
elif [ "$DEPLOY_FRONTEND" = true ]; then
    echo "🎨 Tryb: Tylko frontend"
fi
echo ""

cd "$PROJECT_DIR"

# ============================================
# DEPLOYMENT NA WINDOWS
# ============================================
if [ "$ENV" = "windows" ]; then
    if [ "$SKIP_LOCAL_COMMIT" = true ]; then
        echo "⏭️  [1/4] Pomijanie lokalnego commita (tryb pull-only)..."
        echo ""
    else
        echo "📦 [1/4] Commitowanie i pushowanie zmian..."

        # Sprawdź czy są zmiany do commitowania
        if [[ -n $(git status -s) ]]; then
            read -p "💬 Wiadomość commita: " commit_msg
            git add .
            git commit -m "$commit_msg"
            git push
            echo "✅ Zmiany wypchnięte na GitHub"
        else
            echo "ℹ️  Brak zmian do commitowania"
            git push
        fi
        echo ""
    fi

    # Build i przesłanie frontendu
    if [ "$DEPLOY_FRONTEND" = true ]; then
        echo "🏗️  [2/4] Budowanie frontendu..."
        cd frontend

        # Sprawdź czy pnpm jest dostępny
        if command -v pnpm &> /dev/null; then
            pnpm install
            pnpm run build
        else
            npm install
            npm run build
        fi

        echo "✅ Frontend zbudowany"
        echo ""

        echo "📤 [3/4] Przesyłanie frontendu na RPi..."

        # Utwórz katalog dist na RPi jeśli nie istnieje
        ssh frpi "mkdir -p ~/tamteklipy/frontend/dist"

        # Prześlij zawartość dist
        scp -r dist/* frpi:~/tamteklipy/frontend/dist/

        echo "✅ Frontend przesłany"
        echo ""

        cd ..
    else
        echo "⏭️  [2/4] Pomijanie budowania frontendu..."
        echo "⏭️  [3/4] Pomijanie przesyłania frontendu..."
        echo ""
    fi

    # Deployment na RPi
    echo "🚀 [4/4] Uruchamianie deploymentu na RPi..."

    if [ "$DEPLOY_BACKEND" = true ] && [ "$DEPLOY_FRONTEND" = true ]; then
        ssh frpi "cd ~/tamteklipy && bash deploy.sh"
    elif [ "$DEPLOY_BACKEND" = true ]; then
        ssh frpi "cd ~/tamteklipy && bash deploy.sh -b"
    elif [ "$DEPLOY_FRONTEND" = true ]; then
        ssh frpi "cd ~/tamteklipy && bash deploy.sh -f"
    fi

    echo ""
    echo "╔═══════════════════════════════════════╗"
    echo "║   Deployment Zakończony! 🚀           ║"
    echo "╚═══════════════════════════════════════╝"
    echo ""
    echo "📍 Twoja aplikacja: https://www.tamteklipy.pl"
    echo ""

# ============================================
# DEPLOYMENT NA RPI
# ============================================
else
    # Git pull - zawsze, niezależnie od trybu
    echo "📦 [1/6] Pobieranie najnowszego kodu..."
    git pull
    echo ""

    # Deployment backendu
    if [ "$DEPLOY_BACKEND" = true ]; then
        echo "⚙️  [2/6] Sprawdzanie konfiguracji backendu..."
        cd backend

        if [ ! -f .env ]; then
            echo "❌ backend/.env NIE ZNALEZIONY!"
            echo ""
            echo "Tworzenie z szablonu..."

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

            echo "✅ .env utworzony z automatycznie wygenerowanym SECRET_KEY"
        else
            # Sprawdź czy SECRET_KEY nie jest domyślny
            if grep -q "dev-secret-key\|CHANGE_ME\|TEMPORARY" .env; then
                echo "⚠️  OSTRZEŻENIE: Używany jest niebezpieczny SECRET_KEY!"
                echo "Generowanie nowego..."
                NEW_SECRET=$(openssl rand -hex 32)
                sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env
                echo "✅ SECRET_KEY zaktualizowany"
            else
                echo "✅ .env istnieje i wygląda dobrze"
            fi
        fi
        echo ""

        echo "🔧 [3/6] Aktualizacja backendu..."
        source venv/bin/activate
        pip install -q -r requirements.txt

        # Sprawdzenie/inicjalizacja bazy danych
        if [ ! -f tamteklipy.db ]; then
            echo "📊 Tworzenie bazy danych..."
            python -c "from app.core.init_db import init_db; init_db()"

            echo ""
            echo "👤 Nie znaleziono użytkowników. Tworzenie admina..."
            python seed_database.py --clear
            echo ""
            echo "✅ Admin utworzony: philornot / HasloFilipa"
        else
            # Sprawdź czy są jacyś użytkownicy
            USER_COUNT=$(python -c "from app.core.database import SessionLocal; from app.models.user import User; db = SessionLocal(); count = db.query(User).count(); db.close(); print(count)" 2>/dev/null || echo "0")

            if [ "$USER_COUNT" -eq "0" ]; then
                echo "👤 Baza istnieje ale jest pusta. Tworzenie admina..."
                python seed_database.py --clear
                echo "✅ Admin utworzony: philornot / HasloFilipa"
            else
                echo "✅ Baza OK ($USER_COUNT użytkowników)"
            fi
        fi

        sudo systemctl restart tamteklipy-backend
        echo "✅ Backend zrestartowany"
        echo ""

        cd ..
    else
        echo "⏭️  [2/6] Pomijanie konfiguracji backendu..."
        echo "⏭️  [3/6] Pomijanie aktualizacji backendu..."
        echo ""
    fi

    # Deployment frontendu
    if [ "$DEPLOY_FRONTEND" = true ]; then
        echo "🎨 [4/6] Sprawdzanie konfiguracji frontendu..."
        cd frontend

        if [ ! -f .env.production ]; then
            echo "Tworzenie frontend/.env.production..."
            echo "VITE_API_URL=https://www.tamteklipy.pl" > .env.production
            echo "✅ .env.production utworzony"
        else
            echo "✅ .env.production istnieje"
        fi

        # Sprawdź czy dist istnieje (powinien być przesłany z Windows)
        if [ ! -d "dist" ] || [ -z "$(ls -A dist 2>/dev/null)" ]; then
            echo "⚠️  OSTRZEŻENIE: dist/ jest pusty lub nie istnieje!"
            echo "   Frontend powinien być zbudowany na Windows i przesłany przez SCP"
        else
            echo "✅ dist/ istnieje i zawiera pliki"
        fi
        echo ""

        cd ..
    else
        echo "⏭️  [4/6] Pomijanie konfiguracji frontendu..."
        echo ""
    fi

    # Restart serwisu frontendu
    if [ "$DEPLOY_FRONTEND" = true ]; then
        echo "🔄 [5/6] Restartowanie serwisu frontendu..."
        sudo systemctl restart tamteklipy-frontend
        echo "✅ Frontend zrestartowany"
        echo ""
    else
        echo "⏭️  [5/6] Pomijanie restartu frontendu..."
        echo ""
    fi

    # Sprawdzenie zdrowia systemu
    echo "🏥 [6/6] Sprawdzanie zdrowia systemu..."

    sleep 2  # Daj serwisom czas na start

    if [ "$DEPLOY_BACKEND" = true ]; then
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ Backend odpowiada"
        else
            echo "⚠️  Backend jeszcze nie odpowiada (może potrzebować chwili)"
        fi
    fi

    if [ "$DEPLOY_FRONTEND" = true ]; then
        if [ -d "frontend/dist" ] && [ "$(ls -A frontend/dist)" ]; then
            echo "✅ Frontend dist istnieje"
        else
            echo "❌ Frontend dist jest pusty!"
        fi
    fi

    echo ""
    echo "╔═══════════════════════════════════════╗"
    echo "║   Deployment Zakończony! 🚀           ║"
    echo "╚═══════════════════════════════════════╝"
    echo ""
    echo "📍 Twoja aplikacja: https://www.tamteklipy.pl"
    echo "📍 Health check: https://www.tamteklipy.pl/health"
    echo ""
    echo "🔐 Domyślne logowanie: philornot / HasloFilipa"
    echo ""
    echo "📋 Przydatne komendy:"
    echo "   sudo systemctl status tamteklipy-backend"
    echo "   sudo systemctl status tamteklipy-frontend"
    echo "   tail -f backend/logs/tamteklipy.log"
    echo ""
fi