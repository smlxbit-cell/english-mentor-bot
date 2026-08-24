#!/usr/bin/env bash
# Fill remaining example gaps and re-import (run after finish_word_bank.sh).
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
LOG="${LOG:-/home/mentor/topup_examples.log}"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

for level in a1 a2 b1 b2 c1; do
  log "fill ${level}"
  "$PY" manage.py fill_level_examples --level "$level" --until-complete >> "$LOG" 2>&1 || true
done

log "final seed"
"$PY" manage.py seed_word_bank --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1

log "stats"
"$PY" manage.py word_bank_status >> "$LOG" 2>&1
