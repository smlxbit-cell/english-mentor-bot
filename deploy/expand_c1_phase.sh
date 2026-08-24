#!/usr/bin/env bash
# Expand corpus + seed C1 native words + fill C1/B2 example gaps.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
LOG="${LOG:-/home/mentor/expand_c1.log}"
STATUS="${STATUS:-/home/mentor/word_bank_status.txt}"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

write_status() {
  "$PY" manage.py word_bank_status > "$STATUS" 2>> "$LOG" || true
  log "---"
  cat "$STATUS" >> "$LOG" || true
}

log "=== C1 phase START ==="
write_status

log "refresh Kelly + FreeDict + seed"
"$PY" manage.py seed_word_bank --fetch --fetch-freedict --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1
write_status

for level in b2 c1; do
  log "fill examples ${level}"
  "$PY" manage.py fill_level_examples --level "$level" >> "$LOG" 2>&1 || true
  write_status
done

log "final seed"
"$PY" manage.py seed_word_bank --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1
write_status

log "=== C1 phase DONE ==="
