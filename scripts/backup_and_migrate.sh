#!/usr/bin/env bash
set -Eeuo pipefail

# Resolve DB path (override by exporting EXTERM_DB_PATH)
DB_PATH="${EXTERM_DB_PATH:-instance/exterminus.sqlite3}"

# If user gave a sqlite URL, strip prefix
if [[ "$DB_PATH" == sqlite:///* ]]; then
  DB_PATH="${DB_PATH#sqlite:///}"
fi

mkdir -p "$(dirname "$DB_PATH")" backups

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="backups/exterminus_${STAMP}.sqlite3"

if [[ -f "$DB_PATH" ]]; then
  cp "$DB_PATH" "$BACKUP"
  echo "Backup created: $BACKUP"
else
  echo "No DB at $DB_PATH (fresh env). Migrations will create/shape it."
fi

PYTHONPATH=. python3 -m migrations.run --db "$DB_PATH"

echo "Done."
