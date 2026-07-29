#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

"$PYTHON_BIN" scripts/preflight.py
"$PYTHON_BIN" manage.py check
"$PYTHON_BIN" manage.py makemigrations --check --dry-run
"$PYTHON_BIN" manage.py test accounts catalog orders core dashboard --verbosity 2

echo "All MAHDAI QA checks passed."
