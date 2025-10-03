#!/usr/bin/env bash
set -euo pipefail
SVC_NAME="$1"
APP_USER="$2"
APP_ROOT="$3"
VENV_DIR="$4"
PORT="$5"
FACTORY="$6"
TEMPLATE="deploy/exterminus.service.tmpl"
TARGET="/etc/systemd/system/${SVC_NAME}.service"

[[ -f "${TEMPLATE}" ]] || {
  echo "Missing ${TEMPLATE}" >&2
  exit 1
}

# shellcheck disable=SC2002
cat "${TEMPLATE}" |
  sed "s|{{SERVICE_NAME}}|${SVC_NAME}|g" |
  sed "s|{{APP_USER}}|${APP_USER}|g" |
  sed "s|{{APP_ROOT}}|${APP_ROOT}|g" |
  sed "s|{{VENV_DIR}}|${VENV_DIR}|g" |
  sed "s|{{PORT}}|${PORT}|g" |
  sed "s|{{APP_FACTORY}}|${FACTORY}|g" |
  sudo tee "${TARGET}" >/dev/null
