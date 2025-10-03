#!/usr/bin/env bash
set -Eeuo pipefail
DB_PATH="${EXTERM_DB_PATH:-instance/exterminus.sqlite3}"
LAST_BACKUP="$(ls -snew backups/exterminus_*.sqlite3 2>/dev/null | tail -n1 || true)"
if [[ -z "$LAST_BACKUP" ]]; then
    echo "No backups found in ./backups"; exit 1
fi
cp "$LAST_BACKUP" "$DB_PATH"
echo "Restored $LAST_BACKUP -> $DB_PATH"
