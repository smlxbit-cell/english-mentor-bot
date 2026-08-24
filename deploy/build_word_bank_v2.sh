#!/usr/bin/env bash
# Build conversational word bank v2: Kelly-only, no junk, native exclusive levels, 2-3 examples.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
LOG="${LOG:-/home/mentor/build_word_bank_v2.log}"
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

log "migrate"
"$PY" manage.py migrate --noinput >> "$LOG" 2>&1

phase "1/5 fetch Kelly + FreeDict (RU enrichment only)"
"$PY" manage.py seed_word_bank --fetch --fetch-freedict --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1
write_status

phase "2/5 fill 2-3 examples per level"
for level in a1 a2 b1 b2 c1; do
  phase "2/5 fill ${level}"
  "$PY" manage.py fill_level_examples --level "$level" --until-complete >> "$LOG" 2>&1 || true
  write_status
done

phase "3/5 import examples + purge junk slugs"
"$PY" manage.py seed_word_bank --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1
write_status

phase "4/5 second example pass"
for level in a1 a2 b1 b2 c1; do
  "$PY" manage.py fill_level_examples --level "$level" --until-complete >> "$LOG" 2>&1 || true
done
"$PY" manage.py seed_word_bank --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1
write_status

phase "DONE"
write_status
log "=== BUILD WORD BANK V2 COMPLETE ==="
