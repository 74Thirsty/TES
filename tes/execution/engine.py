"""Execution and backtesting engine for TES strategies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

import numpy as np
import pandas as pd

from strategies.ema_cross_02.ema_cross_class import EMACrossStrategy

from .orders import OrderSide, Trade
from .portfolio import Portfolio
from ..utils.performance import PerformanceMetrics, compute_performance


@dataclass(slots=True)
class BacktestResult:
    portfolio: Portfolio
    trades: List[Trade]
    equity_curve: pd.DataFrame
    metrics: PerformanceMetrics


class ExecutionEngine:
    """High-level coordinator that turns strategy signals into trades."""

    def __init__(
        self,
        strategy: EMACrossStrategy,
        initial_balance: float = 10_000.0,
        max_position_pct: float = 0.95,
        fee_pct: float = 0.0007,
        slippage_pct: float = 0.0005,
        min_trade_value: float = 25.0,
    ) -> None:
        if not 0 < max_position_pct <= 1:
            raise ValueError("max_position_pct must be between 0 and 1")
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.max_position_pct = max_position_pct
        self.fee_pct = fee_pct
        self.slippage_pct = slippage_pct
        self.min_trade_value = min_trade_value

    def run_backtest(self, candles: pd.DataFrame) -> BacktestResult:
        if candles.empty:
            raise ValueError("No candles supplied to execution engine")

        candles = candles.sort_values("timestamp").reset_index(drop=True)
        signals = self.strategy.generate_signals(candles)
        signal_df = self.strategy.to_dataframe(signals)
        signal_df.set_index("timestamp", inplace=True)

        portfolio = Portfolio(cash=self.initial_balance)
        trades: List[Trade] = []

        for idx, candle in candles.iterrows():
            timestamp = _ensure_timestamp(candle["timestamp"])
            price = float(candle["close"])
            signal = signal_df.loc[timestamp] if timestamp in signal_df.index else None

            if signal is not None:
                if isinstance(signal, pd.Series):
                    signal_rows = [signal]
                else:
                    signal_rows = [signal.iloc[i] for i in range(len(signal))]
                for row in signal_rows:
                    target_direction = int(row["direction"])
                    trades.extend(
                        self._rebalance(
                            timestamp=timestamp,
                            price=price,
                            target_direction=target_direction,
                            portfolio=portfolio,
                        )
                    )

            portfolio.mark_to_market(timestamp, price)

        equity_curve = pd.DataFrame(
            [
                {
                    "timestamp": snap.timestamp,
                    "equity": snap.equity,
                    "cash": snap.cash,
                    "position": snap.position_quantity,
                    "unrealised_pnl": snap.unrealised_pnl,
                }
                for snap in portfolio.snapshots
            ]
        ).set_index("timestamp")

        metrics = compute_performance(equity_curve["equity"], trades)

        return BacktestResult(
            portfolio=portfolio,
            trades=trades,
            equity_curve=equity_curve,
            metrics=metrics,
        )

    def _rebalance(
        self,
        timestamp: datetime,
        price: float,
        target_direction: int,
        portfolio: Portfolio,
    ) -> List[Trade]:
        trades: List[Trade] = []
        position = portfolio.position

        if target_direction not in (0, 1):
            raise ValueError(f"Unsupported direction: {target_direction}")

        if target_direction == 1 and position.quantity <= 0:
            desired_value = portfolio.cash * self.max_position_pct
            if desired_value < self.min_trade_value:
                return trades
            quantity = desired_value / price
            trade = Trade(
                timestamp=timestamp,
                side=OrderSide.BUY,
                price=price,
                quantity=quantity,
                fee=desired_value * self.fee_pct,
                slippage=self.slippage_pct,
            )
            portfolio.process_trade(trade)
            trades.append(trade)
        elif target_direction == 0 and position.quantity > 0:
            quantity = position.quantity
            trade = Trade(
                timestamp=timestamp,
                side=OrderSide.SELL,
                price=price,
                quantity=quantity,
                fee=price * quantity * self.fee_pct,
                slippage=self.slippage_pct,
            )
            portfolio.process_trade(trade)
            trades.append(trade)

        return trades


def _ensure_timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, (np.datetime64, pd.Timestamp)):
        return pd.Timestamp(value).to_pydatetime()
    raise TypeError(f"Unsupported timestamp type: {type(value)!r}")
