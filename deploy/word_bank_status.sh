#!/usr/bin/env bash
cd "$(dirname "$0")/.."
.venv/bin/python manage.py word_bank_status
