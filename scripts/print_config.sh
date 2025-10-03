#!/usr/bin/env bash
set -Eeuo pipefail
trap 'code=$?; echo "[print-config] failed at ${BASH_SOURCE[0]}:${LINENO} (exit $code)"; exit $code' ERR

# always run from repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# load + print
# shellcheck source=/dev/null
source "scripts/config.sh"

# sanity: ensure function exists; if not, dump vars directly so we still see output
if ! type -t print_config >/dev/null; then
  echo "[print-config] print_config() not found; dumping vars directly"
  printf 'APP_USER=%s\n'        "${APP_USER:-<unset>}"
  printf 'APP_HOME=%s\n'        "${APP_HOME:-<unset>}"
  printf 'APP_ROOT=%s\n'        "${APP_ROOT:-<unset>}"
  printf 'VENV_DIR=%s\n'        "${VENV_DIR:-<unset>}"
  printf 'SERVICE_NAME=%s\n'    "${SERVICE_NAME:-<unset>}"
  printf 'SERVICE_PORT=%s\n'    "${SERVICE_PORT:-<unset>}"
  printf 'APP_FACTORY=%s\n'     "${APP_FACTORY:-<unset>}"
  printf 'DOMAIN=%s\n'          "${DOMAIN:-<unset>}"
  printf 'CONFIG_PATH=%s\n'     "${CONFIG_PATH:-<unset>}"
  printf 'TUNNEL_NAME=%s\n'     "${TUNNEL_NAME:-<unset>}"
  printf 'REGION=%s\n'          "${REGION:-<unset>}"
  printf 'DB_PATH=%s\n'         "${DB_PATH:-<unset>}"
  printf 'DB_BACKUP_DIR=%s\n'   "${DB_BACKUP_DIR:-<unset>}"
  printf 'USE_ALEMBIC=%s\n'     "${USE_ALEMBIC:-<unset>}"
  exit 0
fi

print_config
