"""Command-line helpers for running TES strategies."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from strategies.ema_cross_02.ema_cross_class import EMACrossStrategy

from .engine import ExecutionEngine


def run_backtest_from_csv() -> None:
    parser = argparse.ArgumentParser(description="Run EMA crossover backtest")
    parser.add_argument("csv", type=Path, help="Path to OHLCV CSV file")
    parser.add_argument("--initial-balance", type=float, default=10_000.0)
    parser.add_argument("--fast-window", type=int, default=12)
    parser.add_argument("--slow-window", type=int, default=26)
    args = parser.parse_args()

    frame = pd.read_csv(args.csv)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])

    strategy = EMACrossStrategy(fast_window=args.fast_window, slow_window=args.slow_window)
    engine = ExecutionEngine(strategy=strategy, initial_balance=args.initial_balance)
    result = engine.run_backtest(frame)

    print("Backtest complete")
    print(f"Total return: {result.metrics.total_return:.2%}")
    print(f"Sharpe ratio: {result.metrics.sharpe_ratio:.2f}")
    print(f"Max drawdown: {result.metrics.max_drawdown:.2%}")
    print(f"Trades executed: {result.metrics.trade_count}")

    equity_csv = args.csv.with_name(args.csv.stem + "_equity.csv")
    result.equity_curve.to_csv(equity_csv)
    print(f"Equity curve exported to {equity_csv}")


if __name__ == "__main__":
    run_backtest_from_csv()
