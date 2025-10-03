#!/usr/bin/env bash
set -euo pipefail

# -- Config --
APP_USER="${APP_USER:-$(id -un)}"
APP_GROUP="${APP_GROUP:-$(id -gn "${APP_USER}")}"
APP_HOME="${APP_HOME:-$HOME}"

if [[ $EUID -eq 0 ]]; then
	CHOWN=chown
else CHOWN="sudo chown"
fi


APP_ROOT="${APP_ROOT:-$APP_HOME/exterminus}"
VENV_DIR="${VENV_DIR:-$APP_ROOT/.venv}"
SERVICE_NAME="${SERVICE_NAME:-exterminus}"
SERVICE_PORT="${SERVICE_PORT:-8000}"
APP_FACTORY="${APP_FACTORY:-exterminus.app:create_app()}"
REQ_FILE="${REQ_FILE:-requirements.txt}"
DB_PATH="${DB_PATH:-${APP_ROOT}/instance/exterminus.sqlite3}"
DB_BACKUP_DIR="${DB_BACKUP_DIR:-${APP_ROOT}/backups}"
USE_ALEMBIC="${USE_ALEMBIC:-0}"

log() { printf "\033[1;36m==>\033[0m %s\n" "$*"; }
die() {
  printf "\033[1;31mERROR:\033[0m %s\n" "$*" >&2
  exit 1
}

# -- Preflight --
command -v python3 >/dev/null || {
  sudo apt update
  sudo apt install -y python3 python3-venv python3-pip
}

sudo mkdir -p "${APP_ROOT}" "${APP_HOME}"
sudo chown -R "${APP_USER}:${APP_GROUP}" "${APP_HOME}"

# -- Ensure root --
REPO_TOP="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${REPO_TOP}" ]]; then
  die "Run this from inside the ExTerminus git repo on the server."
fi
cd "${REPO_TOP}"

# -- Python --
if [[ ! -d "${VENV_DIR}" ]]; then
  log "Creating venv at ${VENV_DIR}"
  python3 -m venv .venv
fi

log "Upgrading pip & installing requirements."
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip
if [[ -f "${REQ_FILE}" ]]; then
  pip install -r "${REQ_FILE}"
else
  log "No ${REQ_FILE}; skipping pip install."
fi

# Instance & .env
mkdir -p "${APP_ROOT}/instance" "${DB_BACKUP_DIR}"
ENV_FILE="${APP_ROOT}/.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  log "Creating ${ENV_FILE} from deploy/.env.example (edit secrets!)"
  if [[ -f "deploy/.env.example" ]]; then
    cp deploy/.env.example "${ENV_FILE}"
  else
    cat >"${ENV_FILE}" <<'EOF'
FLASK_ENV=production
SECRET_KEY=change-me
# DATABASE_URL=sqlite:///instance/exterminus.sqlite3
EOF
  fi
  chown "${APP_USER}:${APP_GROUP}" "${ENV_FILE}"
  chmod 640 "${ENV_FILE}"
fi

# -- DB backup & migrations
if [[ -f "${DB_PATH}" ]]; then
  TS="$(date +%Y%m%d-%H%M%S)"
  cp -v "${DB_PATH}" "${DB_BACKUP_DIR}/exterminus-${TS}.sqlite3.bak"
fi
if [[ "${USE_ALEMBIC}" == "1" && -f "alembic.ini" ]]; then
  log "Running Alembic migrations."
  sudo -u "${APP_USER}" "${VENV_DIR}/bin/alembic" upgrade head
fi

# -- systemd service
log "Rendering systemd service."
sudo bash scripts/render-service.sh \
  "${SERVICE_NAME}" "${APP_USER}" "${APP_ROOT}" "${VENV_DIR}" "${SERVICE_PORT}" "${APP_FACTORY}"

log "Reloading systemd & (re)starting ${SERVICE_NAME}"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

log "Done."
systemctl --no-pager --full status "${SERVICE_NAME}" || true
