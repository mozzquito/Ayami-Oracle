"""CLI entry point: `python -m backtester run --symbol PTT --market set --strategy sma_cross ...`"""

from __future__ import annotations

import argparse
import sys

from .advisor import advise, estimate_min_capital
from .config import (
    DEFAULT_CAPITAL,
    DEFAULT_COMMISSION_PCT,
    DEFAULT_RISK_PCT,
    DEFAULT_SIZE_PCT,
    DEFAULT_SIZING_MODE,
    DEFAULT_SLIPPAGE_PCT,
    STRATEGY_STOP_TARGET_PCT,
    VALID_MARKETS,
)
from .data import fetch_ohlcv
from .engine import run_backtest
from .metrics import compute_metrics
from .report import format_summary, save_equity_chart, save_markdown_report
from .strategy import STRATEGIES


def _parse_params(raw: str | None) -> dict:
    """Parse "fast=20,slow=50" into {"fast": 20, "slow": 50} with int/float coercion."""
    if not raw:
        return {}
    params = {}
    for pair in raw.split(","):
        key, _, value = pair.partition("=")
        key = key.strip()
        value = value.strip()
        for cast in (int, float):
            try:
                value = cast(value)
                break
            except ValueError:
                continue
        params[key] = value
    return params


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="backtester", description="Market analysis & strategy backtesting CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run a backtest for one symbol/strategy")
    run_p.add_argument("--symbol", required=True, help="Ticker symbol, e.g. PTT, AAPL, BTC, EURUSD")
    run_p.add_argument("--market", required=True, choices=VALID_MARKETS, help="Asset class, controls ticker suffix + annualization")
    run_p.add_argument("--strategy", required=True, choices=sorted(STRATEGIES.keys()))
    run_p.add_argument("--params", default=None, help='Strategy params as "key=value,key=value", e.g. "fast=20,slow=50"')
    run_p.add_argument("--start", required=True, help="YYYY-MM-DD")
    run_p.add_argument("--end", default=None, help="YYYY-MM-DD (default: today)")
    run_p.add_argument("--capital", type=float, default=DEFAULT_CAPITAL)
    run_p.add_argument("--commission", type=float, default=DEFAULT_COMMISSION_PCT, help="Fraction per trade, e.g. 0.001 = 0.1%%")
    run_p.add_argument("--slippage", type=float, default=DEFAULT_SLIPPAGE_PCT, help="Fraction per fill, e.g. 0.0005 = 0.05%%")
    run_p.add_argument("--size-pct", type=float, default=DEFAULT_SIZE_PCT, dest="size_pct", help="fixed sizing: fraction of available cash deployed per entry (0-1)")
    run_p.add_argument("--sizing", default=DEFAULT_SIZING_MODE, choices=["fixed", "fractional", "kelly"], help="Position sizing method (Ch.12): fixed=%%-of-cash, fractional=risk-%%-per-stop, kelly=adaptive Kelly criterion")
    run_p.add_argument("--risk-pct", type=float, default=DEFAULT_RISK_PCT, dest="risk_pct", help="fractional sizing: fraction of account risked per trade (needs --stop-pct)")
    run_p.add_argument("--stop-pct", type=float, default=None, dest="stop_pct", help="Stop-loss distance below entry, e.g. 0.05 = 5%% (also required by --sizing fractional)")
    run_p.add_argument("--target-pct", type=float, default=None, dest="target_pct", help="Take-profit distance above entry, e.g. 0.10 = 10%%")
    run_p.add_argument("--save-report", default=None, dest="save_report", help="Write a markdown report to this path")
    run_p.add_argument("--save-chart", default=None, dest="save_chart", help="Write an equity-curve PNG to this path")

    advise_p = sub.add_parser("advise", help="Twice-a-day check: get an enter/hold/exit recommendation instead of watching charts")
    advise_p.add_argument("--symbol", required=True)
    advise_p.add_argument("--market", required=True, choices=VALID_MARKETS)
    advise_p.add_argument("--strategy", required=True, choices=sorted(STRATEGIES.keys()))
    advise_p.add_argument("--params", default=None)
    advise_p.add_argument("--capital", type=float, default=DEFAULT_CAPITAL, help="Only used the first time (new state file)")
    advise_p.add_argument("--commission", type=float, default=DEFAULT_COMMISSION_PCT)
    advise_p.add_argument("--slippage", type=float, default=DEFAULT_SLIPPAGE_PCT)
    advise_p.add_argument("--size-pct", type=float, default=DEFAULT_SIZE_PCT, dest="size_pct")
    advise_p.add_argument("--sizing", default=DEFAULT_SIZING_MODE, choices=["fixed", "fractional", "kelly"])
    advise_p.add_argument("--risk-pct", type=float, default=DEFAULT_RISK_PCT, dest="risk_pct")
    advise_p.add_argument("--stop-pct", type=float, default=None, dest="stop_pct")
    advise_p.add_argument("--target-pct", type=float, default=None, dest="target_pct")
    advise_p.add_argument("--reset", action="store_true", help="Discard saved position state and start fresh")

    min_cap_p = sub.add_parser("min-capital", help="Estimate the minimum account size for --sizing fractional to stay meaningful")
    min_cap_p.add_argument("--market", required=True, choices=VALID_MARKETS)
    min_cap_p.add_argument("--stop-pct", required=True, type=float, dest="stop_pct")
    min_cap_p.add_argument("--risk-pct", type=float, default=DEFAULT_RISK_PCT, dest="risk_pct")
    price_group = min_cap_p.add_mutually_exclusive_group(required=True)
    price_group.add_argument("--symbol", default=None, help="Fetch the latest close for this symbol as the reference price")
    price_group.add_argument("--price", type=float, default=None, help="Use this price directly instead of fetching")

    sub.add_parser("list-strategies", help="List available strategies")

    return parser


def _resolve_stop_target(strategy: str, market: str, stop_pct: float | None, target_pct: float | None) -> tuple[float | None, float | None]:
    """Fill in a strategy's backtest-tuned stop/target (config.STRATEGY_STOP_TARGET_PCT)
    when the user didn't pass --stop-pct/--target-pct explicitly. An explicit flag always
    wins; this only fills the gap, never overrides.
    """
    tuned = STRATEGY_STOP_TARGET_PCT.get(strategy, {}).get(market)
    if not tuned:
        return stop_pct, target_pct
    return (
        stop_pct if stop_pct is not None else tuned["stop_pct"],
        target_pct if target_pct is not None else tuned["target_pct"],
    )


def cmd_run(args: argparse.Namespace) -> int:
    try:
        df = fetch_ohlcv(args.symbol, args.market, args.start, args.end)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    strategy_fn = STRATEGIES[args.strategy]
    params = _parse_params(args.params)

    try:
        signal = strategy_fn(df, **params)
    except TypeError as e:
        print(f"Error: bad --params for strategy '{args.strategy}': {e}", file=sys.stderr)
        return 1

    stop_pct, target_pct = _resolve_stop_target(args.strategy, args.market, args.stop_pct, args.target_pct)

    try:
        result = run_backtest(
            df,
            signal,
            initial_capital=args.capital,
            commission_pct=args.commission,
            slippage_pct=args.slippage,
            size_pct=args.size_pct,
            sizing_mode=args.sizing,
            risk_pct=args.risk_pct,
            stop_pct=stop_pct,
            target_pct=target_pct,
            market=args.market,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    m = compute_metrics(result, df["Close"])

    print(format_summary(args.symbol, args.strategy, result, m))

    if args.save_report:
        save_markdown_report(args.save_report, args.symbol, args.strategy, result, m)
        print(f"\nReport saved: {args.save_report}")

    if args.save_chart:
        save_equity_chart(args.save_chart, args.symbol, result)
        print(f"Chart saved: {args.save_chart}")

    return 0


def cmd_advise(args: argparse.Namespace) -> int:
    params = _parse_params(args.params)
    stop_pct, target_pct = _resolve_stop_target(args.strategy, args.market, args.stop_pct, args.target_pct)
    try:
        report, _event = advise(
            symbol=args.symbol,
            market=args.market,
            strategy_name=args.strategy,
            params=params,
            capital=args.capital,
            commission_pct=args.commission,
            slippage_pct=args.slippage,
            sizing_mode=args.sizing,
            size_pct=args.size_pct,
            risk_pct=args.risk_pct,
            stop_pct=stop_pct,
            target_pct=target_pct,
            reset=args.reset,
        )
    except (ValueError, TypeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(report)
    return 0


def cmd_min_capital(args: argparse.Namespace) -> int:
    if args.price is not None:
        price = args.price
    else:
        try:
            df = fetch_ohlcv(args.symbol, args.market, "2020-01-01", None)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        price = float(df["Close"].iloc[-1])

    min_notional, min_capital = estimate_min_capital(args.market, price, args.stop_pct, args.risk_pct)
    print(f"Market: {args.market}  |  Reference price: {price:,.5f}")
    print(f"Typical minimum trade size (~): {min_notional:,.2f}")
    print(f"Recommended minimum capital for --sizing fractional (--risk-pct {args.risk_pct}, --stop-pct {args.stop_pct}): {min_capital:,.2f}")
    print("(rule-of-thumb based on typical retail lot sizes — confirm your actual broker's minimum)")
    return 0


def cmd_list_strategies(_args: argparse.Namespace) -> int:
    for name in sorted(STRATEGIES.keys()):
        print(name)
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "run": cmd_run,
        "advise": cmd_advise,
        "min-capital": cmd_min_capital,
        "list-strategies": cmd_list_strategies,
    }
    exit_code = handlers[args.command](args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
