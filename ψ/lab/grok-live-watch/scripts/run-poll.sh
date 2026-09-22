#!/bin/bash
# launchd gives the process a bare PATH (no shell profile), so this uses the project's
# own .venv python by absolute path — same reasoning as grafana-report-bot's run-report.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"

cd "$SCRIPT_DIR"
exec "$PYTHON_BIN" run.py
