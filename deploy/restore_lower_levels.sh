#!/usr/bin/env bash
# Restore A1/B1/B2 quotas after a bad full re-seed. No --fetch, no C1 supplement churn.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
LOG="${LOG:-/home/mentor/restore_quotas.log}"
STATUS="${STATUS:-/home/mentor/word_bank_status.txt}"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

log "=== RESTORE lower-level quotas START ==="
"$PY" manage.py word_bank_status | tee -a "$LOG"

log "re-seed from cached remote (forward quota cascade)"
"$PY" manage.py seed_word_bank --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1

log "=== RESTORE DONE ==="
"$PY" manage.py word_bank_status | tee -a "$LOG"
"$PY" manage.py word_bank_status > "$STATUS"
echo "RESTORED" > /home/mentor/word_bank_phase.txt
