#!/usr/bin/env bash
set -euo pipefail

# MConnect — one-command deploy for the 10.14.0.42 production server (or any server).
# Gets the latest code from GitHub, ensures Docker, then starts the stack.
#
# Usage:  bash deploy.sh           (or)   ./deploy.sh
# Optional: APP_DIR=/path ./deploy.sh   (install location, default ~/mconnect)

APP_DIR="${APP_DIR:-$HOME/mconnect}"
REPO_URL="${REPO_URL:-https://github.com/kumamarb-hub/mconnect.git}"

echo "==> MConnect deploy"
echo "    App dir : $APP_DIR"
echo "    Repo    : $REPO_URL"

# --- 1. Ensure Docker ---
if ! command -v docker >/dev/null 2>&1; then
  echo "==> Docker not found — installing..."
  if ! curl -fsSL https://get.docker.com | sh; then
    echo "==> get.docker.com failed (likely a repo GPG issue) — trying distro package instead..."
    sudo apt-get update -qq || true
    sudo apt-get install -y -qq docker.io docker-compose-plugin
  fi
  sudo usermod -aG docker "$USER"
  echo ""
  echo "Your user was added to the 'docker' group."
  echo "Log out and back in, then re-run:  ./deploy.sh"
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "==> Docker Compose plugin missing — installing..."
  # Ignore per-repo errors (e.g. an unsigned external repo) so one bad repo
  # can't abort the deploy; the packages we need will still resolve.
  sudo apt-get update -qq || true
  if ! sudo apt-get install -y -qq docker-compose-plugin; then
    # Compose plugin isn't in distro repos — install the standalone binary.
    ARCH=$(uname -m)
    case "$ARCH" in
      aarch64|arm64) COMPOSE_ARCH="aarch64" ;;
      *)             COMPOSE_ARCH="x86_64"  ;;
    esac
    echo "==> Downloading docker compose binary ($COMPOSE_ARCH)..."
    sudo mkdir -p /usr/local/lib/docker/cli-plugins
    sudo curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$COMPOSE_ARCH" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
  fi
  docker compose version >/dev/null 2>&1 || { echo "[ERROR] docker compose still not available."; exit 1; }
fi

# --- 2. Get (or update) the app code ---
if [ -d "$APP_DIR/.git" ]; then
  echo "==> Updating app at $APP_DIR ..."
  cd "$APP_DIR"
  git pull
else
  echo "==> Cloning app to $APP_DIR ..."
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi

# --- 3. Start the stack ---
echo "==> Building and starting containers..."
docker compose up -d --build

# --- 4. Report ---
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
printf '\n[OK] MConnect is up!\n'
printf '     Local:      http://localhost:4000\n'
[ -n "${IP:-}" ] && printf '     On network: http://%s:4000\n' "$IP"

echo ""
echo "Useful:"
echo "  docker compose logs -f web   # view app logs"
echo "  cd $APP_DIR && git pull && docker compose up -d --build   # update later"