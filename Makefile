SHELL := /usr/bin/env bash

install:
	@bash scripts/install.sh

update:
	@bash scripts/update.sh

restart:
	@sudo systemctl restart exterminus

status:
	@systemctl --no-pager --full status exterminus || true

logs:
	@journalctl -u exterminus -n 200 -f

ngrok:
	@bash scripts/ngrok-service.sh

ngrok-restart:
	@sudo systemctl restart ngrok-exterminus

ngrok-logs:
	@journalctl -u ngrok-exterminus -n 200 -f

print-config:
	@bash -c '. scripts/config.sh; print_config'
