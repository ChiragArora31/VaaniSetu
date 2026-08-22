#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python scripts/operations.py migrate
exec uvicorn app:app --host "${BAIF_HOST:-127.0.0.1}" --port "${PORT:-8501}"
