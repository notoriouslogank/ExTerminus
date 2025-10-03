SHELL := /usr/bin/env bash
SHELLFLAGS := -euo pipefail -c
.PHONY: install

install:
	./scripts/install.sh

update:
	@bash scripts/update.sh

restart:
	@sudo systemctl restart exterminus

status:
	@systemctl --no-pager --full status exterminus || true

logs:
	@journalctl -u exterminus -n 200 -f

ngrok:
	@bash --noprofile --norc -c 'set -eu; source scripts/config.sh; bash scripts/ngrok-service.sh'

ngrok-restart:
	@sudo systemctl restart ngrok-exterminus

ngrok-logs:
	@journalctl -u ngrok-exterminus -n 200 -f

print-config:
	@./scripts/print_config.sh

configure:
	@cp -n deploy/config.example.env deploy/config.local.env 2>/dev/null || true
	@ echo "Edit deploy/config.local.env to override defaults."
