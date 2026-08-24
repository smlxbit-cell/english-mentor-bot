#!/usr/bin/env bash
set -euo pipefail
cd /home/mentor/english-mentor-bot
PY=.venv/bin/python
LOG=/home/mentor/c1_expand.log
echo C1-EXPAND > /home/mentor/word_bank_phase.txt
{
  echo "[$(date -Iseconds)] fill c1 examples only (no quota re-seed)"
  "$PY" manage.py fill_level_examples --level c1 --until-complete || true
  echo "[$(date -Iseconds)] stats"
  "$PY" manage.py word_bank_status
  echo DONE > /home/mentor/word_bank_phase.txt
  "$PY" manage.py word_bank_status > /home/mentor/word_bank_status.txt
  echo "[$(date -Iseconds)] FINISHED"
} >> "$LOG" 2>&1