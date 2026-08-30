---
pattern: "Learned whchien/ai-trader: a GPL-3.0 Backtrader-based backtesting framework — not worth migrating to for an existing production paper-trading system, but its FastMCP tool-server pattern (exposing run_backtest/fetch_data as LLM tool calls) is worth reimplementing for our own market-backtester."
date: 2026-08-16
source: "learn: whchien/ai-trader"
concepts: ["learn", "codebase", "backtrader", "mcp-server", "license-risk", "build-vs-integrate"]
---

# Learned ai-trader (whchien/ai-trader)

Explored via `/learn` (3 parallel agents) at Boss's request, alongside second opinions from
`/agy` (returned) and `/zcode` (did not return in time), to answer: should our own
`ψ/lab/market-backtester/` migrate to or integrate this framework?

**Key insights**:

1. **Config-driven, Backtrader-based, backtest-only.** 18 built-in strategies, US/TW stock +
   crypto + forex data fetchers, SQLite caching, and a FastMCP server exposing `run_backtest`,
   `fetch_market_data`, `list_strategies` as tool calls an LLM can invoke directly. GPL-3.0
   licensed, actively maintained (last commit 2026-03-28). No live/paper-trading execution or
   persistent state — purely a backtest/research tool.

2. **Migration verdict: no.** Our own system is already a *production* stateful service (Railway
   cron, Redis-backed trade store, correlation guard, Discord alerts, Streamlit dashboard) built
   on a pandas-native engine with an explicit lookahead-prevention convention
   (`signal.shift(1)`, proven via synthetic tests — see the 2026-08-15 mtf-strategy retro).
   Migrating to Backtrader's OOP event-loop model would mean rewriting the entire live-state layer
   from scratch (40-60h+ estimated) for a framework that doesn't even solve the problem we
   actually have (live paper-trading), plus it would drag GPL-3.0 copyleft obligations and heavier
   C-extension dependencies into a codebase whose build pipeline (Railway) is already a known
   fragile point.

3. **What's worth borrowing (not copying)**: the FastMCP tool-server pattern is the clear
   highest-value idea — wrapping our own backtester the same way would let Claude/Antigravity call
   `run_backtest`/live-advice checks as tool calls instead of shelling out to a CLI. Strategy
   *formulas* (RSRS regression-based trend strength, AdaptiveRSI's volatility-adaptive period,
   VCP breakout detection) are worth studying and re-deriving clean-room in pandas — never copying
   GPL-3.0 code directly into a codebase we might want to keep license-flexible.

**Generalizable takeaway**: when evaluating whether to adopt an external framework into an
existing production system, the real question isn't "is this framework good" — it's "does
migrating solve a problem we actually have, or are we trading a stable system's known shape for
an unstable one's unknown shape, for a benefit (more strategies, nicer config) obtainable by
grabbing just the useful surface (patterns, formulas) instead of the whole dependency tree
(license, build risk, rewrite cost)."

Full docs: `ψ/learn/whchien/ai-trader/ai-trader.md` (hub) →
`ψ/learn/whchien/ai-trader/2026-08-16/2328_{ARCHITECTURE,CODE-SNIPPETS,QUICK-REFERENCE}.md`
