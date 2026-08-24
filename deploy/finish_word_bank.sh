#!/usr/bin/env bash
# Full word-bank pipeline: Kelly CEFR quotas + AI examples for A1–C1.
# Run on prod: nohup bash deploy/finish_word_bank.sh >> /tmp/finish_word_bank.log 2>&1 &
set -euo pipefail

cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
LOG="${LOG:-/tmp/finish_word_bank.log}"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

seed_level() {
  local level="$1"
  log "seed --apply-quotas --level ${level}"
  "$PY" manage.py seed_word_bank --include-remote --apply-quotas --level "$level" >> "$LOG" 2>&1
}

fill_level() {
  local level="$1"
  log "fill_level_examples --level ${level}"
  "$PY" manage.py fill_level_examples --level "$level" >> "$LOG" 2>&1 || true
}

stats() {
  "$PY" manage.py shell <<'PY' | tee -a "$LOG"
from learning.models import WordBankEntry
from django.db.models import Q
targets = {'a1': 500, 'a2': 1000, 'b1': 2000, 'b2': 4000, 'c1': 8000}
for lvl, target in targets.items():
    qs = WordBankEntry.objects.filter(cefr_level=lvl, is_active=True)
    total = qs.count()
    with_ex = qs.exclude(Q(example='') | Q(example__isnull=True)).count()
    print(f'{lvl.upper()}: {total}/{target} words, {with_ex} examples')
PY
}

log "=== START word bank finish ==="
stats

log "=== Phase 1: full quota seed (c1 path) ==="
seed_level c1
stats

for level in a1 a2 b1 b2 c1; do
  log "=== Phase 2: ${level} examples ==="
  fill_level "$level"
  seed_level "$level"
  if [[ "$level" != "a2" ]]; then
    seed_level a2
  fi
  stats
done

log "=== Phase 3: final full seed ==="
seed_level c1
stats
log "=== DONE word bank finish ==="
