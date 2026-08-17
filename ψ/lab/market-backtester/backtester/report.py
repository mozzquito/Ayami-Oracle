"""Formats backtest results as a printable summary, and optionally writes a markdown
report and an equity-curve PNG (matplotlib import is deferred so it stays an optional dep)."""

from __future__ import annotations

from .engine import BacktestResult
from .metrics import Metrics


def format_summary(symbol: str, strategy_name: str, result: BacktestResult, m: Metrics) -> str:
    lines = [
        f"Backtest: {symbol}  |  strategy={strategy_name}  |  market={result.market}",
        "-" * 60,
        f"{'Initial capital':<24} {result.initial_capital:,.2f}",
        f"{'Final equity':<24} {result.final_equity:,.2f}",
        f"{'Total return':<24} {m.total_return_pct:,.2f}%",
        f"{'CAGR':<24} {m.cagr_pct:,.2f}%",
        f"{'Sharpe (annualized)':<24} {m.sharpe:,.2f}",
        f"{'Max drawdown':<24} {m.max_drawdown_pct:,.2f}%",
        f"{'Trades':<24} {m.num_trades}",
        f"{'Win rate':<24} {m.win_rate_pct:,.2f}%",
        f"{'Buy & hold return':<24} {m.buy_hold_return_pct:,.2f}%",
    ]
    return "\n".join(lines)


def save_markdown_report(path: str, symbol: str, strategy_name: str, result: BacktestResult, m: Metrics) -> None:
    body = format_summary(symbol, strategy_name, result, m)
    with open(path, "w") as f:
        f.write(f"# Backtest Report — {symbol}\n\n```\n{body}\n```\n")
        if not result.trades.empty:
            f.write("\n## Trade Log\n\n")
            f.write(result.trades.to_markdown(index=False))
            f.write("\n")


def save_equity_chart(path: str, symbol: str, result: BacktestResult) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5))
    result.equity_curve.plot(ax=ax, label="Strategy equity")
    ax.axhline(result.initial_capital, color="gray", linestyle="--", linewidth=1, label="Initial capital")
    ax.set_title(f"Equity curve — {symbol}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Equity")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
