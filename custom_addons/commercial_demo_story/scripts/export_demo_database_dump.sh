#!/usr/bin/env bash
# Exact database + filestore snapshot (all POS, accounting, transactions).
# XML/module bootstrap recreates the same *logic*; pg_dump is the only exact clone.
set -euo pipefail
REPO="${REPO:-/home/sabry3/sabry_backup/odoo_base/base_odoo_19}"
DB="${DB:-demo_pos_accounting}"
OUT="${OUT:-$REPO/projects/demo_pos_accounting/backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT"
export PGPASSWORD="${PGPASSWORD:-odoo19}"
pg_dump -h localhost -U odoo19 -Fc -f "$OUT/${DB}_complete_${STAMP}.dump" "$DB"
FS="$REPO/projects/demo_pos_accounting/.filestore/filestore/$DB"
if [[ -d "$FS" ]]; then
  tar -czf "$OUT/${DB}_filestore_${STAMP}.tar.gz" -C "$(dirname "$FS")" "$(basename "$FS")"
fi
echo "Wrote $OUT/${DB}_complete_${STAMP}.dump"
[[ -d "$FS" ]] && echo "Wrote $OUT/${DB}_filestore_${STAMP}.tar.gz"
