#!/usr/bin/env bash
# Single long-running word-bank job: one log, periodic status file, no manual restarts.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
LOG="${LOG:-/home/mentor/word_bank_master.log}"
STATUS="${STATUS:-/home/mentor/word_bank_status.txt}"
PHASE="${PHASE:-/home/mentor/word_bank_phase.txt}"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }
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

phase "START"
write_status

phase "0/4 refresh Kelly + dictionaries"
"$PY" manage.py seed_word_bank --fetch --fetch-freedict --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1
write_status

phase "1/4 fill examples A1→C1"
for level in a1 a2 b1 b2 c1; do
  phase "1/4 fill ${level}"
  "$PY" manage.py fill_level_examples --level "$level" >> "$LOG" 2>&1 || true
  write_status
done

phase "2/4 import examples + quotas"
"$PY" manage.py seed_word_bank --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1
write_status

phase "3/4 top-up remaining example gaps"
for level in a1 a2 b1 b2 c1; do
  "$PY" manage.py fill_level_examples --level "$level" >> "$LOG" 2>&1 || true
done
"$PY" manage.py seed_word_bank --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1
write_status

phase "DONE"
write_status
log "=== MASTER RUN COMPLETE ==="
