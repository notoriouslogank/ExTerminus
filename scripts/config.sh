#!/usr/bin/env bash
set -euo pipefail

CONF_FILE="${CONF_FILE:-deploy/config.env}"
LOCAL_CONF="${LOCAL_CONFG:-deploy/config.local.env}"

# Export everything loaded from env
if [[ -f "$CONF_FILE" ]]; then set -a; "$CONF_FILE"; set +a; fi
if [[ -f "$LOCAL_CONF" ]]; then set -a; . "$LOCAL_CONF"; set +a; fi

# Final safety defaults if still unset
APP_USSER="${APP_USER:-$(id -un)}"

#APP_HOME via passwd DB; fallback to $HOME
if [[ -z "${APP_HOME:-}" ]]; then
  APP_HOME="$(getent passwd "$APP_USER" | cut -d: -f6 2>/dev/null | echo "$HOME")"
fi

# If not set, prefer git repo root; else $APP_HOME/exterminus
REPO_TOP="$(git rev-parse --show-toplevel 2>/dev/null || true)"
APP_ROOT="${APP_ROOT:-${REPO_TOP:-${APP_HOME}/exterminus}}"

VENV_DIR="${VENV_DIR:-${APP_ROOT}/.venv}"
SERVICE_NAME="${SERVICE_NAME:-exterminus}"
SERVICE_PORT="${SERVICE_PORT:-8000}"
APP_FACTORY="${APP_FACTORY:-exterminus.app:create_app()}"

NGROK_BIN="${NGROK_BIN:-/usr/local/bin/ngrok}"
DOMAIN="${DOMAIN:-exterminus.ngrok.app}"
CONFIG_PATH="${CONFIG_PATH:-${APP_HOME}/.config/ngrok/ngrok.yml}"
TUNNEL_NAME="${TUNNEL_NAME:-exterminus}"
REGION="${REGION:-us}"

DB_PATH="${DB_PATH:-${APP_ROOT}/instance/exterminus.sqlite3}"
DB_BACKUP_DIR="${DB_BACKUP_DIR:-${APP_ROOT}/backups}"
USE_ALEMBIC="${USE_ALEMBIC:-0}"

require_bins() { for b in "$@"; do command -v "$b" >/dev/null || { echo "Missing binary: $b" >&2; exit 1; }; done; }
require_vars() { for v in "$@"; do [[ -n "${!v:-}" ]] || { echo "Missing var: $v" >&2; exit 1; }; done; }

print_config() {
  cat <<EOF
  APP_USER=$APP_USER
  APP_HOME=$APP_HOME
  VENV_DIR=$VENV_DIR
  SERVICE_NAME=$SERVICE_NAME
  SERVICE_PORT=$SERVICE_PORT
  APP_FACTORY=$APP_FACTORY
  DOMAIN=$DOMAIN
  CONFIG_PATH=$CONFIG_PATH
  TUNNEL_NAME=$TUNNEL_NAME
  REGION=$REGION
  DB_PATH=$DB_PATH
  DB_BACKUP_DIR=$DB_BACKUP_DIR
  USE_ALEMBIC=$USE_ALEMBIC
  EOF
}
