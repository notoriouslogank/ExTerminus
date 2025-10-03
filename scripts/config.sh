#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(git -C "$SCRIPT_DIR/.." rev-parse --show-toplevel 2>/dev/null \
	|| (cd "$SCRIPT_DIR/.." && pwd))"
CONF_FILE="${CONF_FILE:-${ROOT_DIR}/deploy/config.env}"
LOCAL_CONF="${LOCAL_CONF:-${ROOT_DIR}/deploy/config.local.env}"

load_env() {
  if [ -r "$1" ]; then
    set -a
    . "$1"
    set +a
  fi
}

if [[ -e "$CONF_FILE" && ! -r "$CONF_FILE" ]]; then
	echo "Config not readable: $CONF_FILE"; exit 1
fi

load_env "$CONF_FILE"
load_env "$LOCAL_CONF"

strip_braces() { eval "$1=\"\${$1//\{}\""; eval "$1=\"\${$1//\}}\""; }



# Export everything loaded from env
#if [[ -f "$CONF_FILE" ]]; then set -a; "$CONF_FILE"; set +a; fi
#if [[ -f "$LOCAL_CONF" ]]; then set -a; . "$LOCAL_CONF"; set +a; fi

# Final safety defaults if still unset
APP_USER="${APP_USER:-$(id -un)}"

#APP_HOME via passwd DB; fallback to $HOME
if [[ -z "${APP_HOME:-}" ]]; then
  APP_HOME="$(getent passwd "$APP_USER" | cut -d: -f6 2>/dev/null || true)"
fi

# If not set, prefer git repo root; else $APP_HOME/exterminus
REPO_TOP="$(git rev-parse --show-toplevel 2>/dev/null || true)"
APP_ROOT="${APP_ROOT:-${REPO_TOP:-$APP_HOME/exterminus}}"

REPO_NAME="$(basename "$APP_ROOT")"

: "${APP_USER:=$(id -un)}"
: "${APP_HOME:=${HOME_SAFE:-$HOME}}"
: "${SERVICE_NAME:=$REPO_NAME}"
: "${SERVICE_PORT:=8000}"
: "${APP_FACTORY:=exterminus.app:create_app()}"
: "${VENV_DIR:=$APP_ROOT/.venv}"
: "${CONFIG_PATH:=$APP_ROOT/deploy}"

# ngrok (off by default unless DOMAIN is set)
: "${DOMAIN:=}"						# empty = 'disabled'
: "${NGROK_BIN:=/usr/local/bin/ngrok}"
: "${TUNNEL_NAME:=$SERVICE_NAME}"
: "${REGION:=us}"

# SQLite defaults
: "${DB_PATH:=$APP_ROOT/instance/exterminus.sqlite3}"
: "${DB_BACKUP_DIR:=$APP_ROOT/backups}"
: "${USE_ALEMBIC:=0}"

require_bins() { for b in "$@"; do command -v "$b" >/dev/null || { echo "Missing binary: $b" >&2; exit 1; }; done; }
require_vars() { for v in "$@"; do [[ -n "${!v:-}" ]] || { echo "Missing var: $v" >&2; exit 1; }; done; }
for v in APP_USER APP_HOME APP_ROOT; do strip_braces "$v"; done

print_config() {
printf 'APP_USER=%s\n' "$APP_USER"
printf 'APP_HOME=%s\n' "$APP_HOME"
printf 'APP_ROOT=%s\n' "$APP_ROOT"
printf 'VENV_DIR=%s\n' "$VENV_DIR"
printf 'SERVICE_NAME=%s\n' "$SERVICE_NAME"
printf 'SERVICE_PORT=%s\n' "$SERVICE_PORT"
printf 'APP_FACTORY=%s\n' "$APP_FACTORY"
printf 'DOMAIN=%s\n' "$DOMAIN"
printf 'CONFIG_PATH=%s\n' "$CONFIG_PATH"
printf 'TUNNEL_NAME=%s\n' "$TUNNEL_NAME"
printf 'REGION=%s\n' "$REGION"
printf 'DB_PATH=%s\n' "$DB_PATH"
printf 'DB_BACKUP=%s\n' "$DB_BACKUP_DIR"
printf 'USE_ALEMBIC=%s\n' "$USE_ALEMBIC"
}
