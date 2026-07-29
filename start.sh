#!/usr/bin/env bash
set -euo pipefail

if [ ! -x .venv/bin/python ]; then
  echo "Virtual environment not found. Run ./setup.sh first."
  exit 1
fi

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
exec .venv/bin/python manage.py runserver "${HOST}:${PORT}"
