#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python scripts/operations.py migrate
exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-8501}"
