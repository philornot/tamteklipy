#!/bin/bash
# TamteKlipy - Diagnostyka problemów z deploymentem
# Uruchom na RPi: bash diagnose.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo "╔════════════════════════════════════════╗"
echo "║  TamteKlipy Diagnostyka                ║"
echo "╚════════════════════════════════════════╝"
echo ""

# ============================================
# 1. Sprawdź serwisy systemd
# ============================================
log_info "[1/6] Sprawdzanie serwisów systemd..."
echo ""

check_service() {
    local service=$1
    if systemctl is-active --quiet $service; then
        log_success "$service: RUNNING"
        return 0
    else
        log_error "$service: NOT RUNNING"
        echo ""
        log_warning "Szczegóły:"
        sudo systemctl status $service --no-pager | tail -n 10
        echo ""
        return 1
    fi
}

BACKEND_OK=false
FRONTEND_OK=false
CLOUDFLARED_OK=false

if check_service tamteklipy-backend; then
    BACKEND_OK=true
fi

if check_service tamteklipy-frontend; then
    FRONTEND_OK=true
fi

if check_service cloudflared; then
    CLOUDFLARED_OK=true
fi

echo ""

# ============================================
# 2. Sprawdź porty
# ============================================
log_info "[2/6] Sprawdzanie portów..."
echo ""

if netstat -tuln | grep -q ":8000"; then
    log_success "Port 8000 (backend): LISTENING"
else
    log_error "Port 8000 (backend): NOT LISTENING"
fi

if netstat -tuln | grep -q ":3000"; then
    log_success "Port 3000 (frontend): LISTENING"
else
    log_warning "Port 3000 (frontend): NOT LISTENING (to OK jeśli backend serwuje frontend)"
fi

echo ""

# ============================================
# 3. Test lokalnego połączenia
# ============================================
log_info "[3/6] Testowanie lokalnego połączenia..."
echo ""

if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    log_success "Backend /health: OK"
    echo "Response:"
    curl -s http://localhost:8000/health | head -n 5
else
    log_error "Backend /health: FAILED"
    echo ""
    log_warning "Próbuję bezpośrednio..."
    curl -v http://localhost:8000/health 2>&1 | tail -n 20
fi

echo ""

if curl -s -f http://localhost:8000/ > /dev/null 2>&1; then
    log_success "Frontend root: OK"
else
    log_error "Frontend root: FAILED"
fi

echo ""

# ============================================
# 4. Sprawdź logi cloudflared
# ============================================
log_info "[4/6] Sprawdzanie logów cloudflared..."
echo ""

log_warning "Ostatnie 10 linii logów cloudflared:"
sudo journalctl -u cloudflared -n 10 --no-pager

echo ""

# ============================================
# 5. Sprawdź konfigurację cloudflared
# ============================================
log_info "[5/6] Sprawdzanie konfiguracji cloudflared..."
echo ""

CONFIG_FOUND=false

if [ -f ~/.cloudflared/config.yml ]; then
    log_success "Config znaleziony: ~/.cloudflared/config.yml"
    echo ""
    cat ~/.cloudflared/config.yml
    CONFIG_FOUND=true
elif [ -f /etc/cloudflared/config.yml ]; then
    log_success "Config znaleziony: /etc/cloudflared/config.yml"
    echo ""
    sudo cat /etc/cloudflared/config.yml
    CONFIG_FOUND=true
else
    log_error "Nie znaleziono config.yml cloudflared!"
fi

echo ""

# ============================================
# 6. Sprawdź bazy danych i pliki
# ============================================
log_info "[6/6] Sprawdzanie bazy danych i plików..."
echo ""

if [ -f ~/tamteklipy/backend/tamteklipy.db ]; then
    log_success "Baza danych istnieje"
    DB_SIZE=$(du -h ~/tamteklipy/backend/tamteklipy.db | cut -f1)
    echo "  Rozmiar: $DB_SIZE"
else
    log_error "Baza danych nie istnieje!"
fi

if [ -f ~/tamteklipy/backend/.env ]; then
    log_success "Backend .env istnieje"

    # Sprawdź SECRET_KEY
    if grep -q "CHANGE_ME\|dev-secret-key" ~/tamteklipy/backend/.env; then
        log_warning "SECRET_KEY wygląda na domyślny (niebezpieczny)!"
    else
        log_success "SECRET_KEY wygląda dobrze"
    fi
else
    log_error "Backend .env nie istnieje!"
fi

if [ -d ~/tamteklipy/frontend/dist ]; then
    log_success "Frontend dist/ istnieje"
    FILE_COUNT=$(ls ~/tamteklipy/frontend/dist | wc -l)
    echo "  Plików: $FILE_COUNT"
else
    log_error "Frontend dist/ nie istnieje lub jest pusty!"
fi

echo ""

# ============================================
# PODSUMOWANIE
# ============================================
echo "╔════════════════════════════════════════╗"
echo "║  PODSUMOWANIE                          ║"
echo "╚════════════════════════════════════════╝"
echo ""

ISSUES=0

if [ "$BACKEND_OK" = false ]; then
    log_error "Backend nie działa"
    echo "  FIX: sudo systemctl restart tamteklipy-backend"
    echo "  LOGI: sudo journalctl -u tamteklipy-backend -n 50"
    echo ""
    ISSUES=$((ISSUES + 1))
fi

if [ "$CLOUDFLARED_OK" = false ]; then
    log_error "Cloudflared nie działa"
    echo "  FIX: sudo systemctl restart cloudflared"
    echo "  LOGI: sudo journalctl -u cloudflared -n 50"
    echo ""
    ISSUES=$((ISSUES + 1))
fi

if ! curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    log_error "Backend nie odpowiada lokalnie"
    echo "  FIX: Sprawdź czy backend faktycznie startuje"
    echo "  TEST: cd ~/tamteklipy/backend && source venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo ""
    ISSUES=$((ISSUES + 1))
fi

if [ "$CONFIG_FOUND" = false ]; then
    log_error "Brak konfiguracji cloudflared"
    echo "  FIX: Utwórz ~/.cloudflared/config.yml"
    echo ""
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    log_success "Wszystko wygląda dobrze! 🎉"
    echo ""
    log_info "Jeśli nadal widzisz 502:"
    echo "  1. Sprawdź DNS w Cloudflare (czy wskazuje na tunel)"
    echo "  2. Sprawdź czy tunel jest aktywny w dashboard Cloudflare"
    echo "  3. Zrestartuj wszystko: sudo systemctl restart tamteklipy-backend cloudflared"
else
    log_warning "Znaleziono $ISSUES problemów - zobacz powyżej"
fi

echo ""
log_info "Quick commands:"
echo "  Backend logs:     sudo journalctl -u tamteklipy-backend -f"
echo "  Cloudflared logs: sudo journalctl -u cloudflared -f"
echo "  Restart all:      sudo systemctl restart tamteklipy-backend cloudflared"
echo "  Full redeploy:    cd ~/tamteklipy && bash deploy.sh"
echo ""