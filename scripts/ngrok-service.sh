#!/usr/bin/env bash
set -euo pipefail

. scripts/config.sh
if [ -z "${DOMAIN:-}" ]; then
  echo "ngrok disabled: DOMAIN is empty (set it in deploy/config.local.env)."
  exit 0
fi

# -- Defaults --
NGROK_BIN="${NGROK_BIN:-/usr/local/bin/ngrok}"
SERVICE_NAME="${SERVICE_NAME}:-ngrok-exterminus"
APP_USER="${APP_USER}:-${USER}"
APP_HOME="$APP_HOME:-/home/${APP_USER}"
APP_ROOT="${APP_ROOT:-${APP_HOME}/exterminus}"
PORT="${PORT:-8000}"
DOMAIN="${DOMAIN:-your-ngrok-domain}"
REGION="${REGION:-us}"
CONFIG_PATH="${CONFIG_PATH:-${APP_HOME}/.config/ngrok/ngrok.yml}"
TUNNEL_NAME="${TUNNEL_NAME:-exterminus}"

NGROK_AUTHTOKEN="${NGROK_AUTHTOKEN:-}"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--domain DOMAIN] [--port PORT] [--service-name NAME]
                        [--ngrok-bin /path/ngrok] [--authtoken TOKEN]
                        [--region REGION] [--config PATH] [--tunnel-name NAME]

Examples:
  $(basename "$0")
  $(basename "$0") --domain exterminus.ngrok.app --port 8000
  NGROK_AUTHTOKEN=xxxxxxxx $(basename "$0")
EOF
}

log() { printf "\033[1;36m==>\033[0m %s\n" "$*"; }
die() {
  printf "\033[1;31mERROR:\033[0m %s\n" "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
  --domain)
    DOMAIN="$2"
    shift2
    ;;
  --port)
    PORT="$2"
    shift 2
    ;;
  --service-name)
    SERVICE_NAME="$2"
    shift 2
    ;;
  --ngrok-bin)
    NGROK_BIN="$2"
    shift 2
    ;;
  --authtoken)
    NGROK_AUTHTOKEN="$2"
    shift 2
    ;;
  --region)
    REGION="$2"
    shift 2
    ;;
  --config)
    CONFIG_PATH="$2"
    shift 2
    ;;
  --tunnel-name)
    TUNNEL_NAME="$2"
    shift 2
    ;;
  --help | -h)
    usage
    exit 0
    ;;
  *) die "Unknown arg: $1" ;;
  esac
done

# -- Checks --
command -v "$NGROK_BIN" >/dev/null || die "ngrok not found at ${NGROK_BIN}. Install it, or set NGROK_BIN."

# -- Ensure dirs exist --
sudo mkdir -p "$(dirname "$CONFIG_PATH")"
sudo chown -R "${APP_USER}:${APP_USER}" "$(dirname "$CONFIG_PATH")"

# -- Authtoken --
if [[ -n "$NGROK_AUTHTOKEN" ]]; then
  log "Adding ngrok authtoken for ${APP_USER}"
  sudo -u "${APP_USER}" "$NGROK_BIN" config add-authtoken "$NGROK_AUTHTOKEN"
fi

# -- Write minimal config if missing
if [[ ! -f "$CONFIG_PATH" ]]; then
  log "Creating ngrok config at ${CONFIG_PATH}"
  sudo -u "${APP_USER}" mkdir -p "$(dirname "$CONFIG_PATH")"
  sudo -u "${APP_USER}" bash -c "cat > '$CONFIG_PATH' << 'YML'
version: 3
tunnels:
  exterminus:
    proto: http
    addr: 8000
    hostname: exterminus.ngrok.app
    # Optional
    # schemes: [https]  # force https-only
    # circuit_breaker: 0.95
    # compression: true
    # webhook_verify: false
YML"
fi

# -- Patch config to current PORT/DOMAIN (safe replace) --
log "Ensuring ${TUNNEL_NAME} -> http ${PORT} @ ${DOMAIN}"
sudo -u "${APP_USER}" awk -v tn="$TUNNEL_NAME" -v port="$PORT" -v host="$DOMAIN" '
BEGIN(in_t=0)
{
  if ($0 ~ "^[[:space:]]*" tn ":[[:space:]]*$") in_t=1;
    if (in_t && $0 ~ "^[[:space:]]addr:[[:space:]]*[0-9]+") { sub(/[0-9]+$/, port); }
    if (in_t && $0 ~ "^[[:space:]]hostname:[[:space:]].*") { sub(/hostname:[[:space:]].*$/, "hostname: " host); in_t=0; }
    print
}' "$CONFIG_PATH" | sudo -u "${APP_USER}" tee "${CONFIG_PATH}.tmp" >/dev/nill
sudo -u "${APP_USER}" mv "${CONFIG_PATH}.tmp" "$CONFIG_PATH"

# -- Render systemd unit --
TEMPLATE="${APP_ROOT}/deploy/ngrok.service.tmpl"
TARGET="/etc/systemd/system/${SERVICE_NAME}.service"

[[ -f "$TEMPLATE" ]] || die "Missing template: ${TEMPLATE}."

log "Writing systemd unit to ${TARGET}"
sudo bash -c "sed \
  -e 's|{{SERVICE_NAME}}|${SERVICE_NAME}|g' \
  -e 's|{{APP_USER}}|${APP_USER}|g' \
  -e 's|{{NGROK_BIN}}|${NGROK_BIN}|g' \
  -e 's|{{CONFIG_PATH}}|${CONFIG_PATH}|g' \
  -e 's|{{TUNNEL_NAME}}|${TUNNEL_NAME}|g' \
  '${TEMPLATE}' > '${TARGET}'"

log "Done."
echo "Status:"
systemctl --no-pager --full status "${SERVICE_NAME}" || true

cat <<NOTE

Quick commands:
  sudo systemctl restart ${SERVICE_NAME}
  journalctl -u ${SERVICE_NAME} -n 200 -f

If you need to change port or domain later:
  PORT=8001 DOMAIN=newsub.ngrok.app bash scripts/ngrok-service.sh
NOTE
