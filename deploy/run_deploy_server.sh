#!/usr/bin/env bash
# Vexus CRM - deployment helper
# Usage (on server):
#   sudo bash run_deploy_server.sh /path/to/repo "api.nexuscrm.tech" /var/www/vexus/frontend
# If arguments are omitted the script will attempt to auto-detect common paths and will prompt.

set -euo pipefail
IFS=$'\n\t'

REPO_PATH=${1:-}
DOMAIN=${2:-api.nexuscrm.tech}
FRONTEND_ROOT=${3:-/var/www/vexus/frontend}
VENV_PATH=${4:-/home/$(whoami)/.venv}
USER_HOME=$(getent passwd $(whoami) | cut -d: -f6)

echo "Starting Vexus CRM deployment helper"
echo "Domain: $DOMAIN"
echo "Repo path: ${REPO_PATH:-(not provided)}"
echo "Frontend root: $FRONTEND_ROOT"
echo "Venv: $VENV_PATH"

# Try to detect repo if not provided
if [ -z "$REPO_PATH" ]; then
  echo "Repo path not provided — attempting to find common locations..."
  if [ -d "$USER_HOME/PycharmProjects/Vexus Service" ]; then
    REPO_PATH="$USER_HOME/PycharmProjects/Vexus Service"
  elif [ -d "/home/$(whoami)/Vexus Service" ]; then
    REPO_PATH="/home/$(whoami)/Vexus Service"
  elif [ -d "/var/www/vexus" ]; then
    REPO_PATH="/var/www/vexus"
  else
    read -rp "Enter application repo absolute path on this server: " REPO_PATH
  fi
fi

if [ ! -d "$REPO_PATH" ]; then
  echo "ERROR: Repo path not found: $REPO_PATH"
  exit 1
fi

echo "Using repo: $REPO_PATH"

# Ensure we have sudo privileges for system operations
if [ "$EUID" -ne 0 ]; then
  echo "Note: Some steps require sudo. The script will call sudo where needed."
fi

# 1) Place frontend static files
echo "\n[1/8] Ensure frontend directory exists: $FRONTEND_ROOT"
sudo mkdir -p "$FRONTEND_ROOT"
# Copy frontend build if exists in repo
if [ -d "$REPO_PATH/frontend" ]; then
  echo "Copying frontend files from repo/frontend -> $FRONTEND_ROOT (rsync)"
  sudo rsync -a --delete "$REPO_PATH/frontend/" "$FRONTEND_ROOT/"
else
  echo "No frontend build found at $REPO_PATH/frontend — skip copy."
fi

# 2) Install system packages
echo "\n[2/8] Installing required packages (nginx, certbot, python3-venv, build-essential)"
sudo apt-get update
sudo apt-get install -y nginx python3-venv python3-pip curl

# 3) Place nginx config
NGINX_CONF_SRC="$REPO_PATH/deploy/nginx_vexus.conf"
NGINX_CONF_DEST="/etc/nginx/sites-available/vexus"
if [ -f "$NGINX_CONF_SRC" ]; then
  echo "\n[3/8] Installing nginx config to $NGINX_CONF_DEST"
  sudo cp "$NGINX_CONF_SRC" "$NGINX_CONF_DEST"
  sudo ln -sf "$NGINX_CONF_DEST" /etc/nginx/sites-enabled/vexus
  sudo nginx -t
  sudo systemctl reload nginx || true
else
  echo "Warning: $NGINX_CONF_SRC not found — please copy it to /etc/nginx/sites-available/vexus manually."
fi

# 4) Create virtualenv and install python deps
echo "\n[4/8] Creating virtualenv at $VENV_PATH and installing requirements"
if [ ! -d "$VENV_PATH" ]; then
  python3 -m venv "$VENV_PATH"
fi
# Activate and install
# shellcheck disable=SC1090
source "$VENV_PATH/bin/activate"
if [ -f "$REPO_PATH/requirements.txt" ]; then
  pip install --upgrade pip
  pip install -r "$REPO_PATH/requirements.txt"
else
  echo "Warning: requirements.txt not found in repo — ensure dependencies installed manually."
fi

# 5) Copy systemd unit files
API_UNIT_SRC="$REPO_PATH/deploy/systemd_vexus_api.service"
WORKER_UNIT_SRC="$REPO_PATH/deploy/systemd_vexus_worker.service"
API_UNIT_DEST="/etc/systemd/system/vexus_api.service"
WORKER_UNIT_DEST="/etc/systemd/system/vexus_worker.service"

if [ -f "$API_UNIT_SRC" ]; then
  echo "\n[5/8] Installing systemd unit for API"
  sudo cp "$API_UNIT_SRC" "$API_UNIT_DEST"
else
  echo "Warning: $API_UNIT_SRC not found — create service file manually."
fi

if [ -f "$WORKER_UNIT_SRC" ]; then
  echo "\n[6/8] Installing systemd unit for Worker"
  sudo cp "$WORKER_UNIT_SRC" "$WORKER_UNIT_DEST"
else
  echo "Warning: $WORKER_UNIT_SRC not found — create worker unit manually."
fi

# 6) Setup .env
ENV_SRC="$REPO_PATH/.env.example"
ENV_DEST="$REPO_PATH/.env"
if [ -f "$ENV_SRC" ] && [ ! -f "$ENV_DEST" ]; then
  echo "\n[7/8] Creating .env from .env.example (please edit with real secrets)"
  sudo cp "$ENV_SRC" "$ENV_DEST"
  sudo chown $(whoami):$(whoami) "$ENV_DEST"
  echo "Fill in production secrets in $ENV_DEST then re-run the following to start services."
else
  echo "\n[7/8] .env already exists or .env.example missing — ensure .env contains production secrets."
fi

# 7) Reload systemd and start services
echo "\n[8/8] Reloading systemd and enabling services"
sudo systemctl daemon-reload
if [ -f "$API_UNIT_DEST" ]; then
  sudo systemctl enable --now vexus_api.service || true
  sudo systemctl restart vexus_api.service || true
fi
if [ -f "$WORKER_UNIT_DEST" ]; then
  sudo systemctl enable --now vexus_worker.service || true
  sudo systemctl restart vexus_worker.service || true
fi

# Final status
echo "\nDeployment helper finished. Summary:"
sudo systemctl status vexus_api.service --no-pager || true
sudo systemctl status vexus_worker.service --no-pager || true

echo "\nRemember to edit $REPO_PATH/.env with real secrets (OPENAI_API_KEY, STRIPE keys, WHATSAPP tokens, TELEGRAM_BOT_TOKEN, DATABASE_URL, REDIS_URL)"

echo "To obtain TLS with certbot (interactive), run:"
echo "  sudo apt-get install -y certbot python3-certbot-nginx"
echo "  sudo certbot --nginx -d $DOMAIN"

echo "If anything failed, paste the output of:"
echo "  sudo journalctl -u vexus_api -n 200 --no-pager"
echo "  sudo journalctl -u vexus_worker -n 200 --no-pager"
echo "  sudo nginx -t"

exit 0
