#!/usr/bin/env bash
# Expand word bank toward 5000: Kelly + EN-RU + FreeDict supplements, then examples.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
LOG="${LOG:-/home/mentor/expand_word_bank.log}"
STATUS="${STATUS:-/home/mentor/word_bank_status.txt}"
PHASE="${PHASE:-/home/mentor/word_bank_phase.txt}"

log() { echo "[$(date -Iseconds)] $*" >> "$LOG"; echo "[$(date -Iseconds)] $*"; }
phase() { echo "$1" > "$PHASE"; log ">>> $1"; }

write_status() {
  {
    echo "Updated: $(date -Iseconds)"
    echo "Phase: $(cat "$PHASE" 2>/dev/null || echo unknown)"
    echo ""
    "$PY" manage.py word_bank_status
  } > "$STATUS"
  cat "$STATUS" >> "$LOG"
}

phase "1/4 fetch + merge supplements"
log "fix_translations (pre-clean)"
"$PY" manage.py fix_translations >> "$LOG" 2>&1 || true
log "seed fetch Kelly + EN-RU + FreeDict supplements"
"$PY" manage.py seed_word_bank --fetch --fetch-freedict --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1
write_status

phase "2/4 fill examples (new words only)"
for level in b2 c1; do
  phase "2/4 fill ${level}"
  "$PY" manage.py fill_level_examples --level "$level" --until-complete >> "$LOG" 2>&1 || true
  write_status
done

phase "3/4 import examples"
"$PY" manage.py seed_word_bank --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1
write_status

phase "4/4 second pass B2 C1"
for level in b2 c1; do
  "$PY" manage.py fill_level_examples --level "$level" --limit 200 >> "$LOG" 2>&1 || true
done
"$PY" manage.py seed_word_bank --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1
"$PY" manage.py fix_translations >> "$LOG" 2>&1 || true

phase "DONE"
write_status
log "=== EXPAND WORD BANK COMPLETE ==="
