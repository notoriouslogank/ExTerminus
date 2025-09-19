#!/usr/bin/env bash
set -Eeuo pipefail
VER=$(python3 - <<'PY'
import re, sys
txt=open('utils/version.py', 'r', encoding='utf-8').read()
m=re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", txt)
print(m.group(1) if m else "0.0.0.0")
PY
)
tmp=$(mktemp)
awk -v v="$VER" '{if ($0 ~ /<!--VERSION-->/) { sub(/(<!--VERSION>).*/, "\\1 " v) } print }' README.md > "$tmp"
mv "$tmp" README.md
echo "README version set to $VER"