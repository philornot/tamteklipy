#!/bin/bash
set -e

echo "=== Pulling latest code ==="
cd ~/tamteklipy
git pull

echo "=== Updating backend ==="
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Tylko jeśli baza nie istnieje
if [ ! -f tamteklipy.db ]; then
    echo "Creating database..."
    alembic upgrade head
else
    echo "Database exists, skipping migration (run manually if needed)"
fi

sudo systemctl restart tamteklipy-backend

echo "=== Building frontend ==="
cd ../frontend
pnpm install
NODE_OPTIONS="--max-old-space-size=512" pnpm run build

echo "=== Deployment complete ==="
sudo systemctl status tamteklipy-backend
