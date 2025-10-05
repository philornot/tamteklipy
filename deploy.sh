#!/bin/bash
# TamteKlipy - Jedyny skrypt deployment którego potrzebujesz
set -e

echo "╔═══════════════════════════════════════╗"
echo "║   TamteKlipy Deployment Script        ║"
echo "╚═══════════════════════════════════════╝"
echo ""

cd ~/tamteklipy

# ============================================
# 1. GIT PULL
# ============================================
echo "📦 [1/6] Pulling latest code..."
git pull
echo ""

# ============================================
# 2. BACKEND CONFIG CHECK
# ============================================
echo "⚙️  [2/6] Checking backend configuration..."
cd backend

if [ ! -f .env ]; then
    echo "❌ backend/.env NOT FOUND!"
    echo ""
    echo "Creating from template..."

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

    # Generuj SECRET_KEY automatycznie
    NEW_SECRET=$(openssl rand -hex 32)
    sed -i "s/CHANGE_ME_.*/$(echo $NEW_SECRET)/" .env

    echo "✅ .env created with auto-generated SECRET_KEY"
else
    # Sprawdź czy SECRET_KEY nie jest domyślny
    if grep -q "dev-secret-key\|CHANGE_ME\|TEMPORARY" .env; then
        echo "⚠️  WARNING: Using unsafe SECRET_KEY!"
        echo "Generating new one..."
        NEW_SECRET=$(openssl rand -hex 32)
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env
        echo "✅ SECRET_KEY updated"
    else
        echo "✅ .env exists and looks good"
    fi
fi
echo ""

# ============================================
# 3. BACKEND UPDATE
# ============================================
echo "🔧 [3/6] Updating backend..."
source venv/bin/activate
pip install -q -r requirements.txt

# Database check/init
if [ ! -f tamteklipy.db ]; then
    echo "📊 Creating database..."
    python -c "from app.core.init_db import init_db; init_db()"

    echo ""
    echo "👤 No users found. Creating admin user..."
    python seed_database.py --clear
    echo ""
    echo "✅ Admin created: philornot / HasloFilipa"
else
    # Check if users exist
    USER_COUNT=$(python -c "from app.core.database import SessionLocal; from app.models.user import User; db = SessionLocal(); count = db.query(User).count(); db.close(); print(count)" 2>/dev/null || echo "0")

    if [ "$USER_COUNT" -eq "0" ]; then
        echo "👤 Database exists but empty. Creating admin..."
        python seed_database.py --clear
        echo "✅ Admin created: philornot / HasloFilipa"
    else
        echo "✅ Database OK ($USER_COUNT users)"
    fi
fi

sudo systemctl restart tamteklipy-backend
echo "✅ Backend restarted"
echo ""

# ============================================
# 4. FRONTEND CONFIG CHECK
# ============================================
echo "🎨 [4/6] Checking frontend configuration..."
cd ../frontend

if [ ! -f .env.production ]; then
    echo "Creating frontend/.env.production..."
    echo "VITE_API_URL=https://www.tamteklipy.pl" > .env.production
    echo "✅ .env.production created"
else
    echo "✅ .env.production exists"
fi
echo ""

# ============================================
# 5. FRONTEND BUILD
# ============================================
echo "🏗️  [5/6] Building frontend..."
npm install --silent
npm run build
echo "✅ Frontend built"
echo ""

# ============================================
# 6. HEALTH CHECK
# ============================================
echo "🏥 [6/6] Running health check..."
cd ..

sleep 2  # Give backend time to start

# Check if backend is responding
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is responding"
else
    echo "⚠️  Backend not responding yet (might need a moment)"
fi

# Check if frontend dist exists
if [ -d "frontend/dist" ] && [ "$(ls -A frontend/dist)" ]; then
    echo "✅ Frontend dist exists"
else
    echo "❌ Frontend dist is empty!"
fi

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║   Deployment Complete! 🚀             ║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "📍 Your app: https://www.tamteklipy.pl"
echo "📍 Health check: https://www.tamteklipy.pl/health"
echo ""
echo "🔐 Default login: philornot / HasloFilipa"
echo ""
echo "📋 Useful commands:"
echo "   sudo systemctl status tamteklipy-backend"
echo "   tail -f backend/logs/tamteklipy.log"
echo ""