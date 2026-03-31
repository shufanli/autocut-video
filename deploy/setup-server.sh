#!/bin/bash
# =============================================================
# AutoCut Video - Server Setup Script
# Target: Alibaba Cloud Linux 3 (alinux3 / al8 based)
# =============================================================
set -e

echo "=== AutoCut Server Setup ==="

# --- 1. Install Python 3.10+ ---
echo "[1/5] Installing Python 3.10..."
if command -v python3.10 &>/dev/null; then
    echo "  Python 3.10 already installed: $(python3.10 --version)"
else
    # alinux3 / al8 has python39 in appstream; we install 3.9 which meets
    # FastAPI + pydantic-settings requirements (>= 3.8)
    # If 3.11 is available, prefer it.
    yum install -y python39 python39-pip python39-devel 2>/dev/null || \
    yum install -y python3 python3-pip python3-devel 2>/dev/null
    # Try to get the highest available version
    if command -v python3.9 &>/dev/null; then
        echo "  Python 3.9 installed: $(python3.9 --version)"
        PYTHON_BIN=python3.9
    elif command -v python3.11 &>/dev/null; then
        echo "  Python 3.11 installed: $(python3.11 --version)"
        PYTHON_BIN=python3.11
    else
        echo "  Using system python3: $(python3 --version)"
        PYTHON_BIN=python3
    fi
fi

# Determine best Python binary
for py in python3.12 python3.11 python3.10 python3.9; do
    if command -v $py &>/dev/null; then
        PYTHON_BIN=$py
        break
    fi
done
echo "  Using: $PYTHON_BIN ($(${PYTHON_BIN} --version 2>&1))"

# --- 2. Install FFmpeg ---
echo "[2/5] Installing FFmpeg..."
if command -v ffmpeg &>/dev/null; then
    echo "  FFmpeg already installed: $(ffmpeg -version | head -1)"
else
    # Try EPEL first, then static binary
    yum install -y epel-release 2>/dev/null || true
    yum install -y ffmpeg 2>/dev/null || {
        echo "  yum ffmpeg not available, installing static binary..."
        cd /tmp
        curl -L -o ffmpeg-release.tar.xz "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        tar xf ffmpeg-release.tar.xz
        FFDIR=$(ls -d ffmpeg-*-static 2>/dev/null | head -1)
        if [ -n "$FFDIR" ]; then
            cp "$FFDIR/ffmpeg" /usr/local/bin/
            cp "$FFDIR/ffprobe" /usr/local/bin/
            chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe
        fi
        rm -rf /tmp/ffmpeg-*
        cd -
    }
    echo "  FFmpeg installed: $(ffmpeg -version 2>&1 | head -1)"
fi

# --- 3. Install PM2 ---
echo "[3/5] Installing PM2..."
if command -v pm2 &>/dev/null; then
    echo "  PM2 already installed: $(pm2 --version)"
else
    npm install -g pm2
    echo "  PM2 installed: $(pm2 --version)"
fi

# --- 4. Install certbot for SSL ---
echo "[4/5] Installing Certbot..."
if command -v certbot &>/dev/null; then
    echo "  Certbot already installed"
else
    yum install -y certbot python3-certbot-nginx 2>/dev/null || {
        pip3 install certbot certbot-nginx 2>/dev/null || true
    }
fi

# --- 5. Create deploy directory structure ---
echo "[5/5] Setting up directory structure..."
DEPLOY_DIR=/www/wwwroot/autocut-video
mkdir -p $DEPLOY_DIR/backend
mkdir -p $DEPLOY_DIR/frontend
mkdir -p $DEPLOY_DIR/backend/uploads
mkdir -p $DEPLOY_DIR/logs

echo ""
echo "=== Setup Complete ==="
echo "Python: $(${PYTHON_BIN} --version 2>&1)"
echo "FFmpeg: $(ffmpeg -version 2>&1 | head -1)"
echo "PM2:    $(pm2 --version 2>&1)"
echo "Node:   $(node --version)"
echo ""
echo "Next: Run deploy.sh to deploy the application"
