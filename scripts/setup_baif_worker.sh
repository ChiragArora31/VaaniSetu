#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python3 scripts/one_click_setup.py --profile balanced
