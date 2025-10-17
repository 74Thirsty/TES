"""Performance analytics for TES backtests."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable

import pandas as pd

from ..execution.orders import OrderSide, Trade


@dataclass(slots=True)
class PerformanceMetrics:
    total_return: float
    annualised_return: float
    annualised_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    trade_count: int
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float


def compute_performance(equity_curve: pd.Series, trades: Iterable[Trade]) -> PerformanceMetrics:
    if equity_curve.empty:
        raise ValueError("Equity curve is empty")

    equity = equity_curve.astype(float)
    returns = equity.pct_change().dropna()

    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1)
    if returns.empty:
        annualised_return = 0.0
        annualised_volatility = 0.0
        sharpe = 0.0
        sortino = 0.0
    else:
        periods_per_year = _infer_periods_per_year(equity.index)
        annualised_return = float((1 + returns.mean()) ** periods_per_year - 1)
        annualised_volatility = float(returns.std(ddof=0) * sqrt(periods_per_year))
        sharpe = (
            (annualised_return / annualised_volatility)
            if annualised_volatility > 0
            else 0.0
        )
        downside_returns = returns[returns < 0]
        downside_volatility = float(downside_returns.std(ddof=0) * sqrt(periods_per_year)) if not downside_returns.empty else 0.0
        sortino = (
            (annualised_return / downside_volatility)
            if downside_volatility > 0
            else 0.0
        )

    max_drawdown = float(_calculate_max_drawdown(equity))

    trade_list = list(trades)
    trade_count = len(trade_list)
    round_trip_pnls = _round_trip_pnls(trade_list)
    win_rate = (
        sum(1 for pnl in round_trip_pnls if pnl > 0) / len(round_trip_pnls)
        if round_trip_pnls
        else 0.0
    )
    gross_profit = sum(pnl for pnl in round_trip_pnls if pnl > 0)
    gross_loss = -sum(pnl for pnl in round_trip_pnls if pnl < 0)
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)
    average_win = gross_profit / sum(1 for pnl in round_trip_pnls if pnl > 0) if gross_profit > 0 else 0.0
    average_loss = (
        -(gross_loss / sum(1 for pnl in round_trip_pnls if pnl < 0))
        if gross_loss > 0
        else 0.0
    )

    if trade_count == 0:
        win_rate = 0.0

    return PerformanceMetrics(
        total_return=total_return,
        annualised_return=annualised_return,
        annualised_volatility=annualised_volatility,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        max_drawdown=max_drawdown,
        trade_count=trade_count,
        win_rate=win_rate,
        profit_factor=profit_factor,
        average_win=average_win,
        average_loss=average_loss,
    )


def _infer_periods_per_year(index: pd.Index) -> float:
    if isinstance(index, pd.DatetimeIndex) and len(index) > 1:
        deltas = index.to_series().diff().dropna()
        median_delta = deltas.median()
        if median_delta == pd.Timedelta(0):
            return 252
        return float(pd.Timedelta(days=365) / median_delta)
    return 252.0


def _calculate_max_drawdown(equity: pd.Series) -> float:
    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    return drawdown.min()


def _round_trip_pnls(trades: list[Trade]) -> list[float]:
    pnls: list[float] = []
    open_trade: Trade | None = None
    for trade in trades:
        if trade.side == OrderSide.BUY:
            open_trade = trade
        elif trade.side == OrderSide.SELL and open_trade is not None:
            quantity = min(open_trade.quantity, trade.quantity)
            buy_price = open_trade.execution_price()
            sell_price = trade.execution_price()
            pnl = (sell_price - buy_price) * quantity - (open_trade.fee + trade.fee)
            pnls.append(pnl)
            open_trade = None
    return pnls
