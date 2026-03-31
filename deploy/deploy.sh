#!/bin/bash
# =============================================================
# AutoCut Video - Deployment Script
# Deploys from local machine to Alibaba Cloud server
# =============================================================
set -e

# --- Configuration ---
SERVER_IP="120.26.41.46"
SSH_KEY="~/.ssh/Evan_mac_air_openclaw.pem"
SSH_USER="root"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=15"
DEPLOY_DIR="/www/wwwroot/autocut-video"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Expand SSH key path
SSH_KEY=$(eval echo "$SSH_KEY")

ssh_cmd() {
    ssh $SSH_OPTS -i "$SSH_KEY" "${SSH_USER}@${SERVER_IP}" "$@"
}

scp_cmd() {
    scp $SSH_OPTS -i "$SSH_KEY" "$@"
}

rsync_cmd() {
    rsync -avz -e "ssh $SSH_OPTS -i $SSH_KEY" "$@"
}

echo "======================================"
echo "  AutoCut Video Deployment"
echo "  Server: ${SERVER_IP}"
echo "  Deploy: ${DEPLOY_DIR}"
echo "======================================"
echo ""

# --- Step 1: Build Frontend ---
echo "[1/6] Building frontend..."
cd "$PROJECT_ROOT/frontend"
npm run build
echo "  Frontend build complete."
echo ""

# --- Step 2: Create deploy directory on server ---
echo "[2/6] Preparing server directories..."
ssh_cmd "mkdir -p ${DEPLOY_DIR}/{backend,frontend/.next,logs,backend/uploads}"
echo "  Directories ready."
echo ""

# --- Step 3: Deploy Backend ---
echo "[3/6] Deploying backend..."
rsync_cmd \
    --delete \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='uploads/' \
    --exclude='autocut.db' \
    --exclude='.env' \
    --exclude='alembic/versions/__pycache__' \
    "$PROJECT_ROOT/backend/" "${SSH_USER}@${SERVER_IP}:${DEPLOY_DIR}/backend/"

# Deploy production .env only if one does not already exist on server
scp_cmd "$PROJECT_ROOT/deploy/.env.production" "${SSH_USER}@${SERVER_IP}:${DEPLOY_DIR}/backend/.env.tmp"
ssh_cmd "test -f ${DEPLOY_DIR}/backend/.env || mv ${DEPLOY_DIR}/backend/.env.tmp ${DEPLOY_DIR}/backend/.env; rm -f ${DEPLOY_DIR}/backend/.env.tmp"
echo "  Backend deployed."
echo ""

# --- Step 4: Deploy Frontend (standalone build) ---
echo "[4/6] Deploying frontend..."

# The standalone output lives in .next/standalone/
# We need to sync: standalone server + static assets + public assets
rsync_cmd \
    --delete \
    "$PROJECT_ROOT/frontend/.next/standalone/" "${SSH_USER}@${SERVER_IP}:${DEPLOY_DIR}/frontend/.next/standalone/"

# Static assets must be at .next/static/ relative to the standalone server
rsync_cmd \
    --delete \
    "$PROJECT_ROOT/frontend/.next/static/" "${SSH_USER}@${SERVER_IP}:${DEPLOY_DIR}/frontend/.next/static/"

# Public assets (if any) go to frontend/public/
if [ -d "$PROJECT_ROOT/frontend/public" ]; then
    rsync_cmd \
        --delete \
        "$PROJECT_ROOT/frontend/public/" "${SSH_USER}@${SERVER_IP}:${DEPLOY_DIR}/frontend/public/"
fi

# Copy next.config for reference
scp_cmd "$PROJECT_ROOT/frontend/next.config.mjs" "${SSH_USER}@${SERVER_IP}:${DEPLOY_DIR}/frontend/next.config.mjs"

echo "  Frontend deployed."
echo ""

# --- Step 5: Install deps, configure nginx, start services ---
echo "[5/6] Setting up server..."

# Deploy PM2 ecosystem config
scp_cmd "$PROJECT_ROOT/deploy/ecosystem.config.js" "${SSH_USER}@${SERVER_IP}:${DEPLOY_DIR}/ecosystem.config.js"

# Deploy nginx config
scp_cmd "$PROJECT_ROOT/deploy/nginx-autocut.conf" "${SSH_USER}@${SERVER_IP}:/etc/nginx/conf.d/autocut.conf"

ssh_cmd bash << 'REMOTE_SCRIPT'
set -e
DEPLOY_DIR="/www/wwwroot/autocut-video"

echo "  --- Python setup ---"
# Determine best Python binary (>= 3.8)
PYTHON_BIN=""
for py in python3.12 python3.11 python3.10 python3.9; do
    if command -v $py &>/dev/null; then
        PYTHON_BIN=$py
        break
    fi
done
# Fallback: check if system python3 is >= 3.8
if [ -z "$PYTHON_BIN" ]; then
    PY_VER=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
    PY_MINOR=$(echo $PY_VER | cut -d. -f2)
    if [ "$PY_MINOR" -ge 8 ] 2>/dev/null; then
        PYTHON_BIN=python3
    fi
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "  ERROR: Python 3.8+ not found. Installing python39..."
    yum install -y python39 python39-pip 2>/dev/null || true
    PYTHON_BIN=python3.9
    if ! command -v python3.9 &>/dev/null; then
        echo "  FATAL: Could not install Python 3.9. Aborting."
        exit 1
    fi
fi
echo "  Using: $PYTHON_BIN ($($PYTHON_BIN --version 2>&1))"

# Create venv and install deps
cd $DEPLOY_DIR/backend
if [ ! -d venv ]; then
    $PYTHON_BIN -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip 2>&1 | tail -1
pip install -r requirements.txt 2>&1 | tail -3
deactivate
echo "  Python deps installed."

echo ""
echo "  --- Frontend standalone setup ---"
cd $DEPLOY_DIR/frontend
# The standalone build already includes node_modules; just verify server.js exists
if [ -f ".next/standalone/server.js" ]; then
    echo "  Standalone server.js found."
else
    echo "  WARNING: .next/standalone/server.js not found!"
fi

# Symlink static and public into standalone dir for the server to find
# Next.js standalone expects static at .next/static relative to its own location
STANDALONE_DIR=".next/standalone"
# Static files -- Next standalone looks for .next/static relative to cwd
# We set cwd to frontend/ in PM2, so .next/static is already correct
echo "  Frontend ready."

echo ""
echo "  --- Nginx ---"
nginx -t 2>&1
systemctl reload nginx
echo "  Nginx reloaded."

echo ""
echo "  --- PM2 ---"
cd $DEPLOY_DIR
# Install PM2 if not present
if ! command -v pm2 &>/dev/null; then
    npm install -g pm2
fi
pm2 delete autocut-frontend autocut-backend 2>/dev/null || true
pm2 start ecosystem.config.js
pm2 save
# Setup PM2 to start on boot
pm2 startup systemd -u root --hp /root 2>/dev/null || true
echo "  PM2 started."
echo ""
pm2 list
REMOTE_SCRIPT

echo "  Server setup complete."
echo ""

# --- Step 6: Verify ---
echo "[6/6] Verifying deployment..."
sleep 5

# Check backend health via direct IP
HEALTH=$(curl -s --connect-timeout 10 "http://${SERVER_IP}/api/health" -H "Host: autocut.allinai.asia" 2>/dev/null)
echo "  Backend health (direct): $HEALTH"

# Check via domain
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "http://autocut.allinai.asia/api/health" 2>/dev/null || echo "000")
echo "  Backend health (domain): HTTP $HTTP_CODE"

HTTP_CODE_FE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "http://autocut.allinai.asia/" 2>/dev/null || echo "000")
echo "  Frontend (domain): HTTP $HTTP_CODE_FE"

echo ""
echo "======================================"
echo "  Deployment Complete!"
echo "  URL: http://autocut.allinai.asia"
echo "======================================"
echo ""
echo "Next steps for SSL:"
echo "  ssh -i $SSH_KEY root@$SERVER_IP"
echo "  certbot --nginx -d autocut.allinai.asia"
echo ""
echo "Monitor logs:"
echo "  ssh -i $SSH_KEY root@$SERVER_IP 'pm2 logs'"
