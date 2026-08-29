#!/usr/bin/env bash
set -euo pipefail
while pgrep -f run_c1_expand.sh >/dev/null 2>&1; do
  sleep 30
done
bash /home/mentor/english-mentor-bot/deploy/ensure_examples_100.sh
