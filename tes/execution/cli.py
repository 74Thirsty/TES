"""Command-line helpers for running TES strategies."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict
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
    parser.add_argument(
        "--metrics-json",
        type=Path,
        default=None,
        help="Optional path to export performance metrics as JSON",
    )
    parser.add_argument(
        "--equity-csv",
        type=Path,
        default=None,
        help="Optional path for the exported equity curve CSV",
    )
    parser.add_argument(
        "--trades-csv",
        type=Path,
        default=None,
        help="Optional path to export executed trades as CSV",
    )
    args = parser.parse_args()

    if not args.csv.exists():
        raise SystemExit(f"Input CSV not found: {args.csv}")

    frame = pd.read_csv(args.csv)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])

    required_columns = {"timestamp", "open", "high", "low", "close"}
    missing_columns = required_columns.difference(frame.columns)
    if missing_columns:
        raise SystemExit(
            f"Input data is missing required columns: {', '.join(sorted(missing_columns))}"
        )

    strategy = EMACrossStrategy(fast_window=args.fast_window, slow_window=args.slow_window)
    engine = ExecutionEngine(strategy=strategy, initial_balance=args.initial_balance)
    result = engine.run_backtest(frame)

    print("Backtest complete")
    print(f"Total return: {result.metrics.total_return:.2%}")
    print(f"Sharpe ratio: {result.metrics.sharpe_ratio:.2f}")
    print(f"Sortino ratio: {result.metrics.sortino_ratio:.2f}")
    print(f"Max drawdown: {result.metrics.max_drawdown:.2%}")
    print(f"Trades executed: {result.metrics.trade_count}")
    print(f"Win rate: {result.metrics.win_rate:.2%}")
    profit_factor = result.metrics.profit_factor
    profit_factor_display = "∞" if math.isinf(profit_factor) else f"{profit_factor:.2f}"
    print(f"Profit factor: {profit_factor_display}")

    equity_csv = args.equity_csv or args.csv.with_name(args.csv.stem + "_equity.csv")
    equity_csv.parent.mkdir(parents=True, exist_ok=True)
    result.equity_curve.to_csv(equity_csv)
    print(f"Equity curve exported to {equity_csv}")

    if args.trades_csv:
        args.trades_csv.parent.mkdir(parents=True, exist_ok=True)
        trades_frame = pd.DataFrame(
            [
                {
                    "timestamp": trade.timestamp,
                    "side": trade.side.value,
                    "price": trade.price,
                    "quantity": trade.quantity,
                    "fee": trade.fee,
                    "slippage": trade.slippage,
                    "execution_price": trade.execution_price(),
                }
                for trade in result.trades
            ]
        )
        trades_frame.to_csv(args.trades_csv, index=False)
        print(f"Trades exported to {args.trades_csv}")

    if args.metrics_json:
        args.metrics_json.parent.mkdir(parents=True, exist_ok=True)
        metrics_payload = asdict(result.metrics)
        metrics_payload["final_equity"] = result.portfolio.total_equity()
        metrics_payload["ending_cash"] = result.portfolio.cash
        metrics_payload["open_position_quantity"] = result.portfolio.position.quantity
        metrics_payload["open_position_average_price"] = result.portfolio.position.average_price
        serialised_payload = {
            key: ("inf" if isinstance(value, float) and math.isinf(value) else value)
            for key, value in metrics_payload.items()
        }
        args.metrics_json.write_text(json.dumps(serialised_payload, indent=2))
        print(f"Metrics exported to {args.metrics_json}")


if __name__ == "__main__":
    run_backtest_from_csv()
