#!/usr/bin/env bash
# Fill remaining example gaps and re-import (run after finish_word_bank.sh).
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
LOG="${LOG:-/home/mentor/topup_examples.log}"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

for level in a1 a2 b1 b2; do
  log "fill ${level}"
  "$PY" manage.py fill_level_examples --level "$level" >> "$LOG" 2>&1 || true
done

log "final seed"
"$PY" manage.py seed_word_bank --include-remote --apply-quotas --level c1 >> "$LOG" 2>&1

log "stats"
"$PY" manage.py shell <<'PY' >> "$LOG" 2>&1
from learning.models import WordBankEntry
from django.db.models import Q
targets = {'a1': 500, 'a2': 1000, 'b1': 2000, 'b2': 4000, 'c1': 8000}
for lvl, target in targets.items():
    qs = WordBankEntry.objects.filter(cefr_level=lvl, is_active=True)
    print(f'{lvl.upper()}: {qs.count()}/{target}, examples {qs.exclude(Q(example="")|Q(example__isnull=True)).count()}')
PY
