#!/usr/bin/env bash
# Fill example gaps on all levels until complete, then re-seed.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
LOG="${LOG:-/home/mentor/ensure_examples.log}"
STATUS="${STATUS:-/home/mentor/word_bank_status.txt}"
PHASE="${PHASE:-/home/mentor/word_bank_phase.txt}"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

write_status() {
  {
    echo "Updated: $(date -Iseconds)"
    echo "Phase: $(cat "$PHASE" 2>/dev/null || echo unknown)"
    echo ""
    "$PY" manage.py word_bank_status
  } > "$STATUS"
}

echo "EXAMPLES-100" > "$PHASE"
log "=== ensure 100% examples START ==="
write_status

for level in a1 a2 b1 b2 c1; do
  log "fill ${level} until complete"
  "$PY" manage.py fill_level_examples --level "$level" --until-complete >> "$LOG" 2>&1 || true
  write_status
done

log "re-seed all levels"
"$PY" manage.py seed_word_bank --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1
write_status

log "second pass for any seed gaps"
for level in a1 a2 b1 b2 c1; do
  "$PY" manage.py fill_level_examples --level "$level" --until-complete >> "$LOG" 2>&1 || true
done
"$PY" manage.py seed_word_bank --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1

echo "DONE" > "$PHASE"
write_status
log "=== ensure 100% examples DONE ==="
