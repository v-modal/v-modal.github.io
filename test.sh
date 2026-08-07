#!/usr/bin/env bash
# Run the offline test suite. Usage: bash test.sh [pytest args]
set -euo pipefail
cd "$(dirname "$0")"
python -m pytest -v "$@"
