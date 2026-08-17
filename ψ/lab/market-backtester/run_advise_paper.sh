#!/bin/bash
# Paper-trade check, run twice daily by launchd (com.ayami.market-backtester-advise).
# No real money — --capital here is a fake starting balance tracked only in .state/.
cd "$(dirname "$0")"
LOG_HEADER="=== $(date '+%Y-%m-%d %H:%M:%S %Z') ==="
echo "$LOG_HEADER"

RESULT_FILE=$(mktemp)
.venv/bin/python3 -m backtester advise \
  --symbol BTC --market crypto --strategy book_rsi_ma \
  --sizing fixed --stop-pct 0.05 --target-pct 0.10 --capital 10 | tee "$RESULT_FILE"
echo ""

# Forward the result to Discord (same bot as "สรุปงาน") — best-effort: a network/Discord
# hiccup here must never fail the paper-trade check itself, so failures are swallowed.
NODE_BIN="/Users/phongcheatphus/.nvm/versions/node/v22.13.1/bin/node"
DISCORD_BOT_DIR="$(cd "$(dirname "$0")/../discord-bot" && pwd)"
if [ -s "$RESULT_FILE" ] && [ -x "$NODE_BIN" ] && [ -f "$DISCORD_BOT_DIR/notify.mjs" ]; then
  { echo "$LOG_HEADER"; cat "$RESULT_FILE"; } | (cd "$DISCORD_BOT_DIR" && "$NODE_BIN" notify.mjs) \
    || echo "notify.mjs failed (non-fatal, paper-trade result above is still valid)"
fi
rm -f "$RESULT_FILE"
