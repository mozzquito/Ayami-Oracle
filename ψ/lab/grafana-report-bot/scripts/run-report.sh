#!/bin/bash
# Runs a pre-built dist/cli.js report command with an absolute node path,
# since launchd gives the process a bare PATH (no nvm shims). See README's
# "Known limitations" for what to do if the nvm default node version changes.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NODE_BIN="/Users/phongcheatphus/.nvm/versions/node/v22.13.1/bin/node"
CMD="${1:?usage: run-report.sh <daily|weekly>}"

cd "$SCRIPT_DIR"
# `caffeinate -s` holds a sleep-prevent assertion for the duration of the
# wrapped command (released automatically when it exits). Needed because
# this Mac's battery-power idle-sleep is 1 minute (`pmset -g batt`) — far
# shorter than a full report run (~12 min) — confirmed the direct cause of
# a real Chromium-launch timeout failure on 2026-08-23. Does NOT wake the
# machine if it's already asleep before launchd fires — see README.
exec caffeinate -s "$NODE_BIN" dist/cli.js "$CMD"
